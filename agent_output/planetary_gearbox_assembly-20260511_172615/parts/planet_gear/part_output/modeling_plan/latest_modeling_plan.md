## 行星轮（planet_gear）建模思路

该零件为行星齿轮减速机构中的关键传动部件，属于标准外齿轮。建模将采用“标准件物化+二次特征加工”的策略，以确保齿形精确并满足装配接口需求。

### 1. 特征顺序规划
1.  **物化标准件**：从标准件库 `D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT` 复制并重命名为 `planet_gear.SLDPRT` 到零件指定工作目录。
2.  **参数驱动配置**：
    *   通过修改全局变量设置模数 `M = 2mm`。
    *   设置齿数 `Z = 18`。
    *   设置齿宽 `B = 20mm`。
3.  **中心通孔切除**：在齿轮基准面（XY平面）绘制直径 10mm 的圆，执行拉伸切除以生成销轴安装孔。
4.  **参考几何体构建**：
    *   创建贯穿中心的基准轴。
    *   创建位于齿宽中点的基准面。

### 2. 关键草图与基准
*   **草图（中心孔）**：位于 `XY` 平面，以原点为中心，半径 `0.005m` (10mm直径)。
*   **基准面（mid_plane）**：基于 `XY` 平面偏移 `0.01m`（齿宽 20mm 的一半）。该面作为装配时的轴向对齐基准，确保所有齿轮中点对齐于全局 XY 平面。
*   **基准轴（rotation_axis）**：定义为从 `(0,0,0)` 到 `(0,0,0.02)` 的轴，用于行星轮绕行星架销轴的旋转约束。

### 3. 接口命名
*   **rotation_axis** (Axis)：中心旋转轴，供装配体调用进行同轴约束。
*   **mid_plane** (Plane)：零件轴向中面，供装配体调用进行重合约束。
*   **bore_cylindrical_face** (Face)：中心孔内圆柱面，作为销轴配合的辅助参考。

### 4. 保存目标
*   **目标路径**：`D:\a_src\python\sw_agent\agent_output\planetary_gearbox_assembly-20260511_172615\parts\planet_gear\part_output\code\planet_gear.SLDPRT`

### 5. 风险点说明
*   **单位一致性**：API 强制使用 **米 (m)**。建模时必须将 mm 尺寸（如 2mm, 20mm）转换为 0.002m, 0.02m。
*   **标准件保护**：严禁直接修改 `standard_swpart` 目录下的源文件，必须执行 `copy_standard_part_to_workdir_and_open`。
*   **中面对齐精度**：由于装配规则要求“所有零件轴向中点对齐”，`mid_plane` 的偏移量必须严格等于 `B / 2`。
*   **切除稳定性**：在创建草图实体后，应显式调用 `InsertSketch(True)` 退出草图模式，以确保 `extrude_cut` 能正确识别并选中草图对象。