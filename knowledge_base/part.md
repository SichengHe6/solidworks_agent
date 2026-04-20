# 文档说明：此文档是RV减速器零件的参考示例，展示了如何使用 PySolidWorks API 生成复杂的 CAD 模型。请严格遵守核心系统准则，所有均布特征必须通过 Python 循环和数学计算实现。此文档仅供参考，实际开发中请根据具体零件需求进行调整。

## 1. RV减速器的行星架

这是一个非常经典的精密机械零件——**RV减速器的行星架（Planet Carrier）**。

核心拓扑特征：

1.  **基础盘体**：带有中心通孔（容纳太阳轮或输入轴）。
2.  **曲柄孔（大孔）**：3个呈120度均布的大孔，用于安装曲柄轴，且正面带有沉头/台阶特征。
3.  **销柱/螺栓孔簇（小孔群）**：错开大孔60度分布，每组包含多个小孔，用于固定行星架的另一半或输出盘。
4.  **背面减重槽（异形凹坑）**：背面为了减重和避让，铣削出了复杂的凹槽，留下了外围的加强圈（Rim）和曲柄孔周围的凸台（Boss）。

由于 PySolidWorks 基础 API 难以直接生成由复杂样条曲线构成的异形 CNC 铣削槽，将**使用纯数学极坐标循环**，并通过**多圆叠加切除**的方式，在现有 API 边界内完美逼近该零件的拓扑结构和物理功能。

### 零件建模路径推演

\<think\>

1.  空间坐标系规划：以 XY 面为基准面，Z 轴向上生长。底面 Z=0，顶面 Z=0.02 (20mm)。
2.  基体成型：在 XY 面绘制外径 R=0.1，内径 R=0.02 的同心圆，拉伸厚度 0.02，得到基础圆盘。
3.  大曲柄孔与沉头：
      - 在顶面 (Z=0.02) 绘制 3 个 R=0.025 的圆 (PCD=0.05)，深度 -0.02 切穿。
      - 再次在顶面绘制 3 个 R=0.028 的圆，深度 -0.005 切除，形成沉头台阶。
4.  小孔簇：在顶面，极角偏移 60 度，PCD=0.07 处，使用双层循环绘制 3 组孔（每组1个中心孔+3个卫星孔），全部切穿 (-0.02)。
5.  背面减重槽近似：在底面 (XY 面，Z=0) 绘制 3 个较大的圆 (R=0.025, PCD=0.065)。向 Z 轴正方向 (+0.01) 进行切除。这样既能挖出减重槽，又能完美保留外围圆环边缘和曲柄孔周围的加强凸台，实现与原图高度一致的拓扑效果。
    \</think\>

### PySolidWorks 建模代码

