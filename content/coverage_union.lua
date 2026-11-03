-- Circle-union boundaries: only exposed arcs become polygon edges.
-- No convex hull: disconnected coverage and uncovered holes stay separate.
local tau, epsilon = 2 * math.pi, 1e-7
local function angle(x, y) return math.atan2(y, x) % tau end
local function nodeKey(p)
  return math.floor(p.x * 10000 + 0.5) .. ':' .. math.floor(p.y * 10000 + 0.5)
end
local function point(c, a)
  return {x=c.x+c.radius*math.cos(a), y=c.y+c.radius*math.sin(a)}
end
local function signedArea(poly)
  local area = 0
  for i, p in ipairs(poly) do
    local q = poly[i % #poly + 1]
    area = area + p.x*q.y - q.x*p.y
  end
  return area / 2
end
local function contains(poly, p)
  local inside = false
  for i, a in ipairs(poly) do
    local b = poly[i % #poly + 1]
    if (a.y > p.y) ~= (b.y > p.y)
      and p.x < a.x + (p.y-a.y)*(b.x-a.x)/(b.y-a.y) then
      inside = not inside
    end
  end
  return inside
end
local function contours(circles)
  local cuts, arcs, outgoing = {}, {}, {}
  for i in ipairs(circles) do cuts[i] = {0, tau} end
  for i, a in ipairs(circles) do
    for j=i+1,#circles do
      local b = circles[j]
      local dx, dy = b.x-a.x, b.y-a.y
      local d = math.sqrt(dx*dx+dy*dy)
      if d > math.abs(a.radius-b.radius)+epsilon
        and d < a.radius+b.radius-epsilon then
        local along = (a.radius*a.radius-b.radius*b.radius+d*d)/(2*d)
        local height = math.sqrt(math.max(0,a.radius*a.radius-along*along))
        for _, sign in ipairs({-1,1}) do
          local x = a.x + along*dx/d - sign*height*dy/d
          local y = a.y + along*dy/d + sign*height*dx/d
          cuts[i][#cuts[i]+1] = angle(x-a.x,y-a.y)
          cuts[j][#cuts[j]+1] = angle(x-b.x,y-b.y)
        end
      end
    end
  end
  for i, c in ipairs(circles) do
    local covered = false
    for j, other in ipairs(circles) do
      local dx,dy = c.x-other.x,c.y-other.y
      if i~=j and math.sqrt(dx*dx+dy*dy)+c.radius<=other.radius+epsilon
        and (c.radius<other.radius or j<i) then covered=true;break end
    end
    table.sort(cuts[i])
    for k=1,#cuts[i]-1 do
      local a, b = cuts[i][k], cuts[i][k+1]
      if not covered and b-a > epsilon then
        local middle, exposed = point(c,(a+b)/2), true
        for j, other in ipairs(circles) do
          local dx, dy = middle.x-other.x, middle.y-other.y
          if i ~= j and dx*dx+dy*dy < other.radius*other.radius-epsilon then
            exposed = false
            break
          end
          -- Identical input circles are safe even outside collectCircles.
          if j < i and c.x==other.x and c.y==other.y and c.radius==other.radius then
            exposed = false
            break
          end
        end
        if exposed then
          local samples, steps = {}, math.max(1,math.ceil((b-a)/(tau/96)))
          for step=0,steps do samples[#samples+1] = point(c,a+(b-a)*step/steps) end
          local arc = {points=samples, start=nodeKey(samples[1]), finish=nodeKey(samples[#samples])}
          arcs[#arcs+1] = arc
          outgoing[arc.start] = outgoing[arc.start] or {}
          table.insert(outgoing[arc.start],arc)
        end
      end
    end
  end
  local loops = {}
  for _, first in ipairs(arcs) do
    if not first.used then
      local polygon, arc, finish = {}, first, nil
      while arc and not arc.used do
        arc.used = true
        for i=1,#arc.points-1 do polygon[#polygon+1] = arc.points[i] end
        finish = arc.finish
        if finish == first.start then break end
        local nextArc = nil
        for _, candidate in ipairs(outgoing[finish] or {}) do
          if not candidate.used then nextArc = candidate; break end
        end
        arc = nextArc
      end
      assert(finish==first.start, 'coverage union boundary did not close')
      if #polygon>=3 and math.abs(signedArea(polygon))>epsilon then
        loops[#loops+1] = polygon
      end
    end
  end
  return loops
end
-- Bridge holes to the outside using a zero-width slit. This preserves area
-- and uncovered interiors without overlapping filled polygons.
local function bridge(outer, hole)
  local hi = 1
  for i,p in ipairs(hole) do if p.x>hole[hi].x then hi=i end end
  local h, bestX, edge = hole[hi], math.huge, nil
  for i,a in ipairs(outer) do
    local b = outer[i % #outer+1]
    if (a.y>h.y) ~= (b.y>h.y) then
      local x = a.x+(h.y-a.y)*(b.x-a.x)/(b.y-a.y)
      if x>=h.x and x<bestX then bestX,edge=x,i end
    end
  end
  assert(edge, 'coverage hole has no enclosing boundary')
  local e, result = {x=bestX,y=h.y}, {}
  for i=1,edge do result[#result+1]=outer[i] end
  result[#result+1]=e
  for offset=0,#hole-1 do result[#result+1]=hole[(hi+offset-1)%#hole+1] end
  result[#result+1]=h
  result[#result+1]=e
  for i=edge+1,#outer do result[#result+1]=outer[i] end
  return result
end
local function build(circles)
  local loops, outers, holes = contours(circles), {}, {}
  for _, loop in ipairs(loops) do
    if signedArea(loop)>0 then outers[#outers+1]=loop else holes[#holes+1]=loop end
  end
  table.sort(holes,function(a,b)
    local function rightmost(poly)
      local x=-math.huge;for _,p in ipairs(poly)do x=math.max(x,p.x)end;return x
    end
    return rightmost(a)>rightmost(b)
  end)
  for _, hole in ipairs(holes) do
    local found = false
    for i, outer in ipairs(outers) do
      if contains(outer,hole[1]) then outers[i]=bridge(outer,hole);found=true;break end
    end
    assert(found, 'coverage hole was not enclosed')
  end
  return outers
end
-- Zone rendering outlines every polygon edge, including zero-width bridges.
-- Send outer/hole boundaries separately; normalize winding for the native API.
local function outlines(circles)
  local loops = contours(circles)
  for i,loop in ipairs(loops) do
    if signedArea(loop)<0 then
      local reversed={}
      for j=#loop,1,-1 do reversed[#reversed+1]=loop[j] end
      loops[i]=reversed
    end
  end
  return loops
end
return {build=build, contours=contours, outlines=outlines, signedArea=signedArea, contains=contains}
