# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 1. 启动与创建
app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("AdjustableArm"))

# 2. 参数定义 (单位: m)
arm_length = 0.120      # 120mm
arm_width = 0.025       # 25mm
arm_thickness = 0.015   # 15mm
base_hole_dia = 0.008   # 8mm
tip_ball_dia = 0.020    # 20mm
tip_ball_radius = tip_ball_dia / 2.0

print("Starting modeling of Adjustable Arm...")

# 3. 建模步骤

# --- 3.1 创建悬臂主体 ---
# 指令：在YZ平面绘制截面，沿X方向拉伸。
# 注意：SolidWorks API中，基准面名称可能区分大小写或需要特定格式。
# 常见基准面名称: "Front Plane" (XY), "Top Plane" (XZ), "Right Plane" (YZ).
# 但封装通常映射为 "XY", "XZ", "ZY" (注意是ZY不是YZ)。
# 根据KB: plane_name 仅限: "XY", "XZ", "ZY" 或自定义平面名。
# 所以这里应该使用 "ZY" 而不是 "YZ"。

print("Step 1: Creating Arm Body Sketch on ZY plane...")
sketch_body = sw_doc.insert_sketch_on_plane("ZY")

if sketch_body is None:
    raise Exception("Failed to create sketch on ZY plane")

# 绘制矩形截面
# 在ZY平面上，X是法线方向。草图坐标是(Y, Z)。
# center_x, center_y 对应草图平面的局部坐标。
# 对于ZY平面，局部X轴对应全局Y，局部Y轴对应全局Z？
# 或者封装内部处理了映射。我们按照封装要求传入 sketch_ref="ZY"。
# create_centre_rectangle(center_x, center_y, width, height, sketch_ref)
# 假设 center_x, center_y 是草图平面内的坐标。
# 我们要画一个宽 arm_width (Y方向), 高 arm_thickness (Z方向) 的矩形。
# 中心在 (0,0)。
sw_doc.create_centre_rectangle(
    center_x=0, 
    center_y=0, 
    width=arm_width, 
    height=arm_thickness, 
    sketch_ref="ZY"
)

# 退出草图以确保特征操作能正确选择草图
# 某些API需要在拉伸前结束草图编辑。如果 insert_sketch_on_plane 返回对象，
# 且 extrude 接受该对象，则通常不需要显式结束。
# 但如果失败，可能是因为草图仍处于编辑状态且未被正确选中。
# 尝试直接拉伸。

print("Step 2: Extruding Arm Body...")
try:
    # depth: 拉伸深度。ZY平面的法线是X轴。正向拉伸即+X方向。
    body_feature = sw_doc.extrude(sketch_body, depth=arm_length, single_direction=True, merge=True)
    print("Body extrusion successful.")
except Exception as e:
    print(f"Extrusion failed: {e}")
    raise e

# --- 3.2 创建基部轴孔 (Base Hole) ---
# 孔轴线沿Y方向，穿过基部中心 (0,0,0)。
# 策略：在 XZ 平面画圆，然后沿Y方向切除。
# XZ平面的法线是Y轴。
# 实体占据 Y: [-width/2, +width/2]。
# 我们在 XZ 平面 (Y=0) 画圆，然后双向切除或单向切除足够深度。
# 为了简单，使用单向切除，深度设为 arm_width，从 Y=0 向 +Y 切？
# 不，这样只切了一半。
# 更好的方法：创建一个偏移平面，例如 Y = -arm_width/2，然后向 +Y 切除 arm_width。

print("Step 3: Creating Base Hole...")
# 创建基准面用于孔切除起始位置
# create_workplane_p_d(plane, offset_val)
# plane可以是 "XY"/"XZ"/"ZY"
# 我们需要一个平行于 XZ 的平面，偏移 Y = -arm_width/2。
# XZ 平面的法线是 Y。所以偏移是在 Y 方向。
plane_hole_start = sw_doc.create_workplane_p_d("XZ", -arm_width / 2.0)
if plane_hole_start is None:
    raise Exception("Failed to create workplane for hole")

sketch_hole_cut = sw_doc.insert_sketch_on_plane(plane_hole_start)
if sketch_hole_cut is None:
    raise Exception("Failed to create sketch on hole plane")

