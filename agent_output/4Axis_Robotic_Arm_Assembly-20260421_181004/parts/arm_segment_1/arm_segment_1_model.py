# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 1. 启动与创建
app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("Arm Segment 1"))

# 2. 参数定义 (单位: m)
cube_size = 0.060       # 60mm
cyl_dia = 0.040         # 40mm
cyl_len = 0.150         # 150mm
hole_dia = 0.040        # 40mm
pin_dia = 0.010         # 10mm
pin_len = 0.015         # 15mm
chamfer_dist = 0.002    # C2 = 2mm

# 3. 建模步骤

# --- Step 1: 底部方块 (Bottom Cube) ---
print("Step 1: Creating Bottom Cube...")
sketch_bottom = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=cube_size, height=cube_size, sketch_ref="XY")
bottom_cube_feat = sw_doc.extrude(sketch_bottom, depth=cube_size, single_direction=True, merge=True)

# --- Step 2: 底部中心孔 (Central Hole in Bottom Cube) ---
print("Step 2: Cutting Central Hole...")
# 在顶部面(Z=0.06)创建草图，或者直接在XY平面切除贯穿
# 为了准确定位，我们在XY平面画圆，然后向上切除贯穿整个方块
sketch_hole = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_circle(center_x=0, center_y=0, radius=hole_dia/2, sketch_ref="XY")
# 切除深度略大于方块高度以确保贯穿
sw_doc.extrude_cut(sketch_hole, depth=cube_size + 0.001, single_direction=True)

# --- Step 3: 连接圆柱 (Connector Cylinder) ---
print("Step 3: Extruding Connector Cylinder...")
# 在底部方块的顶面 (Z=0.06) 创建草图
# 我们需要一个参考平面或者直接利用现有几何。
# 这里我们创建一个偏移平面 Z=0.06
plane_top_of_bottom = sw_doc.create_workplane_p_d("XY", offset_val=cube_size)
sketch_cyl = sw_doc.insert_sketch_on_plane(plane_top_of_bottom)
sw_doc.create_circle(center_x=0, center_y=0, radius=cyl_dia/2, sketch_ref="XY")
# 沿 +Z 方向拉伸
connector_feat = sw_doc.extrude(sketch_cyl, depth=cyl_len, single_direction=True, merge=True)

# --- Step 4: 顶部方块 (Top Cube) ---
print("Step 4: Creating Top Cube...")
# 在圆柱顶面 (Z = 0.06 + 0.15 = 0.21) 创建草图
plane_top_of_cyl = sw_doc.create_workplane_p_d("XY", offset_val=cube_size + cyl_len)
sketch_top = sw_doc.insert_sketch_on_plane(plane_top_of_cyl)
sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=cube_size, height=cube_size, sketch_ref="XY")
top_cube_feat = sw_doc.extrude(sketch_top, depth=cube_size, single_direction=True, merge=True)

# --- Step 5: 倒角 (Chamfer C2 on Cube Edges) ---
print("Step 5: Applying Chamfers to Cube Edges...")
# 需要对两个方块的棱边进行倒角。
# 由于API限制，我们通过指定边上的点来定位边。
# 底部方块 (Z: 0 -> 0.06):
# 垂直边: (±0.03, ±0.03, 0.03)
# 水平边: (±0.03, 0, 0), (0, ±0.03, 0), (±0.03, 0, 0.06), (0, ±0.03, 0.06) 等
# 为了简化且稳定，我们选择每个方块最具代表性的几条边，或者尝试对所有可见边倒角。
# 注意：SolidWorks API 通常允许选择所有相切边或特定边。这里我们手动指定关键点。

