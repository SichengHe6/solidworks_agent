# SolidWorks 零件 API 参考

该文档由 v2 `PartModelingAgent Knowledge Base` 归纳而来。用于代码生成和局部修复阶段。

## 应用与文档

```python
class SldWorksApp:
    def __init__(self): ...
    def createAndActivate_sw_part(self, part_name: str) -> "PartDoc": ...
    def createAndActivate_sw_assembly(self, assem_name: str) -> "PartDoc": ...

class PartDoc:
    def __init__(self, sw_doc): ...
    def save_as(self, path: str) -> bool: ...
    def set_global_variable(self, variable_name: str, value, rebuild: bool = True) -> bool: ...
```

生成代码必须创建或打开零件文档，并保存到 `part_spec.workspace.model_file` 或固定工作区下的等价目标路径。

### `set_global_variable` 方程式单位

`set_global_variable` 修改的是 SolidWorks 方程式。目标方程式有单位时，传入值必须带单位后缀，并尽量沿用该方程原本单位；这和草图/特征尺寸 API 使用米制数值不同。

- 长度方程式：按原方程单位写字符串，例如 `"2mm"`、`"10mm"` 或 `"2cm"`，不要使用 `"2"`、`"10"`，也不要把 `"2mm"` 错换成 `"0.002m"` 除非原方程本身使用 m。
- 角度方程式：使用 `"20deg"`。
- 无量纲方程式：使用 `"24"`、`"1"`、`"0.25"`。

齿轮模板示例：

```python
sgear.set_global_variable("M", "2mm")
sgear.set_global_variable("Z", "24")
sgear.set_global_variable("B", "10mm")
```

## 草图与工作平面

```python
def create_workplane_p_d(plane: str, offset_val: float) -> object: ...
def insert_sketch_on_plane(plane: str | object) -> object: ...
```

主基准面标记：

- `XY`
- `XZ`
- `ZY`

草图元素：

```python
def create_centre_rectangle(center_x: float, center_y: float, width: float, height: float, sketch_ref: str): ...
def create_circle(center_x: float, center_y: float, radius: float, sketch_ref: str): ...
def create_3point_arc(start_x: float, start_y: float, end_x: float, end_y: float, mid_x: float, mid_y: float, sketch_ref: str): ...
def create_lines(points: list[tuple[float, float]], sketch_ref: str): ...
def create_sketch_fillet(sketch_points: list[tuple[float, float]], radius: float, sketch_ref: str): ...
def create_sketch_chamfer(sketch_points: list[tuple[float, float]], distance: float, angle: float, sketch_ref: str): ...
def create_ellipse(center_x: float, center_y: float, length: float, width: float, sketch_ref: str) -> object: ...
def create_construction_line(x1: float, y1: float, x2: float, y2: float, sketch_ref: str): ...
def create_polygon(center_x: float, center_y: float, radius: float, sides: int, inscribed: bool, sketch_ref: str) -> object: ...
```

注意：不同草图面内部可能有坐标翻转处理。只需按封装要求传入 `sketch_ref`，不要额外做二次坐标补偿。

## 三维特征

```python
def extrude(sketch: object, depth: float, single_direction: bool = True, merge: bool = True) -> object: ...
def extrude_cut(sketch: object, depth: float, single_direction: bool = True) -> object: ...
def revolve(sketch: object, angle: float, merge: bool = True) -> object: ...
def revolve_cut(sketch: object, angle: float) -> object: ...
def sweep(profile_sketch: object, path_sketch: object) -> object: ...
def shell(on_face_points: list[tuple[float, float, float]], thickness: float, outward: bool = False) -> None: ...
def fillet_edges(on_line_points: list[tuple[float, float, float]], radius: float) -> object: ...
def fillet_faces(on_face_points: list[tuple[float, float, float]], radius: float) -> object: ...
def chamfer_edges(on_line_points: list[tuple[float, float, float]], distance: float, angle: float = 45.0) -> object: ...
def chamfer_faces(on_face_points: list[tuple[float, float, float]], distance: float, angle: float = 45.0) -> object: ...
```

### `extrude_cut` 修复提示

如果日志出现“草图选择失败”“无法拉伸”“无法切除”或 `extrude_cut` 失败，优先视为代码实现问题：

- 检查传入的 sketch 是否是刚创建的草图对象。
- 检查草图是否处于正确平面，并且轮廓闭合。
- 对齿轮标准件二次切除，优先使用已验证的封装流程：`insert_sketch_on_plane("XY")` -> `create_circle(...)` -> `extrude_cut(sketch, depth)`。
- 不要为了修复齿轮通孔而新增 `SelectByID2`、`InsertSketch2`、`sgear.sw_doc` 或 `sgear.sw_instance` 这类底层调用。
- 优先局部修复 `latest_code.py` 中草图创建和切除调用，不要重写建模思路。

## 参考几何

```python
def create_ref_plane(plane: object | str, offset_val: float, target_plane_name: str | None = None) -> object: ...
def create_axis(pt1: tuple[float, float, float], pt2: tuple[float, float, float], axis_name: str | None = None) -> object: ...
```

参考面偏移和参考轴端点都使用米。参考轴只需要表达方向，长度应接近零件尺寸或略小于零件包围盒；不要用 mm 数字直接作为米传入，否则会创建过长参考轴并影响截图反馈。

参考面和参考轴是装配阶段最稳定的接口载体。只有装配规划或用户要求会引用这些接口时，零件代码才应创建命名参考面和命名参考轴；独立单零件任务不要为了静态检查添加无用接口。

## 标准代码骨架

```python
from pysw import SldWorksApp, PartDoc

app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("DemoPart"))

# 建模步骤

sw_doc.save_as(model_file)
```