# 圆心在局部坐标 (0,0)，对应全局 (X=0, Z=0)
# sketch_ref 应该与平面一致，即 "XZ"
sw_doc.create_circle(
    center_x=0, 
    center_y=0, 
    radius=base_hole_dia / 2.0, 
    sketch_ref="XZ" 
)

# 沿法线方向(+Y)切除，深度 arm_width
print("Cutting base hole...")
sw_doc.extrude_cut(sketch_hole_cut, depth=arm_width, single_direction=True)
print("Base hole cut successful.")

# --- 3.3 创建顶端球头 (Tip Ball) ---
# 球心位置：悬臂末端中心 (arm_length, 0, 0)
# 方法：旋转成型 (Revolve)
# 在 XY 平面画半圆轮廓 + 构造线轴。
# XY平面的法线是Z轴。
# 轮廓：右半圆，圆心 (arm_length, 0)，半径 tip_ball_radius。
# 旋转轴：过球心的垂直线 (平行于Y轴? 不，在XY平面内，Y是垂直方向)。
# 标准球体生成：画半圆，绕其直径旋转。
# 直径线：连接 (arm_length, -r) 和 (arm_length, r) 的线段 (平行于Y轴)。
# 旋转后生成球体。

print("Step 4: Creating Tip Ball Sketch on XY plane...")
sketch_ball = sw_doc.insert_sketch_on_plane("XY")
if sketch_ball is None:
    raise Exception("Failed to create sketch on XY plane for ball")

center_x_ball = arm_length
radius_ball = tip_ball_radius

# 绘制半圆弧 (右半圆)
# Start: (center_x, -r), End: (center_x, r), Mid: (center_x + r, 0)
sw_doc.create_3point_arc(
    start_x=center_x_ball, 
    start_y=-radius_ball, 
    end_x=center_x_ball, 
    end_y=radius_ball, 
    mid_x=center_x_ball + radius_ball, 
    mid_y=0, 
    sketch_ref="XY"
)

# 绘制旋转轴 (构造线)
# 轴是连接起点和终点的直线，即 X=center_x_ball 的竖线 (平行于Y轴)
sw_doc.create_construction_line(
    x1=center_x_ball, 
    y1=-radius_ball, 
    x2=center_x_ball, 
    y2=radius_ball, 
    sketch_ref="XY"
)

# 旋转生成球体
print("Revolving Tip Ball...")
ball_feature = sw_doc.revolve(sketch_ball, angle=360, merge=True)
print("Tip ball creation successful.")

# 4. 创建接口 (Interfaces)

# --- 4.1 面接口 ---
# base_side_face: 侧面，法线 +/- Y。
# 创建参考面：平行于 XZ 平面，偏移 Y = arm_width/2
print("Step 5: Creating Interface Planes...")
ref_plane_base_side_pos = sw_doc.create_ref_plane("XZ", arm_width / 2.0, target_plane_name="base_side_face")
print(f"Created reference plane: base_side_face at Y={arm_width/2.0}")

# --- 4.2 轴接口 ---

# arm_pitch_axis: 沿 local Y，穿过基部孔中心 (0,0,0)。
print("Step 6: Creating Interface Axes...")
axis_pitch = sw_doc.create_axis(
    pt1=(0, -0.01, 0), 
    pt2=(0, 0.01, 0), 
    axis_name="arm_pitch_axis"
)
print("Created axis: arm_pitch_axis")

# arm_longitudinal_axis: 沿几何长轴方向 (X轴)。
# 尽管接口描述说 "along local Z"，但几何是沿 X 拉伸的。
# 为了装配代理能正确识别方向，我们创建沿实际几何长轴的轴。
axis_long = sw_doc.create_axis(
    pt1=(0, 0, 0), 
    pt2=(arm_length, 0, 0), 
    axis_name="arm_longitudinal_axis"
)
print("Created axis: arm_longitudinal_axis")

# --- 4.3 点接口 ---
# ball_center_point: (arm_length, 0, 0)
# 记录日志
print(f"Interface Point 'ball_center_point' located at: ({arm_length}, 0, 0)")

# 5. 保存
output_path = r"D:\a_src\python\sw_agent\agent_output\iPhone17_5DOF_Stand_Assembly-20260424_171652\parts\adjustable_arm\adjustable_arm.SLDPRT"
print(f"Saving part to: {output_path}")
success = sw_doc.save_as(output_path)

if success:
    print("Modeling and saving completed successfully.")
else:
    print("Failed to save the part.")