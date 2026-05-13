# 直齿轮标准件评审事实

用于静态审查和截图审查齿轮标准件任务，避免用通用齿轮直觉误判模板几何。

## 模板几何事实

- 标准直齿轮模板不是运行时从零绘制齿形，而是从 `standard_swpart/gear/spur_gear.SLDPRT` 复制到工作区后修改方程式。
- 模板齿轮从 `Z = 0` 平面开始，沿正 Z 方向拉伸到齿宽 `B`。
- 模板中心不在 `Z = 0`；齿轮中面在 `Z = B / 2`。
- 不要要求该模板必须双向拉伸，也不要因为中面不在 `Z = 0` 判失败。

## 二次切除事实

- 中心孔通常在 `XY` 平面建草图，从底面向正 Z 方向切除。
- 通孔切除深度应使用齿宽对应的米制值；例如 `B = 10mm` 时，切除深度为 `0.01`。
- 封装级稳定流程是 `insert_sketch_on_plane("XY") -> create_circle(..., "XY") -> extrude_cut(sketch, depth)`。
- 不要建议用 `SelectByID2`、`InsertSketch2`、`sw_doc` 或 `sw_instance` 修复齿轮通孔。

## 单位事实

- SolidWorks Python 建模 API 的长度单位是米：12mm 通孔半径为 `0.006`，10mm 齿宽为 `0.01`。
- 参考轴端点也使用米，且只需表达方向；10mm 齿宽可用 `[0, 0, 0]` 到 `[0, 0, 0.01]`。
- `set_global_variable` 修改的是 SolidWorks 方程式，带单位变量应沿用原方程单位字符串：`M="2mm"`、`B="10mm"`、`Alpha="20deg"`；`Z`、`Hax`、`Cx` 使用裸数字字符串。
