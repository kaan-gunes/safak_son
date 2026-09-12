"""Sınırlı maliyetli OpenCV renk + dörtgen araması."""
from dataclasses import dataclass

import cv2
import numpy as np

from ..geometry import bbox_iou
from .config import COLORS, ColorSearch


@dataclass(frozen=True)
class ColorRegion:
    color: str
    bbox: tuple
    fill: float  # Geometrik renk doluluğu.


class ColorDetector:
    def __init__(self, camera, options=None):
        self.camera = camera
        self.options = options or ColorSearch()
        self.options.validate()
        self.kernel = np.ones((3, 3), np.uint8)

    def mask(self, hsv, color):
        s, v = self.options.min_saturation, self.options.min_value
        if color == 'mavi':
            return cv2.inRange(hsv, (90, s, v), (135, 255, 255))
        return cv2.bitwise_or(cv2.inRange(hsv, (0, s, v), (12, 255, 255)),
                             cv2.inRange(hsv, (168, s, v), (179, 255, 255)))

    def quads(self, mask, minimum_area):
        cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, self.kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, self.kernel)
        contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        result = []
        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            area = cv2.contourArea(contour)
            if area < minimum_area:
                break
            quad = cv2.approxPolyDP(contour, .025 * cv2.arcLength(contour, True), True)
            if len(quad) != 4 or not cv2.isContourConvex(quad):
                continue
            rw, rh = cv2.minAreaRect(quad)[1]
            if min(rw, rh) <= 0 or max(rw, rh)/min(rw, rh) > self.options.max_aspect:
                continue
            if area/max(rw*rh, 1) < self.options.min_fill:
                continue
            x, y, w, h = cv2.boundingRect(quad)
            interior = np.zeros((h, w), np.uint8)
            cv2.fillConvexPoly(interior, quad.reshape(4,2)-[x,y], 255)
            pixels = mask[y:y+h, x:x+w][interior > 0]
            fill = float(np.count_nonzero(pixels)/max(len(pixels), 1))
            if fill >= self.options.min_fill:
                result.append(((x,y,x+w,y+h), fill))
            if len(result) >= self.options.max_candidates:
                break
        return result

    def detect(self, image, border_px=None):
        # Hızlı görevde metrik ölçüm yok; kenara değen hedef bölgesi elenmez.
        border = self.camera.min_border_px if border_px is None else max(0, int(border_px))
        h, w = image.shape[:2]
        width = min(w, self.options.width)
        height = max(1, round(h*width/w))
        small = cv2.resize(image, (width,height), interpolation=cv2.INTER_AREA)
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        scale_x, scale_y = w/width, h/height
        found = []
        for color in COLORS:
            coarse = self.quads(self.mask(hsv,color), self.camera.min_quad_area_px/(scale_x*scale_y))
            for box, _ in coarse:
                # Yalnız birkaç aday bölgesi tam çözünürlükte yeniden doğrulanır.
                x1,y1,x2,y2 = box
                left,top = max(0,int(x1*scale_x)-6),max(0,int(y1*scale_y)-6)
                right,bottom = min(w,int(x2*scale_x)+6),min(h,int(y2*scale_y)+6)
                roi = cv2.cvtColor(image[top:bottom,left:right],cv2.COLOR_BGR2HSV)
                for refined,fill in self.quads(self.mask(roi,color),self.camera.min_quad_area_px):
                    a,b,c,d = refined
                    a,b,c,d = a+left,b+top,c+left,d+top
                    if border and (min(a,b) < border or c>w-border or d>h-border):
                        continue
                    if max((c-a)/w,(d-b)/h)>self.camera.max_frame_occupancy:
                        continue
                    normalized = (a/w,b/h,c/w,d/h)
                    if any(r.color==color and bbox_iou(r.bbox,normalized)>.5 for r in found):
                        continue
                    found.append(ColorRegion(color,normalized,fill))
        return tuple(found)
