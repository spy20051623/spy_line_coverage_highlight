"""Offline bootstrap-to-render parameter checks; never starts the game."""
import json
from pathlib import Path
from lupa.lua52 import LuaRuntime

MOD = Path(__file__).resolve().parents[1]
definition = json.loads((MOD/'mod.json').read_text(encoding='utf-8'))
translations = json.loads((MOD/'strings.json').read_text(encoding='utf-8'))
option = definition['params'][0]
assert option['key']=='coverageColor' and option['defaultIndex']==0
assert len(option['values'])==7 and option['uiType']=='ComboBox'
for locale in translations.values():
    assert all(key in locale for key in [option['name'],option['tooltip'],*option['values']])
expected = [(0.05,0.65,1.0), (0.05,0.8,0.2), (0.05,0.8,0.8),
            (1.0,0.45,0.05), (0.55,0.2,1.0), (1.0,0.2,0.5), (0.65,0.65,0.65)]
cases = [(str(i), expected[i-1]) for i in range(1,8)]
cases += [(v,expected[0]) for v in ['nil','0','8','-1','1.5','0/0','math.huge',"'2'",'{}']]
for value, rgb in cases:
    for failure in ([False,True] if value=='nil' else [False]):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
react={useStateLazy=function(fn)return {old=fn}end,onUnmount=function()end,
 RegisterPluginRecipe=function(area,name,fn)return fn end}
lineUtil={makeLineActionDescriptor=function()return 123 end}
api={engine={config={}},type={Vec2f={new=function(x,y)return {x=x,y=y}end},
 Vec4f={new=function(r,g,b,a)return {r,g,b,a}end}},gui={mission={
 setZone=function(key,points,draw,color,prohibit,animate)
  rendered=color;assert(draw and not prohibit and not animate)
 end,removeZone=function()end}}}
ug_require=function(path)
 if path=='spy_line_coverage::/coverage_union.lua'then return {outlines=function()return {{{x=0,y=0},{x=1,y=0},{x=0,y=1}}}end}end
 if path=='::/gui/main/react.lua'then return react end
 if path=='::/gui/line_vehicle_mgmt/line_util.tl'then return lineUtil end
 if path=='::/gui/main/main_mod_button_area.tl'then return {MainModButtonAreaExtension={}}end
 if path=='spy_line_coverage::/coverage.lua'then return coverage end
 error(path)
end
''')
        lua.execute('api.engine.config.getModParams=function() '+
                    ("error('unavailable')" if failure else 'return {spy_line_coverage={coverageColor='+value+'}}')+' end')
        lua.globals().coverage = lua.execute((MOD/'content/coverage.lua').read_text(encoding='utf-8'))
        lua.execute((MOD/'content/coverage_bootstrap.script.lua').read_text(encoding='utf-8'))
        lua.execute("coverage.syncZones({id=1,zones={}},{{key='circle'}})")
        color=lua.globals().rendered
        assert tuple(color[i] for i in range(1,5))==(*rgb,0.35),value
        lua.execute('assert(data().BootstrapPlugin()==nil)')
print('PASS: 7 colors through real bootstrap/install/render, original blue default, invalid/missing parameters, unavailable config API, localized option keys; offline only')
