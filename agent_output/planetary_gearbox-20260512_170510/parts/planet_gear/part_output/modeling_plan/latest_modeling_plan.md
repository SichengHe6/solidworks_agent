# 行星轮 (Planet Gear) 建模思路

该零件为行星减速机构中的行星轮，将基于标准直齿轮模板进行参数化驱动建模，并添加中心安装孔特征。

## 1. 基础基准与坐标系
*   **原点**：位于齿轮几何中心。
*   **基准面**：
    *   `XY平面`：齿轮端面（底面），对应 `Z=0`。
    *   `XZ/ZY平面`：对称中心面。
*   **接口对齐**：确保 `front_face` 位于 `Z=0` 平面，符合装配体一键对齐要求。

## 2. 特征建模顺序
1.  **物化标准件**：从 `D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT` 复制并重命名为 `planet_gear.SLDPRT`。
2.  **参数驱动**：
    *   设置模数 `M = 2`。
    *   设置齿数 `Z = 18`。
    *   设置齿宽 `B = 10` (单位换算为 0.01m)。
    *   保持压力角 `Alpha = 20`，齿顶高系数 `Hax = 1`。
3.  **中心通孔（二次特征）**：
    *   在 `XY平面` 创建草图。
    *   绘制直径 `10mm` (0.01m) 的圆，圆心对齐原点。
    *   执行 `extrude_cut`，深度为 `10mm`，生成用于销轴配合的通孔。
4.  **接口创建**：
    *   创建参考轴 `rotation_axis`。
    *   创建参考面 `front_face`。

## 3. 关键接口命名
*   **轴接口**：`rotation_axis`（中心旋转轴，由原点指向 Z 正向）。
*   **面接口**：
    *   `front_face`：位于 `Z=0` 的端面。
    *   `back_face`：位于 `Z=0.01` 的端面。
    *   `bore_cylindrical_face`：中心孔内圆柱面。
*   **点接口**：`center_point`（位于原点）。

## 4. 保存目标
*   **文件路径**：`D:\a_src\python\sw_agent\agent_output\planetary_gearbox-20260512_170510\parts\planet_gear\part_output\code\planet_gear.SLDPRT`

## 5. 风险点与注意事项
*   **单位换算**：所有输入 mm 必须严格除以 1000 转换为米（例如 10mm -> 0.01m）。
*   **干涉预警**：由于 Z=18 且分布在 72mm 节圆上，齿顶圆间隙较小。必须确保 `Hax` 严格为 1，不要随意增大。
*   **草图平面**：标准件模板通常从 `Z=0` 向 `+Z` 方向拉伸，二次切除草图应选在 `XY` 平面以保证方向一致。
*   **接口稳定性**：确保 `rotation_axis` 命名准确，以便后续装配体通过 `SelectByID2` 引用。