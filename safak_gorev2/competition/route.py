import math
import hashlib
import json
import struct
from ..geometry import local_distance


def mission_digest(mission):
    # seq0 HOME, FC açılışı/GPS ile değişebilir; uçurulan seq1+ sözleşmeye dahildir.
    # WPL ondalıklarını MAVLink float32 irtifasıyla aynı biçimde karşılaştır.
    items = [dict(seq=x.seq, command=x.command, frame=x.frame, x=x.x, y=x.y,
                  z=struct.unpack('<f',struct.pack('<f',float(x.z)))[0]) for x in mission.items[1:]]
    return hashlib.sha256(json.dumps(items,sort_keys=True).encode()).hexdigest()


def cross(a, b):
    return a[0]*b[1] - a[1]*b[0]


def crossed(gate, before, after):
    """Sonlu kapı ve doğru yön. Uzak telemetri örnekleri çağıran tarafından elenir."""
    if not gate or before is None:
        return False
    a, b = gate
    edge = local_distance(*a, *b)
    p, q = local_distance(*a, *before), local_distance(*a, *after)
    sp, sq = cross(edge, p), cross(edge, q)
    if not sp < 0 <= sq:
        return False
    fraction = -sp / (sq - sp)
    hit = [p[i] + fraction*(q[i]-p[i]) for i in (0,1)]
    along = sum(hit[i]*edge[i] for i in (0,1)) / sum(v*v for v in edge)
    return 0 <= along <= 1


def inside(polygon, point):
    if len(polygon) < 3 or point[0] is None or point[1] is None:
        return False
    x, y = point
    result = False
    j = len(polygon)-1
    for i, (xi, yi) in enumerate(polygon):
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj-xi)*(y-yi)/(yj-yi)+xi:
            result = not result
        j = i
    return result


class RouteProgress:
    def __init__(self, options):
        self.options = options
        self.entry_count = 0
        self.finished = False
        self.previous = None
        self.last_at = None

    @property
    def entered(self):
        return bool(self.options.entry_gates) and self.entry_count == len(self.options.entry_gates)

    def update(self, t, now, timeout):
        if self.last_at == t.global_at:
            return
        point = (t.lat, t.lon)
        fresh = 0 <= now-t.global_at <= timeout
        continuous = self.last_at is not None and 0 < t.global_at-self.last_at <= timeout
        if fresh and continuous and t.armed and t.mode == 'AUTO':
            if not self.entered and self.options.entry_gates:
                if crossed(self.options.entry_gates[self.entry_count], self.previous, point):
                    self.entry_count += 1
            if self.entered and t.mission_seq is not None and self.options.search_end_seq is not None:
                if t.mission_seq > self.options.search_end_seq and crossed(self.options.finish_gate, self.previous, point):
                    self.finished = True
        self.previous = point if fresh and t.armed and t.mode == 'AUTO' else None
        self.last_at = t.global_at

    def search_allowed(self, t, mission):
        o = self.options
        return (self.entered and not self.finished and mission is not None
                and mission_digest(mission) == o.mission_fingerprint
                and o.search_start_seq is not None and o.search_end_seq is not None
                and t.mission_seq is not None and o.search_start_seq <= t.mission_seq <= o.search_end_seq
                and mission.current_command(t.mission_seq) == 16
                and inside(o.flight_polygon, (t.lat, t.lon)))
