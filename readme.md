# Line Coverage Highlight / 线路覆盖范围高亮

编辑线路时，高亮显示沿线各车站合并后的覆盖范围，方便查看覆盖缺口和重复覆盖。可直接在已有存档中启用，不依赖其他模组。

## 范围显示

打开线路管理并选择一条线路后，地图上会显示该线路各停靠站合并后的覆盖范围。增删停靠站时，范围会自动更新；关闭线路编辑后自动隐藏。

## 颜色配置

在模组选项的「覆盖范围颜色」中选择高亮颜色。

可选颜色：蓝色（默认）、绿色、青色、橙色、紫色、粉色、白色。

## 项目与开发

[GitHub 仓库](https://github.com/spy20051623/spy_line_coverage_highlight)

本模组由 spy 与 AI 协作开发。作者：spy。版本：1.0.0。Mod ID：`spy_line_coverage`。

## 安装

在游戏模组中心订阅本模组，并在存档的模组列表中启用。

## English

Highlight combined station coverage while editing a line. Works with existing saves and requires no other mods.

Open line management and select a line to see its combined coverage. The outline updates as stops change and hides when line editing closes.

Choose the highlight color under Coverage color in the mod options. Available colors: blue (default), green, cyan, orange, purple, pink and white.

Developed by spy in collaboration with AI.

## 开发检查 / Development checks

安装 Python 依赖后运行离线检查：

```powershell
python -m pip install -r requirements-dev.txt
python tools/verify_coverage_union.py
python tools/verify_line_coverage_colors.py
python tools/verify_line_coverage.py
```

原版 helper 检查读取本机游戏的 base/content/base.zip 和 gui.zip，不启动游戏；默认游戏路径写在 `tools/verify_line_coverage.py` 的 `GAME` 常量中，安装位置不同时请调整。另两项验证不依赖游戏安装。

The helper check reads installed vanilla UI sources without launching the game. Set `GAME` in `tools/verify_line_coverage.py` to your installation path. Geometry and color checks do not require a game installation.

## 验证记录

1.0.0 已在游戏内确认默认蓝色显示及通过模组选项切换为绿色后正常显示。空洞轮廓修正已通过离线验证，游戏内验证待后续进行；其他颜色及模组组合尚未逐项实测。

日志前缀为 `[spy_line_coverage]`。反馈问题时请提供版本、复现步骤及截图。