```python
import math
from pysolidworks import PartDoc, SldWorksApp

# 初始化应用与文档

app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("RV_Planet_Carrier"))

# \==========================================

# 1\. 基础圆盘基体成型 (Z: 0 -\> 0.02)

# \==========================================

s_base = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_circle(0, 0, 0.1, "XY")    # 外边缘 R=100mm
sw_doc.create_circle(0, 0, 0.02, "XY")   # 中心太阳轮孔 R=20mm
sw_doc.extrude(s_base, 0.02, single_direction=True)

# 创建顶面基准面用于后续加工

plane_top = sw_doc.create_workplane_p_d("XY", 0.02)

# \==========================================

# 2\. 3个曲柄轴大孔 (贯通切除)

# \==========================================

s_crank_holes = sw_doc.insert_sketch_on_plane(plane_top)
pcd_crank = 0.05
for i in range(3):
    angle = math.radians(i * 120)
    cx = pcd_crank * math.cos(angle)
    cy = pcd_crank * math.sin(angle)
    sw_doc.create_circle(cx, cy, 0.025, "XY")
sw_doc.extrude_cut(s_crank_holes, -0.02, single_direction=True)

# \==========================================

# 3\. 曲柄轴大孔正面的沉头台阶 (浅切除)

# \==========================================

s_counterbore = sw_doc.insert_sketch_on_plane(plane_top)
for i in range(3):
    angle = math.radians(i * 120)
    cx = pcd_crank * math.cos(angle)
    cy = pcd_crank * math.sin(angle)
    sw_doc.create_circle(cx, cy, 0.028, "XY") # 半径稍大
sw_doc.extrude_cut(s_counterbore, -0.005, single_direction=True) # 切深 5mm

# \==========================================

# 4\. 销柱/螺栓小孔簇 (交错 60 度，贯通切除)

# \==========================================

s_pin_holes = sw_doc.insert_sketch_on_plane(plane_top)
pcd_pin_group = 0.07
for i in range(3):
# 组中心角度：60, 180, 300
    group_angle = math.radians(i * 120 + 60)
    gx = pcd_pin_group * math.cos(group_angle)
    gy = pcd_pin_group * math.sin(group_angle)


    # 绘制组内中心孔
    sw_doc.create_circle(gx, gy, 0.004, "XY")

    # 绘制组内周围的 3 个卫星小孔
    for j in range(3):
        local_angle = group_angle + math.radians(j * 120)
        px = gx + 0.01 * math.cos(local_angle)
        py = gy + 0.01 * math.sin(local_angle)
        sw_doc.create_circle(px, py, 0.003, "XY")


sw_doc.extrude_cut(s_pin_holes, -0.02, single_direction=True)

# \==========================================

# 5\. 背面减重槽 (在底面 XY 面向上切除)

# 用相交圆规避复杂样条曲线，完美保留外缘和曲柄凸台

# \==========================================

s_pockets = sw_doc.insert_sketch_on_plane("XY")
pcd_pocket = 0.065
for i in range(3):
    angle = math.radians(i * 120 + 60) # 槽的位置与小孔簇对齐
    cx = pcd_pocket * math.cos(angle)
    cy = pcd_pocket * math.sin(angle)
    # R=0.028 会刚好切到离外缘 7mm 的位置留下 Rim，且避开曲柄孔留下 Boss
    sw_doc.create_circle(cx, cy, 0.028, "XY")

# 向 Z 轴正方向（零件内部）切削 10mm

sw_doc.extrude_cut(s_pockets, 0.01, single_direction=True)

# \==========================================

# 6\. 后处理修饰 (倒角去应力)

# \==========================================

# 对顶面外围进行倒角 (推演安全坐标落在顶面外环)

sw_doc.chamfer_faces([(0.09, 0, 0.02)], 0.001)
```

## 2. 摆线轮
### 核心特征
1. **摆线齿廓**：由摆线曲线定义的复杂齿形，无法通过简单的圆弧或样条直接生成。
2. **中心孔**：用于安装在输入轴上，通常带有键槽

```python
import math
from pysolidworks import PartDoc, SldWorksApp

# [推理] 目标：利用原生方程式曲线 API 生成绝对平滑的 RV 摆线轮廓。
# 考点 1 (常数静态化)：CAD 的方程解析器对复杂变量支持有限。必须提前在 Python 中将 A, R_z, K 等参数计算为绝对数值常量，再注入到方程字符串中。
# 考点 2 (规避闭合限制)：针对 API "不能创造闭合曲线" 的硬性限制，将 0 到 2*pi 的全周期拆分为 [0, pi] 和 [pi, 2*pi] 两段曲线，实现完美无缝对接闭合。
# 考点 3 (原生数学语法)：SolidWorks 方程识别 "pi" 常数，求幂使用 "^"，平方根使用 "^0.5"。


app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("Equation_Cycloidal_Gear"))
s_gear = sw_doc.insert_sketch_on_plane("XY")
# ==========================================
# 1. 物理参数推演与静态化
# ==========================================
# Z_b = 11, R_z = 0.04, A = 0.003, R_rp = 0.002
# 计算短幅系数 K = A * Z_b / R_z = 0.825
# 计算统一分母内部常数: C1 = 1 + K^2 = 1.680625, C2 = 2 * K = 1.65

# 将解析几何公式转换为 CAD 字符串 (代入静态算出的常数)
# 分母 S = (1.680625 - 1.65*cos(11*t))^0.5
eq_x = "0.04*cos(t) - 0.003*cos(12*t) - 0.002*(cos(t) - 0.825*cos(12*t)) / ((1.680625 - 1.65*cos(11*t))^0.5)"
eq_y = "0.04*sin(t) - 0.003*sin(12*t) - 0.002*(sin(t) - 0.825*sin(12*t)) / ((1.680625 - 1.65*cos(11*t))^0.5)"
# ==========================================
# 2. 核心突破：分段生成方程式曲线
# ==========================================
# 第一段：上半区 [0, pi]
sw_doc.create_equation_spline_t(eq_x, eq_y, "0", "pi", "XY")

# 第二段：下半区 [pi, 2*pi]
sw_doc.create_equation_spline_t(eq_x, eq_y, "pi", "2*pi", "XY")
# ==========================================
# 3. 嵌套标准内部特征
# ==========================================
sw_doc.create_circle(0, 0, 0.008, "XY")

R_pcd = 0.022
for i in range(6):
    a = (2 * math.pi / 6) * i
    sw_doc.create_circle(R_pcd * math.cos(a), R_pcd * math.sin(a), 0.006, "XY")
align_x = 0.033 * math.cos(-math.pi / 4)
align_y = 0.033 * math.sin(-math.pi / 4)
sw_doc.create_circle(align_x, align_y, 0.0015, "XY")
# 单次整体拉伸
sw_doc.extrude(s_gear, 0.005)
print("方程式摆线齿轮模型生成成功")
```

