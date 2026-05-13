# 装配 API 参考

该文档由 v2 `AssemblyAgent Knowledge Base` 归纳而来。用于装配代码生成和局部修复。

## 应用与装配文档

```python
from pysw import SldWorksApp, AssemDoc

sw_app = SldWorksApp()
sw_assem = AssemDoc(sw_app.createAndActivate_sw_assembly(assem_name))
```

可用能力：

```python
def createAndActivate_sw_assembly(assem_name: str): ...
def get_assembly_path(workdir: str, assem_name: str): ...
```

## 插入零件

```python
def add_component(file_path: str, x: float, y: float, z: float): ...
```

`add_component(...)` 返回的是装配中的组件名。后续配合必须使用返回的组件名，不要使用原始文件名或零件名字符串。

## 配合

```python
def mate_faces(assem_name, comp1, comp2, plane_name1, plane_name2, aligned=True): ...
def mate_axes(assem_name, comp1, comp2, axis_name1, axis_name2, aligned=True): ...
```

当前最稳定的装配引用对象是：

- 组件名 `comp_name`
- 组件内部的命名参考面
- 组件内部的命名参考轴

不要假设可以临时通过几何识别自动找到正确面或轴。

## 保存

```python
def save_as(path: str): ...
```

装配代码必须保存到 `assembly.assembly_output.model_file` 或固定工作区下的等价目标路径。

## 代码结构

推荐结构：

1. 导入封装。
2. 读取装配规划、实例列表和路径。
3. 创建装配文档。
4. 插入零件并缓存 `part_id -> model_file`、`instance_id -> comp_name`。
5. 按 `assembly_sequence` 和 `constraints` 执行配合。
6. 保存装配。
7. 对关键失败点做判空和日志输出。

## 日志要求

建议至少打印：

- 装配开始。
- 每个零件导入成功/失败。
- 每条约束执行情况。
- 最终保存路径。
