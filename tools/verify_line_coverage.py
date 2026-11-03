"""Exercise the installed vanilla UI helper with simulated native constructors."""
import json
import zipfile
from pathlib import Path
from lupa.lua52 import LuaRuntime

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT
GAME = Path(r'D:\Program Files\Steam\steamapps\common\Transport Fever 3')
for path in MOD.rglob('*.json'):
    json.loads(path.read_text(encoding='utf-8'))
lua = LuaRuntime(unpack_returned_tuples=True)
with zipfile.ZipFile(GAME / 'base/content/base.zip') as z:
    tl = lua.execute(z.read('base/tl.lua').decode('utf-8-sig'))
with zipfile.ZipFile(GAME / 'base/content/gui.zip') as z:
    source = z.read('gui/line_vehicle_mgmt/line_util.tl').decode('utf-8-sig')
start = source.index('line_util.makeLineActionDescriptor = function')
end = source.index('\nend', start) + len('\nend')
compiled, result = tl.gen(source[start:end])
assert compiled, result

lua.execute(r'''
nodes = {}; nextNode = 0
function node(kind, params)
  nextNode = nextNode + 1; nodes[nextNode] = {kind=kind, params=params}; return nextNode
end
function constructor() return {} end
local function opaque()
  return setmetatable({}, {__index=function(t,k) local v=opaque(); rawset(t,k,v); return v end})
end
resource = opaque()
api={
  engine={entityExists=function(id) return id~=99 end,
    getComponent=function(id,ct)
      if ct==3 and id==42 then return {} end
      if ct==1 and (id==10 or id==20) then return {stations={id+1}} end
      if ct==2 and (id==11 or id==21) then return {catchmentAreas={{position={x=id*10,y=50},radius=100}}} end
      return nil end},
  type={ComponentType={STATION_GROUP=1,STATION=2,LINE=3}, StationTerminal={new=constructor},Vec3f={new=function(x,y,z)return {x=x,y=y,z=z}end},Vec2f={new=function(x,y)return {x=x,y=y}end},
    Vec4f={new=function(r,g,b,a)return {r=r,g=g,b=b,a=a}end},
    ['enum']={BackgroundContrastMode={Both=1,LineVehicleManager=2}},
    LayerConfig={PlotsRenderableConfig={new=constructor},new=constructor, CatchmentAreaRenderableConfig={new=constructor},CatchmentAreaDisplaySettings={new=constructor},
      ColorPassFn={LineVehicleColor={new=constructor},new=constructor}}},
  gui={genericRep={find=function()return 1 end,get=function()return {data=resource} end},
    SelectionDetails={Type={Town=1}}, camera={getHeightAboveTerrain=function()return 0 end}},
}
local function dummy()return {}end
engine_react_util={useStepState=function()return {old=function()return false end}end}
layer_react_util={createDefaultFallbackColor=dummy}
hud_react_util={makeDefaultVisibilityThresholds=dummy,resetSubEntityThresholds=function(x)return x end,
  makeVehicleIconOffsets=dummy,makeDefaultLineViewerSnapFactors=dummy}
color_util={toVec4=dummy,withTransparency=dummy}
app_util={getMouseOrGamepad=function(a,b)return a end}
makeDefaultOnSelect=dummy;makeDefaultOnHover=dummy
builtin={LayerConfig=function(p)return node('layer',p)end,
 ActionDescriptor=function(p)return node('action',p)end,
 LineViewer=function(p)return node('viewer',p)end, Selector=function(p)return node('selector',p)end}
zones={foreign={}}; zoneAdds=0; zoneRemoves=0
api.gui.mission={
 setZone=function(key,points,draw,color,prohibit,animate)
  assert(draw==true and prohibit==false and animate==false)
  assert(color.r==0.05 and color.g==0.65 and color.b==1.0 and color.a==0.35)
  assert(#points>=3 and key:match('^spy_line_coverage:editor:'))
  zones[key]={points=points};zoneAdds=zoneAdds+1
 end,
 removeZone=function(key)
  assert(key~='foreign');zones[key]=nil;zoneRemoves=zoneRemoves+1
 end,
}
react={RegisterWrapperRecipe=function(name,original,fn)return fn end,
 useStateLazy=function(fn)
  if not ownerState then ownerState=fn()end
  return {old=function()return ownerState end}
 end,
 onUnmount=function(fn)unmountCoverage=fn end,
}
line_util={}
ug_require=function(path)
 if path=='spy_line_coverage::/coverage_union.lua' then return coverage_union end
 if path=='::/gui/main/react.lua' then return react end
 if path=='::/gui/line_vehicle_mgmt/line_util.tl' then return line_util end
 if path=='::/gui/main/builtin.lua' then return builtin end
 error('unexpected module '..path)
end
''')
lua.globals().coverage_union = lua.execute((MOD / 'content/coverage_union.lua').read_text(encoding='utf-8'))
lua.execute(compiled)
lua.execute(r'''
function callEditor(line)
 local common={lineState={old=function()return line end}}
 return line_util.makeLineActionDescriptor(common,{},nil,function()end,{{entity=42}},nil,{7},
  {mouseCursor=123},function()end,function()end,true,false,false,false,'2D',false,false)
end
line={entityAndRevision={entity=42},path={{stop={stationGroup=10}}, {waypoint={}},
 {stop={stationGroup=20}}, {stop={stationGroup=10}}, {stop={stationGroup=99}}}}
baseline=callEditor(line)
originalLayer=builtin.LayerConfig;originalAction=builtin.ActionDescriptor
''')
coverage = lua.execute((MOD / 'content/coverage.lua').read_text(encoding='utf-8'))
lua.globals().coverage = coverage
coverage.install()
lua.execute(r'''
local function layerFor(line)
 local id=callEditor(line);local action=nodes[id].params
 assert(#action.children==3)
 assert(builtin.LayerConfig==originalLayer and builtin.ActionDescriptor==originalAction)
 local layer=nodes[action.children[1]].params.config
 assert(layer.colorPassFn~=nil and layer.plotsRenderableConfig==nil)
 return layer
end
local function ownZoneCount()
 local n=0;for key in pairs(zones)do if key~='foreign'then n=n+1 end end;return n
end
local circles=coverage.collectCircles(line)
assert(#circles==2)
layerFor(line);assert(ownZoneCount()==1)
local count=zoneAdds
layerFor(line);assert(zoneAdds==count)
layerFor({path={{stop={stationGroup=20}},{stop={stationGroup=10}}}})
assert(zoneAdds==count)
for _,circle in ipairs(circles)do
 local covered=false
 for key,zone in pairs(zones)do
  if key~='foreign' and coverage_union.contains(zone.points,{x=circle.x,y=circle.y})then covered=true end
 end
 assert(covered)
end
layerFor({path={{stop={stationGroup=10}},{stop={stationGroup=10}}}})
assert(ownZoneCount()==1)
local exists=api.engine.entityExists
api.engine.entityExists=function(id)return id~=21 and exists(id)end
layerFor(line);assert(ownZoneCount()==1)
api.engine.entityExists=exists
layerFor({path={{waypoint={}}}});assert(ownZoneCount()==0)
local wrapped=line_util.makeLineActionDescriptor;local calls=0
line_util.makeLineActionDescriptor=function(...)calls=calls+1;return wrapped(...)end
layerFor(line);assert(calls==1 and ownZoneCount()==1)
unmountCoverage();assert(ownZoneCount()==0 and zones.foreign)
local first={id=998,zones={}};local second={id=999,zones={}}
coverage.syncZones(first,circles);coverage.syncZones(second,circles)
assert(ownZoneCount()==2)
coverage.clearZones(first);assert(ownZoneCount()==1)
coverage.clearZones(second);assert(ownZoneCount()==0 and zones.foreign)
''')
for path in (MOD / 'content').glob('*.lua'):
    lua.execute('assert(load(...))', path.read_text(encoding='utf-8'))
lua.execute(r'''
react={RegisterPluginRecipe=function(area,name,fn)return fn end}
ug_require=function(path)
 if path=='::/gui/main/react.lua' then return react end
 if path=='::/gui/line_vehicle_mgmt/line_util.tl' then return line_util end
 if path=='::/gui/main/builtin.lua' then return builtin end
 if path=='::/gui/main/main_mod_button_area.tl' then return {MainModButtonAreaExtension={}} end
 if path=='spy_line_coverage::/coverage.lua' then return coverage end
 error('unexpected module '..path)
end
''')
lua.execute((MOD / 'content/coverage_bootstrap.script.lua').read_text(encoding='utf-8'))
lua.execute('assert(data().BootstrapPlugin()==nil)')
assert '.install(params)' in (MOD / 'content/coverage_bootstrap.script.lua').read_text(encoding='utf-8')
print('PASS: original blue RGBA, vanilla helper, union polygons, station coverage, cached updates, empty-line cleanup, unmount cleanup, owner isolation and chaining')
print('Native rendering is simulated; simultaneous coverage still requires game verification.')
