"""Yalnız dosyadan Hailo/TAPPAS ve aynı tensörden HailoRT karşılaştırması."""
from __future__ import annotations
from dataclasses import asdict
import ctypes
import json
import os
from pathlib import Path
import time
import cv2
import numpy as np
from .types import Detection


def letterbox_rgb(bgr, size=(640,640), padding=114):
    """Teşhis referansı; gerçek çıkarım tensörü hailonet sink pad'inden alınır."""
    h,w=bgr.shape[:2]; tw,th=size
    scale=min(tw/w,th/h); nw,nh=int(w*scale),int(h*scale)
    left,top=(tw-nw)//2,(th-nh)//2
    rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)
    dst=np.full((th,tw,3),padding,np.uint8)
    dst[top:top+nh,left:left+nw]=cv2.resize(rgb,(nw,nh),interpolation=cv2.INTER_AREA)
    return dst, {'width':w,'height':h,'tensor_width':tw,'tensor_height':th,
                 'resized_width':nw,'resized_height':nh,'left':left,'top':top}


def unletterbox(box, transform):
    t=transform
    return ((box[0]*t['tensor_width']-t['left'])/t['resized_width'],
            (box[1]*t['tensor_height']-t['top'])/t['resized_height'],
            (box[2]*t['tensor_width']-t['left'])/t['resized_width'],
            (box[3]*t['tensor_height']-t['top'])/t['resized_height'])


def compare_detections(left,right,tolerance=2e-6):
    remaining=list(right); errors=[]; maximum=0.
    for a in left:
        matches=[(i,b) for i,b in enumerate(remaining) if a['class_id']==b['class_id']]
        if not matches:
            errors.append('missing_class');continue
        i,b=min(matches,key=lambda pair:np.max(np.abs(np.array(a['bbox'])-pair[1]['bbox'])))
        remaining.pop(i)
        diff=float(np.max(np.abs(np.array([a['confidence'],*a['bbox']])-np.array([b['confidence'],*b['bbox']]))))
        maximum=max(maximum,diff)
        if diff>tolerance: errors.append('values_differ')
    if remaining: errors.append('extra_detection')
    return {'equal':not errors,'max_abs_error':maximum,'errors':errors,'tolerance':tolerance}


