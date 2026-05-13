# 齿轮标准件工作流

直齿轮和标准件驱动的齿轮修改使用本参考文档。

## 标准件源文件

可复用直齿轮模板：

```text
D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT
```

绝对不要直接修改该源文件。必须先复制或物化到当前任务工作区，打开工作副本，然后只修改工作副本。

## 默认主动参数

齿轮模板由以下主动全局变量控制：

```json
{
  "M": {"default": 2, "unit": "mm", "meaning": "模数"},
  "Z": {"default": 30, "unit": "count", "meaning": "齿数"},
  "B": {"default": 10, "unit": "mm", "meaning": "齿宽"},
  "Alpha": {"default": 20, "unit": "deg", "meaning": "压力角"},
  "Hax": {"default": 1, "unit": "coefficient", "meaning": "齿顶高系数"},
  "Cx": {"default": 0.25, "unit": "coefficient", "meaning": "顶隙系数"}
}
```

只设置零件规格明确要求或显式假设需要修改的变量。需求没有覆盖的参数应保持默认值。

## 参数关系

- 分度圆直径：`d = M * Z`。
- 齿顶圆直径：`da = M * (Z + 2 * Hax)`。
- 齿根圆直径受 `M`、`Z`、`Hax` 和 `Cx` 影响；除非模板暴露独立变量，否则不要单独设置。
- 齿宽由 `B` 控制。
- 在 `M` 固定时，增大 `Z` 会增大齿轮直径。
- 在 `Z` 固定时，增大 `M` 会放大齿形尺寸和齿轮直径。
- 除非需求明确要求其他压力角，`Alpha` 通常保持 `20`。

修改参数时，应通过主动全局变量保持从动尺寸一致，不要手动编辑依赖几何。

## 方程式单位规则

齿轮模板的主动参数来自 SolidWorks 方程式。修改带单位的方程式目标时，传给 `set_global_variable` 的值必须带单位后缀，并按模板原方程单位表达；不要把带单位目标写成裸数字字符串，也不要按 SW Python API 的米制规则改写方程式值。

- `M` 是长度量，模板当前使用 mm，必须写成 `"2mm"`、`"1.5mm"` 这类带 `mm` 的字符串。
- `B` 是长度量，模板当前使用 mm，必须写成 `"10mm"`、`"20mm"` 这类带 `mm` 的字符串。
- `Alpha` 是角度量；如果需要修改，使用带角度单位的表达，例如 `"20deg"`。未明确要求时保持模板默认值。
- `Z`、`Hax`、`Cx` 是无量纲参数，保持裸数字字符串，例如 `"24"`、`"1"`、`"0.25"`。

正确示例：

```python
sgear.set_global_variable("M", "2mm")
sgear.set_global_variable("Z", "24")
sgear.set_global_variable("B", "10mm")
```

错误示例：

```python
sgear.set_global_variable("M", "2")
sgear.set_global_variable("B", "10")
```

## 代码模式

```python
from pysw import SldWorksApp, PartDoc, AssemDoc
import pysw
import os

swapp = SldWorksApp()

sgear = PartDoc(swapp.copy_standard_part_to_workdir_and_open(
    standard_part_path=r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT",
    workdir=r"D:\work\assem_test",
    new_part_name="gear_001.SLDPRT",))

# 齿轮主动参数（不包含从动参数）：
# M = 2mm        # 模数
# Z = 30         # 齿数
# B = 10mm       # 齿宽
# Alpha = 20     # 压力角
# Hax = 1        # 齿顶高系数
# Cx = 0.25      # 顶隙系数
sgear.set_global_variable("M", "2mm")
sgear.set_global_variable("Z","40")
sgear.set_global_variable("B", "10mm")


# 下面是一些示例操作，展示如何使用 PartDoc 类的方法来二次修改零件。
# 注意：这些 SolidWorks Python API 的长度单位是 m，0.01 表示 10mm。
sketch1 = sgear.insert_sketch_on_plane("XY")
# 齿轮是从Z=0开始拉伸的，所以在XY平面上画一个圆，作为拉伸的轮廓
sgear.create_circle(0,0,0.01,"XY")
# 拉伸切除，从底面向上切除，切除深度 0.01m = 10mm = 齿宽，切除后齿轮会有一个通孔
sgear.extrude_cut(sketch1,0.01)

sgear.create_axis([0,0,0], [0,0,0.01], "axis")
sgear.create_ref_plane("XY", 0.01/2, "mid_plane")
sgear.create_ref_plane("XY", 0.01, "top_plane")
sgear.create_ref_plane("XY", 0, "bottom_plane")
```

生成任务代码时，应使用编排器提供的工作区路径，不要硬编码示例中的 `workdir` 和 `new_part_name`。

## 零件二次修改

二次修改应在打开已物化的齿轮工作副本之后进行。

中心通孔示例：

```python
sketch1 = sgear.insert_sketch_on_plane("XY")
sgear.create_circle(0, 0, 0.01, "XY")
sgear.extrude_cut(sketch1, 0.01)
```

该流程已验证可正常切除。生成代码和返修代码应优先保持这个封装级调用模式：

1. `sketch1 = sgear.insert_sketch_on_plane("XY")`
2. `sgear.create_circle(0, 0, radius, "XY")`
3. `sgear.extrude_cut(sketch1, depth)`

不要在这个流程中额外调用底层 COM 选择接口，例如：

- `SelectByID2`
- `InsertSketch2`
- `sgear.sw_doc`
- `sgear.sw_instance`
- `sgear_doc.Extension.SelectByID2`

这些底层调用容易造成类型不匹配或属性不存在。出现“草图选择失败，无法拉伸”时，优先回退到上面的三步封装流程，而不是增加底层选择代码。

注意：

- 模板齿轮从 `Z = 0` 开始拉伸。
- 在 `XY` 平面上的圆可以定义从底面向上的孔或切除轮廓。
- 切除深度应匹配所需贯穿特征。完整通孔通常使用齿宽或需求明确指定的切除深度。
- 孔半径、切除深度、参考面偏移和轴端点都必须使用米；例如 12mm 通孔半径是 `0.006`，10mm 齿宽是 `0.01`。
- 参考轴端点不应超出齿轮数量级太多。对于 10mm 齿宽，`create_axis([0,0,0], [0,0,0.01], "shaft_axis")` 已足够表达方向；不要写成 `[0,0,10]`。
- 孔半径、切除深度和齿宽优先使用命名变量，便于后续局部修复。

## 接口命名

在代码注释、日志或 sidecar 元数据中暴露稳定外部接口。独立齿轮零件只需体现用户明确要求的功能接口；齿轮副或装配任务才把这些接口作为后续配合的硬需求：

- `shaft_axis`：中心旋转轴。
- `front_face`：正向端面或零件规格指定的一侧。
- `back_face`：相反端面。
- `bore_cylindrical_face`：生成孔之后的内圆柱面。
- `pitch_circle_reference`：由 `M * Z` 推导的节圆参考。
- `gear_mid_plane`：需要装配约束时可使用 `B / 2` 处的齿轮中面。

对于齿轮副装配，下游装配代码需要轴线、分度圆直径关系、端面对齐面和预期中心距。

## 修复策略

- 如果请求参数错误，优先局部修改 `latest_code.py` 中的 `set_global_variable` 调用。
- 如果齿轮尺寸关系错误，先修复建模思路，因为从动尺寸可能需要重新计算。
- 如果二次特征缺失，在标准件打开之后局部添加或修复对应特征代码。
- 如果源资产路径失败，分类为 `asset_binding_error`，并从正确的标准件源物化。
