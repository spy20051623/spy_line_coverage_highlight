local react = ug_require('::/gui/main/react.lua')
local area = ug_require('::/gui/main/main_mod_button_area.tl')
local ok, allParams = pcall(function() return api.engine.config.getModParams() end)
local params = ok and type(allParams)=='table' and allParams.spy_line_coverage or nil
ug_require('spy_line_coverage::/coverage.lua').install(params)
local plugin = react.RegisterPluginRecipe(area.MainModButtonAreaExtension,
  'SpyLineCoverageBootstrap', function() return nil end)
function data() return {BootstrapPlugin = plugin} end