def replay_hailo(frames,cfg,out,hailo_env=None):
    from .replay import ReplayError,sha256
    if hailo_env:
        if not Path(hailo_env).is_file(): raise ReplayError('Hailo .env bulunamadı')
        os.environ['HAILO_ENV_FILE']=str(Path(hailo_env).resolve())
    try:
        import gi
        gi.require_version('Gst','1.0')
        from gi.repository import Gst
        import hailo
        import hailo_platform as hp
        from hailo_apps.hailo_app_python.core.gstreamer import gstreamer_helper_pipelines as helpers
        from hailo_apps.hailo_app_python.core.common.buffer_utils import get_caps_from_pad,get_numpy_from_buffer
        from hailo_apps.hailo_app_python.core.common.core import get_resource_path
        from hailo_apps.hailo_app_python.core.common.defines import DETECTION_PIPELINE,RESOURCES_SO_DIR_NAME,DETECTION_POSTPROCESS_SO_FILENAME,DETECTION_POSTPROCESS_FUNCTION
    except ImportError as e:
        raise ReplayError(f'Hailo bulunamadı; CPU yedeği yok. Mevcut setup_env.sh ortamını etkinleştirin: {e}') from e
    if getattr(hp,'__version__','') != '4.20.0':
        raise ReplayError('Ham NMS okuyucusu yalnız doğrulanan HailoRT 4.20.0 için etkin')
    hef=hp.HEF(cfg.hef_file)
    inputs=hef.get_input_vstream_infos();outputs=hef.get_output_vstream_infos()
    if (len(inputs)!=1 or tuple(inputs[0].shape)!=(640,640,3) or len(outputs)!=1
        or outputs[0].nms_shape.number_of_classes!=2 or outputs[0].nms_shape.max_bboxes_per_class!=100):
        raise ReplayError('Bu okuyucu 640x640 RGB, 2 sınıf, sınıf başına 100 NMS kutusu bekliyor')
    Gst.init(None)
    post=get_resource_path(DETECTION_PIPELINE,RESOURCES_SO_DIR_NAME,DETECTION_POSTPROCESS_SO_FILENAME)
    if not post or not Path(post).is_file():raise ReplayError(f'Hailo postprocess bulunamadı: {post}')
    quote=lambda v:json.dumps(str(v))
    inner=helpers.INFERENCE_PIPELINE(hef_path=quote(cfg.hef_file),post_process_so=quote(post),
        post_function_name=DETECTION_POSTPROCESS_FUNCTION,batch_size=1,config_json=quote(cfg.labels_file),
        additional_params='nms-score-threshold=0.25 nms-iou-threshold=0.7 output-format-type=HAILO_FORMAT_TYPE_FLOAT32')
    wrapped=helpers.INFERENCE_PIPELINE_WRAPPER(inner,bypass_max_size_buffers=4)
    pipeline_text=(f'appsrc name=replay_source is-live=true format=time block=true ! '
        f'video/x-raw,format=RGB,width={cfg.camera.width},height={cfg.camera.height},framerate=30/1,pixel-aspect-ratio=1/1 ! '
        f'{wrapped} ! identity name=replay_result ! fakesink sync=false qos=false async=false')
    (out/'pipeline.txt').write_text(pipeline_text)
    trace_dir=out/'tensors';trace_dir.mkdir()
    results={}; pending={}; errors=[]; active=[]
    def identity(buffer,kind):
        if buffer.pts in pending:
            return pending[buffer.pts]
        # Crop dalı CLOCK_TIME_NONE üretir. Aynı anda kesinlikle tek giriş vardır;
        # birleşmiş son dal özgün PTS'yi ayrıca doğrular.
        if kind != 'application' and buffer.pts == Gst.CLOCK_TIME_NONE and len(active)==1:
            return pending[active[0]]
        raise ReplayError(f'Beklenmeyen PTS: {buffer.pts}/{kind}')
    def decode(buffer):
        ds=[]
        for item in hailo.get_roi_from_buffer(buffer).get_objects_typed(hailo.HAILO_DETECTION):
            c=item.get_class_id();label=item.get_label();b=item.get_bbox()
            if {1:'kirmizi_hedef',2:'mavi_hedef'}.get(c)!=label:raise ReplayError('TAPPAS sınıf eşlemesi uyuşmuyor')
            ds.append(asdict(Detection(label,float(item.get_confidence()),(b.xmin(),b.ymin(),b.xmax(),b.ymax()),c)))
        return ds
    def probe(kind):
        def callback(pad,info):
            try:
                buf=info.get_buffer();r=identity(buf,kind);name=r['name']
                r.setdefault('stage_pts',{})[kind]=int(buf.pts)
                if kind in r:raise ReplayError(f'Yinelenen çıktı: {name}/{kind}')
                if kind=='input':
                    fmt,w,h=get_caps_from_pad(pad)
                    if (fmt,w,h)!=('RGB',640,640):raise ReplayError(f'Hailonet giriş caps uyuşmazlığı: {fmt}/{w}/{h}')
                    tensor=get_numpy_from_buffer(buf,fmt,w,h)
                    np.save(trace_dir/f'{name}-input.npy',tensor,allow_pickle=False)
                    r[kind]={'shape':list(tensor.shape),'dtype':str(tensor.dtype),'sha256':sha256(trace_dir/f'{name}-input.npy')}
                elif kind=='nms':
                    tensors=hailo.get_roi_from_buffer(buf).get_tensors()
                    captured=[]
                    for j,t in enumerate(tensors):
                        # TAPPAS 3.31 Python buffer, NMS union'unu HWC olarak sunar:
                        # shape=(2,100,0). Adres geçerli; boyut sıfır. Yalnız geçerli
                        # FLOAT32 count + 5 değer kayıtlarını, sınıf başına <=100 sınırıyla kopyala.
                        view=np.asarray(t)
                        if view.shape!=(2,100,0) or view.dtype!=np.uint8:
                            raise ReplayError('TAPPAS NMS Python buffer düzeni doğrulanan sürümden farklı')
                        pointer=view.__array_interface__['data'][0]
                        if not pointer:raise ReplayError('NMS veri adresi yok')
                        chunks=[];classes=[];offset=0
                        for cls in range(2):
                            count_bytes=ctypes.string_at(pointer+offset,4)
                            count=float(np.frombuffer(count_bytes,dtype='<f4')[0])
                            if not np.isfinite(count) or count!=int(count) or not 0<=count<=100:
                                raise ReplayError('NMS count/format beklenen FLOAT32 değil')
                            offset+=4;chunks.append(count_bytes)
                            data=ctypes.string_at(pointer+offset,int(count)*20)
                            offset+=len(data);chunks.append(data)
                            boxes=np.frombuffer(data,dtype='<f4').reshape(-1,5).copy()
                            if not np.isfinite(boxes).all():raise ReplayError('Sonlu olmayan NMS çıktısı')
                            classes.append(boxes.tolist())
                        (trace_dir/f'{name}-nms-{j}.bin').write_bytes(b''.join(chunks))
                        captured.append({'name':t.name(),'python_buffer_shape':list(view.shape),
                            'format':'FLOAT32 packed NMS valid prefix, little endian',
                            'valid_bytes':offset,'classes_yxyx_score':classes})
                    if len(captured)!=1:raise ReplayError('Tek NMS tensörü bekleniyor')
                    r[kind]=captured
                elif kind=='postprocess_before_aggregator':r[kind]=decode(buf)
                else:
                    r[kind]=decode(buf)
                    if name in results:raise ReplayError('Yinelenen son kare')
                    results[name]=r
            except Exception as e: errors.append(str(e))
            return Gst.PadProbeReturn.OK
        return callback
    pipe=Gst.parse_launch(pipeline_text)
    # Salt okunur teşhis için HEF çıkış tensörünün ömrünü src probuna uzatır.
    pipe.get_by_name('inference_hailofilter').set_property('remove-tensors',False)
    for element,pad,kind in [('inference_hailonet','sink','input'),('inference_hailofilter','src','nms'),
                             ('inference_hailofilter','src','postprocess_before_aggregator'),('replay_result','src','application')]:
        pipe.get_by_name(element).get_static_pad(pad).add_probe(Gst.PadProbeType.BUFFER,probe(kind))
    bus=pipe.get_bus();src=pipe.get_by_name('replay_source')
    try:
        pipe.set_state(Gst.State.PLAYING)
        for index,f in enumerate(frames):
            pts=(index+1)*Gst.SECOND
            active[:]=[pts]
            pending[pts]={'name':f['name'],'frame_id':f['meta']['frame_id'],'pts':pts}
            im=cv2.imread(str(f['path']));rgb=cv2.cvtColor(im,cv2.COLOR_BGR2RGB)
            buf=Gst.Buffer.new_wrapped(rgb.tobytes());buf.pts=pts;buf.duration=Gst.SECOND//30
            if src.emit('push-buffer',buf)!=Gst.FlowReturn.OK:raise ReplayError('appsrc push başarısız')
            deadline=time.monotonic()+20
            while f['name'] not in results:
                message=bus.timed_pop_filtered(100*Gst.MSECOND,Gst.MessageType.ERROR)
                if message:
                    err,debug=message.parse_error();raise ReplayError(f'GStreamer: {err}: {debug}')
                if errors:raise ReplayError(errors[0])
                if time.monotonic()>deadline:raise ReplayError(f'Kare zaman aşımı: {f["name"]}')
            if errors:raise ReplayError(errors[0])
            if not {'input','nms','postprocess_before_aggregator','application'} <= set(results[f['name']]):raise ReplayError('Eksik aşama')
        src.emit('end-of-stream')
    finally:
        pipe.set_state(Gst.State.NULL)
        pipe.get_state(5*Gst.SECOND)
    # TAPPAS cihazı kapandıktan sonra aynı baytlar doğrudan HailoRT'ye girer.
    comparisons=[];tensor_equal=[]
    with hp.VDevice() as device:
        params=hp.ConfigureParams.create_from_hef(hef,interface=hp.HailoStreamInterface.PCIe)
        groups=device.configure(hef,params)
        if len(groups)!=1:raise ReplayError('Tek ağ grubu bekleniyor')
        group=groups[0]
        ip=hp.InputVStreamParams.make_from_network_group(group,quantized=True,format_type=hp.FormatType.UINT8)
        op=hp.OutputVStreamParams.make_from_network_group(group,quantized=False,format_type=hp.FormatType.FLOAT32)
        with group.activate(group.create_params()):
            with hp.InferVStreams(group,ip,op,tf_nms_format=False) as infer:
                infer.set_nms_score_threshold(.25);infer.set_nms_iou_threshold(.7)
                for f in frames:
                    name=f['name'];r=results[name]
                    tensor=np.load(trace_dir/f'{name}-input.npy',allow_pickle=False)
                    reference,transform=letterbox_rgb(cv2.imread(str(f['path'])))
                    r['transform']=transform;r['reference_tensor_equal']=bool(np.array_equal(tensor,reference))
                    r['reference_max_abs_difference']=int(np.abs(tensor.astype(int)-reference.astype(int)).max())
                    tensor_equal.append(r['reference_tensor_equal'])
                    if not r['reference_tensor_equal']:
                        raise ReplayError('Gerçek tensör doğrulanan letterbox dönüşümüyle eşleşmiyor; koordinat karşılaştırması durdu')
                    raw=infer.infer({inputs[0].name:tensor[None]})[outputs[0].name]
                    classes=raw[0]
                    if len(classes)!=2:raise ReplayError(f'İki NMS sınıfı bekleniyor: {len(classes)}')
                    ds=[];raw_json=[]
                    for cls,arr in enumerate(classes):
                        arr=np.asarray(arr).reshape(-1,5);raw_json.append(arr.tolist())
                        for y1,x1,y2,x2,score in arr:
                            ds.append(asdict(Detection(['kirmizi_hedef','mavi_hedef'][cls],float(score),
                                unletterbox((float(x1),float(y1),float(x2),float(y2)),transform),cls+1)))
                    r['direct_nms']=raw_json;r['direct_application']=ds
                    packed=r['nms'][0]['classes_yxyx_score']
                    r['packed_nms_equals_direct']=len(packed)==len(raw_json) and all(
                        np.array_equal(np.asarray(a),np.asarray(b)) for a,b in zip(packed,raw_json))
                    r['comparison']=compare_detections(r['application'],ds)
                    comparisons.append(r['comparison'])
                    (trace_dir/f'{name}-trace.json').write_text(json.dumps(r,indent=2,allow_nan=False))
    info={'hailort':getattr(hp,'__version__','UNKNOWN'),'gstreamer':Gst.version_string(),
          'helpers_path':helpers.__file__,'helpers_sha256':sha256(helpers.__file__),
          'postprocess_path':str(post),'diagnostic_remove_tensors':False,'postprocess_sha256':sha256(post),
          'input_info':{'name':inputs[0].name,'shape':list(inputs[0].shape),'format':str(inputs[0].format)},
          'output_info':{'name':outputs[0].name,'classes':2,'max_boxes_per_class':100,'format':str(outputs[0].format)},
          'comparison':{'frames':len(comparisons),'equal_frames':sum(c['equal'] for c in comparisons),
                        'max_abs_error':max(c['max_abs_error'] for c in comparisons),
                        'reference_tensor_equal_frames':sum(tensor_equal),
                        'packed_nms_equal_frames':sum(r['packed_nms_equals_direct'] for r in results.values())},
          'limits':'Yalnız HEF dışa açık NMS; ara ağ logitleri erişilebilir değildir.'}
    return results,info
