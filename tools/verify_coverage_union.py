"""Check union geometry independently of native rendering."""
import math
from pathlib import Path
import random
from lupa.lua52 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
lua = LuaRuntime(unpack_returned_tuples=True)
union = lua.execute((ROOT / 'content/coverage_union.lua').read_text(encoding='utf-8'))

def build(circles):
    values = lua.table_from([lua.table_from(dict(x=x, y=y, radius=r)) for x, y, r in circles])
    return union.build(values), union.contours(values)

def check(circles, seed):
    polygons, loops = build(circles)
    assert abs(sum(union.signedArea(p) for p in polygons.values()) - sum(union.signedArea(p) for p in loops.values())) < 1e-5
    rng = random.Random(seed)
    low_x = min(x-r for x, y, r in circles)
    high_x = max(x+r for x, y, r in circles)
    low_y = min(y-r for x, y, r in circles)
    high_y = max(y+r for x, y, r in circles)
    for _ in range(800):
        x, y = rng.uniform(low_x-1, high_x+1), rng.uniform(low_y-1, high_y+1)
        # Arc tessellation is inscribed: skip its bounded approximation band.
        if any(abs(math.hypot(x-cx, y-cy)-r) < r*0.0007 for cx, cy, r in circles):
            continue
        expected = any((x-cx)**2+(y-cy)**2 < r*r for cx, cy, r in circles)
        point = lua.table_from(dict(x=x, y=y))
        actual = any(union.contains(p, point) for p in polygons.values())
        assert actual == expected, (circles, x, y, expected, actual)
    return polygons, loops

single, _ = check([(0, 0, 100)], 1)
assert abs(union.signedArea(single[1]) / (math.pi*100**2) - 1) < 0.001
overlap, _ = check([(0, 0, 100), (100, 0, 100)], 2)
lens = 2*100**2*math.acos(0.5) - 0.5*100*math.sqrt(4*100**2-100**2)
assert len(overlap) == 1
assert abs(union.signedArea(overlap[1])/(2*math.pi*100**2-lens)-1) < 0.001
separate, _ = check([(0, 0, 100), (400, 0, 100)], 3)
assert len(separate) == 2
contained, _ = check([(0, 0, 100), (-50, 0, 50), (0, 0, 100)], 4)
assert len(contained) == 1
tangent, _ = check([(0, 0, 100), (200, 0, 100)], 5)
assert len(tangent) == 2
ring, loops = check([(0, 0, 100), (180, 0, 100), (90, 90*math.sqrt(3), 100)], 6)
assert len(ring) == 1 and len(loops) == 2
assert not union.contains(ring[1], lua.table_from(dict(x=90, y=30*math.sqrt(3))))
assert len(union.build(lua.table())) == 0

def check_boundary(circles):
    values = lua.table_from([lua.table_from(dict(x=x,y=y,radius=r)) for x,y,r in circles])
    outlines = union.outlines(values)
    max_edge = 2*max(r for x,y,r in circles)*math.sin(math.pi/96)+0.001
    seen = set()
    for poly in outlines.values():
        assert union.signedArea(poly)>0
        for i in range(1,len(poly)+1):
            a,b=poly[i],poly[i%len(poly)+1]
            assert math.hypot(a.x-b.x,a.y-b.y)<=max_edge, 'artificial straight connector'
            key=tuple(sorted([(round(a.x,6),round(a.y,6)),(round(b.x,6),round(b.y,6))]))
            assert key not in seen, 'repeated bridge edge'
            seen.add(key)
    return outlines

hole_case=[(0,0,100),(180,0,100),(90,90*math.sqrt(3),100)]
assert len(check_boundary(hole_case))==2
# Preserve the hole's actual boundary instead of inserting a long return edge.
two_rng=random.Random(20261103)
for case in range(300):
    x,y=two_rng.uniform(-10000,10000),two_rng.uniform(-10000,10000)
    r1,r2=two_rng.uniform(50,500),two_rng.uniform(50,500)
    direction=two_rng.uniform(0,2*math.pi)
    distance=two_rng.uniform(0,1.2)*(r1+r2)
    circles=[(x,y,r1),(x+distance*math.cos(direction),y+distance*math.sin(direction),r2)]
    check_boundary(circles)
rng = random.Random(20261013)
for case in range(30):
    circles = [(rng.uniform(-400, 400), rng.uniform(-400, 400), rng.uniform(30, 180)) for _ in range(12)]
    check(circles, case+10)
print('PASS: overlapping union area, disconnected regions, containment, duplicates, tangency, uncovered holes, empty input and 30 randomized 12-circle cases')
print('Native polygon appearance is separate from geometry correctness.')
print('PASS: hole outlines have no bridge edge; 300 rotated/translated unequal-radius two-circle cases have no long straight connectors')
