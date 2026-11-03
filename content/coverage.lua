-- TF3 build 40420: direct React forwarding; GUI-only circle overlays.
-- Read station coverage data only; all line editing remains vanilla.
local installed = false
local nextOwnerId = 0
-- ComboBox defaultIndex is zero-based; getModParams returns one-based values.
local palette = {
  {0.05,0.65,1.0,0.35}, -- Original blue, unchanged.
  {0.05,0.8,0.2,0.35},
  {0.05,0.8,0.8,0.35},
  {1.0,0.45,0.05,0.35},
  {0.55,0.2,1.0,0.35},
  {1.0,0.2,0.5,0.35},
  {0.65,0.65,0.65,0.35},
}
local color = palette[1]
local function resolveColor(params)
  local index = type(params)=='table' and params.coverageColor
  if type(index)~='number' or index%1~=0 or not palette[index] then index=1 end
  local c=palette[index]
  return {c[1],c[2],c[3],c[4]}
end
local union = ug_require('spy_line_coverage::/coverage_union.lua')
local function collectGroups(line)
  local groups, seen = {}, {}
  for _, via in ipairs(line and line.path or {}) do
    local id = via.stop and via.stop.stationGroup
    if type(id) == 'number' and id >= 0 and not seen[id]
      and api.engine.entityExists(id)
      and api.engine.getComponent(id, api.type.ComponentType.STATION_GROUP) then
      seen[id] = true
      groups[#groups + 1] = id
    end
  end
  return groups
end
local function finite(n) return type(n)=='number' and n==n and math.abs(n)<math.huge end
local function collectCircles(line)
  local circles, seen = {}, {}
  for _, groupId in ipairs(collectGroups(line)) do
    local group = api.engine.getComponent(groupId, api.type.ComponentType.STATION_GROUP)
    for _, stationId in ipairs(group.stations or {}) do
      if api.engine.entityExists(stationId) then
        local station = api.engine.getComponent(stationId, api.type.ComponentType.STATION)
        for _, area in ipairs(station and station.catchmentAreas or {}) do
          local pos, radius = area.position, area.radius
          if pos and finite(pos.x) and finite(pos.y) and finite(radius) and radius>0 then
            local key = tostring(pos.x)..':'..tostring(pos.y)..':'..tostring(radius)
            if not seen[key] then
              seen[key]=true
              circles[#circles+1]={x=pos.x,y=pos.y,radius=radius,key=key}
            end
          end
        end
      end
    end
  end
  return circles
end
local function clearZones(owner)
  for key in pairs(owner.zones) do
    api.gui.mission.removeZone(key)
    owner.zones[key] = nil
  end
  owner.geometryKey = nil
end
local function syncZones(owner, circles)
  local keys = {}
  for _, circle in ipairs(circles) do keys[#keys+1]=circle.key end
  table.sort(keys)
  local geometryKey = table.concat(keys,'|')
  if owner.geometryKey==geometryKey then return end
  local polygons = union.outlines(circles)
  clearZones(owner)
  for i, polygon in ipairs(polygons) do
    local points = {}
    for _,p in ipairs(polygon) do points[#points+1]=api.type.Vec2f.new(p.x,p.y) end
    local key = 'spy_line_coverage:editor:' .. owner.id .. ':region:' .. i
    -- Draw only real boundary loops; never draw a hole's artificial bridge.
    api.gui.mission.setZone(key, points, true,
      api.type.Vec4f.new(color[1],color[2],color[3],color[4]), false, false)
    owner.zones[key] = true
  end
  owner.geometryKey=geometryKey
  print('[spy_line_coverage] Union regions: '..#polygons..'; station circles: '..#circles)
end
local function install(lineUtil,react,params)
  if installed then return end
  color = resolveColor(params)
  local original=lineUtil.makeLineActionDescriptor
  assert(type(original)=='function','unsupported LineUtil')
  lineUtil.makeLineActionDescriptor=function(common,...)
    local owner = react.useStateLazy(function()
      nextOwnerId = nextOwnerId + 1
      return {id = nextOwnerId, zones = {}}
    end):old()
    react.onUnmount(function() clearZones(owner) end)
    local line=common and common.lineState and common.lineState:old()
    syncZones(owner, collectCircles(line))
    -- Preserve the original renderer's tail-call context. A pcall-only no-op
    -- wrapper reproduced the native bridge crash without any added graphics.
    return original(common,...)
  end
  installed=true
  print('[spy_line_coverage] Installed configurable union coverage 1.0.0; direct React forwarding.')
end
return {
  install=function(params)install(ug_require('::/gui/line_vehicle_mgmt/line_util.tl'),ug_require('::/gui/main/react.lua'),params)end,
  resolveColor=resolveColor,
  collectGroups=collectGroups,
  collectCircles=collectCircles,
  syncZones=syncZones,
  clearZones=clearZones,
}
