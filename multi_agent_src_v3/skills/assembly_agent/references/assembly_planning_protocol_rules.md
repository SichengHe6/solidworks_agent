# 装配规划协议规则

该文档由 v2 `AssemblyPlanningAgent Knowledge Base` 归纳而来。用于把已补全的装配需求转换成可被零件建模和装配代码消费的 JSON。

## 核心目标

装配规划必须保证：

- 每个零件都能被独立建模。
- 每个接口都能被稳定引用。
- 装配关系能落到当前 SolidWorks 封装真实支持的能力上。

## 当前稳定装配关系

当前装配层稳定支持：

- 插入现有零件文件到装配。
- 平面与平面的重合/贴合。
- 轴与轴的同心。
- 保存装配文件。

规划 `constraints` 时优先表达为：

- `coincident` 或 `face_coincident`：平面重合 / 面贴合。
- `concentric` 或 `axis_coincident`：轴同心。
- `fix`：基准件固定。

## 接口规划

每个零件都应包含稳定接口。

### `faces`

每个面接口应包含：

- `name`
- `purpose`
- `normal_direction_relation`

命名示例：

- `mount_face_top`
- `base_face_bottom`
- `side_face_x_plus`
- `side_face_y_minus`

方向示例：

- `normal +Z`
- `normal -Z`
- `normal parallel to global Z`

### `axes`

每个轴接口应包含：

- `name`
- `purpose`
- `direction_relation`

命名示例：

- `main_axis_z`
- `hole_axis_1`
- `shaft_axis`

方向示例：

- `along local Z`
- `along global X`
- `from pt_a to pt_b`

### `points`

当前封装没有成熟的命名点装配 API。点位仍可用于表达参考轴两点、面/边选择近似定位和局部坐标含义。

## 零件拆分原则

- `parts` 表示唯一零件模板或唯一建模对象。
- `instances` 表示装配中实际出现的零件实例。
- 几何相同、建模方式相同的重复件必须优先合并成一个唯一 `part`。
- 外形相同但接口用途不同的实例，仍优先复用同一个 `part`，在 `part.interfaces` 中提供全部可能接口，并在 `instances[].interface_usage` 中说明每个实例实际使用哪些接口。
- 不要因为某个实例使用 `top_face`、另一个实例使用 `side_face` 就拆成两个零件，除非几何本体、孔位、厚度或特征尺寸已经不同。

## 必填规划信息

每个 `part` 应包含：

- `part_id`
- `name`
- `function`
- `shape`
- `key_dimensions`
- `material_or_notes`
- `quantity`
- `instance_ids`
- `interfaces`
- `assembly_relation_notes`
- `standalone_modeling_instructions`

每个 `instance` 应包含：

- `instance_id`
- `part_id`
- `name`
- `instance_role`
- `placement_notes`
- `interface_usage`

## 建模表达

`shape` 和 `standalone_modeling_instructions` 应贴近底层能力：

- “在 `XY` 面画中心矩形后单向拉伸”。
- “在 `ZY` 面画剖面并绕构造线旋转 360 度”。
- “在顶面草图切除通孔”。
- “创建偏移基准面用于第二特征”。
- “创建参考轴供装配同心配合使用”。

## 单位与坐标系

- 用户需求通常是 mm。
- 底层代码使用 m。
- `key_dimensions` 可保留 mm 表达，但应提示后续代码换算。
- `global_coordinate_system` 应服务装配配合，让关键安装面和主轴与全局 X/Y/Z 有明确关系。

## 工作区与输出路径

- 顶层 `workspace` 不应丢失外部传入路径。
- 每个零件 `workspace` 应保留自己的输出路径信息。
- `assembly_output` 必须保留最终装配文件路径。