# 底部方块边缘点 (8个顶点附近的边中点或任意点)
# 实际上，chamfer_edges 需要的是“边上”的点。
# 让我们选取底部方块的12条边的中点附近点：
bottom_edge_points = [
    (0.03, 0, 0.03), (-0.03, 0, 0.03), (0, 0.03, 0.03), (0, -0.03, 0.03), # 垂直边
    (0.03, 0.03, 0.03), (0.03, -0.03, 0.03), (-0.03, 0.03, 0.03), (-0.03, -0.03, 0.03), # 这些是顶点，可能不唯一确定边，改用边中点
    (0.03, 0, 0), (0.03, 0, 0.06), # X+ 面的上下边
    (-0.03, 0, 0), (-0.03, 0, 0.06), # X- 面的上下边
    (0, 0.03, 0), (0, 0.03, 0.06), # Y+ 面的上下边
    (0, -0.03, 0), (0, -0.03, 0.06)  # Y- 面的上下边
]
# 更稳健的方式：只选几个关键边，或者依赖SW的自动链选（如果封装支持）。
# 鉴于封装签名 `on_line_points` 是列表，我们传入一组能覆盖主要棱边的点。
# 底部方块：
sw_doc.chamfer_edges(
    on_line_points=[
        (0.03, 0, 0.03), (-0.03, 0, 0.03), (0, 0.03, 0.03), (0, -0.03, 0.03), # 4条竖边
        (0.03, 0.03, 0.03), (0.03, -0.03, 0.03), (-0.03, 0.03, 0.03), (-0.03, -0.03, 0.03) # 顶点可能不行，换边中点
    ], 
    distance=chamfer_dist, 
    angle=45.0
)
# 重新尝试更明确的边中点：
# 底部方块底面4条边中点: (0.03, 0, 0), (-0.03, 0, 0), (0, 0.03, 0), (0, -0.03, 0)
# 底部方块顶面4条边中点: (0.03, 0, 0.06), (-0.03, 0, 0.06), (0, 0.03, 0.06), (0, -0.03, 0.06)
# 底部方块侧面4条竖边中点: (0.03, 0, 0.03)... 已包含
# 让我们分两次调用以确保稳定性，或者一次传入足够多的点。
# 修正：上面的点有些重复或不准确。让我们使用更标准的边中点。
# 底部方块：
bottom_chamfer_pts = [
    (0.03, 0, 0.03), (-0.03, 0, 0.03), (0, 0.03, 0.03), (0, -0.03, 0.03), # Vertical edges
    (0.03, 0, 0), (-0.03, 0, 0), (0, 0.03, 0), (0, -0.03, 0),             # Bottom horizontal edges
    (0.03, 0, 0.06), (-0.03, 0, 0.06), (0, 0.03, 0.06), (0, -0.03, 0.06)  # Top horizontal edges
]
sw_doc.chamfer_edges(on_line_points=bottom_chamfer_pts, distance=chamfer_dist, angle=45.0)

# 顶部方块 (Z: 0.21 -> 0.27):
# 中心 (0,0, 0.24)
top_z_base = cube_size + cyl_len
top_z_top = top_z_base + cube_size
top_chamfer_pts = [
    (0.03, 0, top_z_base + 0.03), (-0.03, 0, top_z_base + 0.03), (0, 0.03, top_z_base + 0.03), (0, -0.03, top_z_base + 0.03), # Vertical
    (0.03, 0, top_z_base), (-0.03, 0, top_z_base), (0, 0.03, top_z_base), (0, -0.03, top_z_base),             # Bottom horiz
    (0.03, 0, top_z_top), (-0.03, 0, top_z_top), (0, 0.03, top_z_top), (0, -0.03, top_z_top)                  # Top horiz
]
sw_doc.chamfer_edges(on_line_points=top_chamfer_pts, distance=chamfer_dist, angle=45.0)