## 3. 曲柄轴承
 ```python

import sys
import math

# 假设您的库在路径中
try:
    from pysolidworks import SldWorksApp, PartDoc
except ImportError:
    pass

# 全局常量
MM = 0.001

def create_trapezoid_cut_front(sw_part, z_pos, r_shaft):
    """ 创建前端梯形槽 """
    print(f"--- 创建前端梯形槽 (Z:{z_pos*1000:.1f}mm) ---")
    sketch = sw_part.insert_sketch_on_plane("XZ")
    depth = 0.26 * MM; width_surface = 3.0 * MM; width_bottom = 2.48 * MM
    p1 = (r_shaft, z_pos); p2 = (r_shaft - depth, z_pos)
    p3 = (r_shaft - depth, z_pos + width_bottom); p4 = (r_shaft, z_pos + width_surface)
    sw_part.create_lines([p1, p2, p3, p4, p1], "XZ")
    sw_part.create_construction_line(0, z_pos - 0.01, 0, z_pos + 0.02, "XZ")
    sw_part.revolve_cut(sketch, 360)

def create_trapezoid_cut_rear(sw_part, z_pos, r_shaft):
    """ 创建后端梯形槽 """
    print(f"--- 创建后端梯形槽 (Z:{z_pos*1000:.1f}mm) ---")
    sketch = sw_part.insert_sketch_on_plane("XZ")
    depth = 0.26 * MM; width_surface = 3.0 * MM; width_bottom = 2.48 * MM
    p1 = (r_shaft, z_pos); p2 = (r_shaft - depth, z_pos)
    p3 = (r_shaft - depth, z_pos - width_bottom); p4 = (r_shaft, z_pos - width_surface)
    sw_part.create_lines([p1, p2, p3, p4, p1], "XZ")
    sw_part.create_construction_line(0, z_pos + 0.01, 0, z_pos - 0.02, "XZ")
    sw_part.revolve_cut(sketch, 360)

def create_middle_groove(sw_part, z_center):
    """ 创建中间 U 型槽 """
    print(f"--- 创建中间回转切槽 (Z中心:{z_center*1000:.1f}mm) ---")
    sketch = sw_part.insert_sketch_on_plane("XZ")
    
    groove_width = 2.92 * MM
    half_w = groove_width / 2.0
    r_outer = 27.85 * MM; r_inner_straight = 24.25 * MM; r_arc_mid = 22.80 * MM
    z_top = z_center - half_w; z_bot = z_center + half_w 
    
    p1 = (r_outer, z_top); p2 = (r_inner_straight, z_top)
    p3 = (r_inner_straight, z_bot); p4 = (r_outer, z_bot)
    p_mid_arc = (r_arc_mid, z_center)
    
    sw_part.create_lines([p1, p2], "XZ")
    sw_part.create_lines([p3, p4], "XZ")
    sw_part.create_lines([p4, p1], "XZ")
    sw_part.create_3point_arc(p2[0], p2[1], p3[0], p3[1], p_mid_arc[0], p_mid_arc[1], "XZ")
    sw_part.create_construction_line(0, z_center - 0.01, 0, z_center + 0.01, "XZ")
    sw_part.revolve_cut(sketch, 360)

def create_roller_bearing(sw_part, center_x, center_y, z_start, shaft_dia, bearing_width):
    """
    更新后的轴承生成逻辑：
    1. 滚子居中 (Z轴方向不贯穿)
    2. 滚子长度为架子宽度的 4/5
    3. XY坐标严格对齐分度圆
    """
    print(f"--- 生成轴承 @ Z:{z_start*1000:.1f}, Center({center_x*1000:.1f}, {center_y*1000:.1f}) ---")
    
    # --- 参数计算 ---
    bearing_od = shaft_dia + 16 * MM  # 外径
    bearing_id = shaft_dia              # 内径
    roller_dia = 10 * MM               # 滚子直径
    num_rollers = 14                    # 滚子数量
    
    # 关键修改 1: 滚子长度为架子宽度的 80% (4/5)
    roller_len = bearing_width * 0.8
    
    # 关键修改 2: 计算 Z 轴居中偏移量
    # 偏移量 = (总宽 - 滚子长) / 2
    z_center_offset = (bearing_width - roller_len) / 2.0
    z_roller_start = z_start + z_center_offset  # 滚子的起始高度
    
    # 关键修改 3: 分度圆半径 (内外径平均值的一半，即直径和的四分之一)
    pitch_radius = (bearing_od + bearing_id) / 4

    # --- 1. 建立轴承基体 (保持架主体) ---
    # 在 z_start 建立平面
    plane_base = sw_part.create_workplane_p_d("XY", z_start)
    s1 = sw_part.insert_sketch_on_plane(plane_base)
    # sw_part.create_circle(center_x, center_y, bearing_od/2, "XY")
    sw_part.create_circle(center_x, center_y, bearing_od/2, "XY")
    base = sw_part.extrude(s1, bearing_width, True, False) # 实体

    # --- 2. 切内孔 ---
    s2 = sw_part.insert_sketch_on_plane(plane_base)
    sw_part.create_circle(center_x, center_y, bearing_id/2+5*MM, "XY")
    hole = sw_part.extrude(s2, bearing_width, True, False) # 实体
    ring = sw_part.boolean_sub(base, hole)

    # --- 3. 保持架内部掏空 (Shell) ---
    # 为了让滚子能转动，通常中间大部分是空的，只留上下边缘
    rim_thickness = 2.0 * MM
    shell_z = z_start + rim_thickness
    shell_width = bearing_width - (2 * rim_thickness)
    
    if shell_width > 0:
        plane_shell = sw_part.create_workplane_p_d("XY", shell_z)
        s3 = sw_part.insert_sketch_on_plane(plane_shell)
        # 切除范围：从内孔切到接近外边缘
        sw_part.create_circle(center_x, center_y, bearing_od/2 - 1.5*MM, "XY")
        roller_spadce = sw_part.extrude(s3, shell_width, True, False)
        shell = sw_part.boolean_sub(ring, roller_spadce)

    # --- 4. 滚子位置处理 (挖槽 + 生成实体) ---
    # 我们需要在 z_roller_start 的高度进行操作，确保居中
    
    plane_roller = sw_part.create_workplane_p_d("XY", z_roller_start)
    
    # A. 挖滚子槽 (Pocket) - 可选，如果希望保持架上有对应的孔
    # 这里我们挖一个比滚子稍微大一点点的槽，长度也一致，让滚子嵌进去
    s_cut = sw_part.insert_sketch_on_plane(plane_roller)
    for i in range(num_rollers):
        angle = 2 * math.pi * i / num_rollers
        # 严格的 XY 坐标计算
        cx = center_x + (bearing_id+roller_dia)/2 * math.cos(angle)
        cy = center_y + (bearing_id+roller_dia)/2 * math.sin(angle)
        # 挖稍微大一点的孔 (间隙 0.2mm)
        sw_part.create_circle(cx, cy, (roller_dia/2) + 0.1*MM, "XY")
    
    # 这里的深度设为滚子长度，这样上下就留有了 z_center_offset 的实体材料，不会贯穿
    sw_part.extrude_cut(s_cut, roller_len, True)

    # B. 生成滚子实体
    s_roller = sw_part.insert_sketch_on_plane(plane_roller)
    for i in range(num_rollers):
        angle = 2 * math.pi * i / num_rollers
        cx = center_x + (bearing_id+roller_dia)/2 * math.cos(angle)
        cy = center_y + (bearing_id+roller_dia)/2 * math.sin(angle)
        sw_part.create_circle(cx, cy, roller_dia/2, "XY")
        
    # 拉伸滚子，merge=True 与主体合并(演示用)，实际工程中可能设为 False
    sw_part.extrude(s_roller, roller_len, True, False)

def main():
    # --- 1. 尺寸定义 ---
    dia_main = 35.0 * MM
    dia_ecc = 52.5 * MM
    
    len_rear = 26 * MM
    len_flange_pos = 26 * MM
    len_mid_pos = 26 * MM
    len_front = 50.2 * MM
    
    len_ecc_body = 26.0 * MM
    eccentricity = 1.6 * MM
    dia_thru_hole = 6.0 * MM
    
    # Z轴关键节点
    z_junction_rear = len_rear                                      # Z=26
    z_junction_mid = len_rear + len_flange_pos                      # Z=52
    z_junction_front = len_rear + len_flange_pos + len_mid_pos      # Z=78
    total_len = z_junction_front + len_front                        # Z=128.2
    
    groove_half_width = 1.46 * MM
    
    # --- 2. 启动 ---
    app = SldWorksApp()
    sw_part = PartDoc(app.createAndActivate_sw_part("Crank_With_Bearings_Updated"))
    
    print("=== 开始建模 (带居中滚子版) ===")

    # --- 3. 实体生成 ---
    print(">>> 生成主轴与偏心体")
    s1 = sw_part.insert_sketch_on_plane("XY")
    sw_part.create_circle(0, 0, dia_main/2, "XY")
    sw_part.extrude(s1, total_len, True, True) 
    
    p2 = sw_part.create_workplane_p_d("XY", z_junction_rear)
    s2 = sw_part.insert_sketch_on_plane(p2)
    sw_part.create_circle(eccentricity, 0, dia_ecc/2, "XY")
    sw_part.extrude(s2, len_ecc_body, True, True)
    
    p3 = sw_part.create_workplane_p_d("XY", z_junction_mid)
    s3 = sw_part.insert_sketch_on_plane(p3)
    sw_part.create_circle(-eccentricity, 0, dia_ecc/2, "XY")
    sw_part.extrude(s3, len_ecc_body, True, True)

    # ==========================================
    # Step 4: 倒角 (1mm)
    # ==========================================
    chamfer_points_1mm = [
        (dia_main/2, 0, 0),
        (dia_main/2, 0, total_len),
        (eccentricity + dia_ecc/2, 0, z_junction_rear),
        (-eccentricity - dia_ecc/2, 0, z_junction_front)
    ]
    sw_part.chamfer_edges(chamfer_points_1mm, 1.0 * MM, 45.0)

    # ==========================================
    # Step 5: 切除中间 U 型槽
    # ==========================================
    create_middle_groove(sw_part, z_center=z_junction_mid)

    # ==========================================
    # Step 6: 倒角 (0.5mm)
    # ==========================================
    z_groove_top_edge = z_junction_mid - groove_half_width 
    z_groove_bot_edge = z_junction_mid + groove_half_width 
    
    chamfer_points_05mm = [
        (eccentricity, dia_ecc/2, z_groove_top_edge),
        (-eccentricity, dia_ecc/2, z_groove_bot_edge)
    ]
    sw_part.chamfer_edges(chamfer_points_05mm, 0.5 * MM, 45.0)

    # ==========================================
    # Step 7: 生成轴承 (应用新逻辑)
    # ==========================================
    print(">>> 生成偏心轴承")
    
    # 轴承宽度设为 20mm
    bearing_width = 26.0 * MM
    offset_z = (len_ecc_body - bearing_width) / 2.0
    
    # 轴承 1: 位于后段偏心轴 (Z=26起, X偏心=1.6)
    create_roller_bearing(
        sw_part, 
        center_x=eccentricity, 
        center_y=0, 
        z_start=z_junction_rear + offset_z, 
        shaft_dia=dia_ecc, 
        bearing_width=bearing_width
    )
    
    # 轴承 2: 位于前段偏心轴 (Z=52起, X偏心=-1.6)
    create_roller_bearing(
        sw_part, 
        center_x=-eccentricity, 
        center_y=0, 
        z_start=z_junction_mid + offset_z, 
        shaft_dia=dia_ecc, 
        bearing_width=bearing_width
    )

    # ==========================================
    # Step 8: 切除梯形槽
    # ==========================================
    create_trapezoid_cut_rear(sw_part, z_junction_rear, dia_main/2)
    create_trapezoid_cut_front(sw_part, z_junction_front, dia_main/2)
    
    # Step 9: 通孔
    s_hole = sw_part.insert_sketch_on_plane("XY")
    sw_part.create_circle(0, 0, dia_thru_hole/2, "XY")
    sw_part.extrude_cut(s_hole, total_len * 1.05, True)

    print("\n=== 建模完成 ===")

if __name__ == "__main__":
    main()
```