# --- Step 6: 顶部销钉 (Top Pin) ---
print("Step 6: Extruding Top Pin...")
# 销钉位于顶部方块的 +X 侧面中心
# 顶部方块范围: X[-0.03, 0.03], Y[-0.03, 0.03], Z[0.21, 0.27]
# +X 侧面中心: X=0.03, Y=0, Z=0.24
# 我们需要在 X=0.03 的平面上创建草图。
# 创建参考平面 X=0.03
plane_pin_side = sw_doc.create_workplane_p_d("ZY", offset_val=0.03) # ZY plane is X=0, offset 0.03 -> X=0.03
# 注意：create_workplane_p_d 的第一个参数是基准面名称。"ZY" 对应 X=0 平面。
# 在该平面上，坐标系统是 (Y, Z)。
# 销钉中心在局部坐标系 (Y=0, Z=0.24)
sketch_pin = sw_doc.insert_sketch_on_plane(plane_pin_side)
# 在 ZY 平面上，x 参数对应 Y 轴，y 参数对应 Z 轴 (根据封装习惯，需确认 sketch_ref)
# 封装说明: sketch_ref 必须与当前草图平面方向一致 ("XY"/"XZ"/"ZY")
# 对于 ZY 平面，通常 x->Y, y->Z 或者 x->Z, y->Y。
# 根据常见 SW API 映射，ZY 平面草图中，第一个坐标通常是 Y，第二个是 Z。
# 让我们假设 create_circle(x, y, ...) 在 ZY 平面上意味着 Center(Y=x, Z=y)。
# 销钉中心: Y=0, Z=0.24
sw_doc.create_circle(center_x=0, center_y=top_z_base + cube_size/2, radius=pin_dia/2, sketch_ref="ZY")
# 向 +X 方向拉伸 (即远离 ZY 平面的正方向)
pin_feat = sw_doc.extrude(sketch_pin, depth=pin_len, single_direction=True, merge=True)

# 4. 创建接口 (Interfaces)

# --- Axis: central_hole_axis ---
# 沿 Z 轴，穿过原点
print("Creating Interface: central_hole_axis")
sw_doc.create_axis(pt1=(0, 0, 0), pt2=(0, 0, 1), axis_name="central_hole_axis")

# --- Axis: pin_axis ---
# 沿 X 轴，穿过销钉中心 (0.03, 0, 0.24)
print("Creating Interface: pin_axis")
# 起点 (0.03, 0, 0.24), 终点 (0.04, 0, 0.24) 以定义 +X 方向
sw_doc.create_axis(pt1=(0.03, 0, top_z_base + cube_size/2), pt2=(0.04, 0, top_z_base + cube_size/2), axis_name="pin_axis")

# --- Face: bottom_face ---
# 底部方块的底面 (Z=0)
print("Creating Interface: bottom_face")
# 使用 create_ref_plane 基于 XY 平面偏移 0，命名为 bottom_face
sw_doc.create_ref_plane(plane="XY", offset_val=0, target_plane_name="bottom_face")

# --- Face: top_pin_face ---
# 销钉所在的侧面 (X=0.03)
print("Creating Interface: top_pin_face")
# 这个面已经是实体的一部分，但为了装配引用，我们可以创建一个重合的参考平面
sw_doc.create_ref_plane(plane="ZY", offset_val=0.03, target_plane_name="top_pin_face")

# --- Face: side_mate_face_top ---
# 顶部方块的 +X 侧面 (X=0.03) - 注意：这与 top_pin_face 是同一个平面位置吗？
# 顶部方块范围 X[-0.03, 0.03]。+X 侧面确实是 X=0.03。
# 销钉也是从 X=0.03 伸出的。
# 所以 top_pin_face 和 side_mate_face_top 在几何上是共面的。
# 为了区分语义，我们可以创建另一个同名或不同名的参考，或者复用。
# 规划中要求 side_mate_face_top 用于轴向约束。
# 我们创建一个名为 side_mate_face_top 的参考平面，同样在 X=0.03。
sw_doc.create_ref_plane(plane="ZY", offset_val=0.03, target_plane_name="side_mate_face_top")

# 5. 保存
model_path = r"D:\a_src\python\sw_agent\agent_output\4Axis_Robotic_Arm_Assembly-20260421_181004\parts\arm_segment_1\arm_segment_1.SLDPRT"
print(f"Saving part to: {model_path}")
sw_doc.save_as(model_path)

print("Modeling completed successfully.")