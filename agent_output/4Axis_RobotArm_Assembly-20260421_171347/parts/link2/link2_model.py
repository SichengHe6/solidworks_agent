# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 1. 解析输入参数与路径
part_spec = {
    "workspace": {
        "model_file": "D:\\a_src\\python\\sw_agent\\agent_output\\4Axis_RobotArm_Assembly-20260421_171347\\parts\\link2\\link2.SLDPRT"
    }
}
model_path = part_spec["workspace"]["model_file"]

# 2. 启动应用并创建零件文档
app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("Link2"))

# 3. 定义尺寸 (单位: m)
cyl_diam = 0.050      # D50 mm
cyl_len = 0.150       # L150 mm
block_w = 0.060       # 60 mm
block_h = 0.060       # 60 mm
block_t = 0.020       # 20 mm
hole_diam = 0.010     # D10 mm
pin_len = 0.020       # Pin length 20 mm
chamfer_dist = 0.002  # C2 chamfer

print("Starting Link2 modeling...")

# 4. 主体圆柱 (Z=0 to Z=0.150)
# 在 XY 平面绘制圆，沿 Z 轴拉伸
sketch_cyl = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_circle(center_x=0, center_y=0, radius=cyl_diam/2, sketch_ref="XY")
sw_doc.extrude(sketch_cyl, depth=cyl_len, single_direction=True, merge=True)
print("Cylinder created.")

# 5. 底部方块 (Z=-0.020 to Z=0)
# 在 XY 平面 (Z=0) 绘制正方形，向负 Z 方向拉伸
sketch_bot_block = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=block_w, height=block_h, sketch_ref="XY")
sw_doc.extrude(sketch_bot_block, depth=-block_t, single_direction=True, merge=True)
print("Bottom block created.")

# 6. 顶部方块 (Z=0.150 to Z=0.170)
# 需要在 Z=0.150 处创建参考平面
plane_top_base = sw_doc.create_workplane_p_d("XY", cyl_len)
sketch_top_block = sw_doc.insert_sketch_on_plane(plane_top_base)
sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=block_w, height=block_h, sketch_ref="XY")
sw_doc.extrude(sketch_top_block, depth=block_t, single_direction=True, merge=True)
print("Top block created.")

# 7. 底部侧孔 (Bottom Hole)
# 位置：底部方块侧面 (Y- face, Y=-0.030)，中心 Z=-0.010 (方块中间)
# 孔径 D10，深度 20mm (向内，即 +Y 方向)
# 需要在 Y=-0.030 处创建参考平面
plane_bot_side = sw_doc.create_workplane_p_d("XZ", -block_w/2) # Y = -0.030
sketch_bot_hole = sw_doc.insert_sketch_on_plane(plane_bot_side)
# 在 XZ 平面上，X是水平，Z是垂直。圆心在 X=0, Z=-0.010
sw_doc.create_circle(center_x=0, center_y=-0.010, radius=hole_diam/2, sketch_ref="XZ")
# 切除方向：从 Y=-0.030 向 Y+ 方向切除，深度 0.020
sw_doc.extrude_cut(sketch_bot_hole, depth=block_t, single_direction=True)
print("Bottom hole created.")

# 8. 顶部销钉 (Top Pin)
# 位置：顶部方块侧面 (Y+ face, Y=0.030)，中心 Z=0.160 (方块中间: 0.150 + 0.010)
# 直径 D10，长度 20mm (向外，即 +Y 方向)
# 需要在 Y=0.030 处创建参考平面
plane_top_side = sw_doc.create_workplane_p_d("XZ", block_w/2) # Y = 0.030
sketch_top_pin = sw_doc.insert_sketch_on_plane(plane_top_side)
# 在 XZ 平面上，圆心在 X=0, Z=0.160
sw_doc.create_circle(center_x=0, center_y=0.160, radius=hole_diam/2, sketch_ref="XZ")
# 拉伸方向：从 Y=0.030 向 Y+ 方向拉伸，深度 0.020
sw_doc.extrude(sketch_top_pin, depth=pin_len, single_direction=True, merge=True)
print("Top pin created.")

# 9. 倒角 (Chamfer)
# 对底部方块和顶部方块的边缘进行 C2 倒角
bot_edges_pts = [
    (0.03, 0.03, 0), (-0.03, 0.03, 0), (-0.03, -0.03, 0), (0.03, -0.03, 0), # Top face edges of bottom block
    (0.03, 0.03, -0.02), (-0.03, 0.03, -0.02), (-0.03, -0.03, -0.02), (0.03, -0.03, -0.02) # Bottom face edges
]
try:
    sw_doc.chamfer_edges(on_line_points=bot_edges_pts, distance=chamfer_dist, angle=45.0)
    print("Bottom block chamfers applied.")
except Exception as e:
    print(f"Warning: Chamfer on bottom block failed or partial: {e}")

top_edges_pts = [
    (0.03, 0.03, 0.15), (-0.03, 0.03, 0.15), (-0.03, -0.03, 0.15), (0.03, -0.03, 0.15), # Bottom face edges of top block
    (0.03, 0.03, 0.17), (-0.03, 0.03, 0.17), (-0.03, -0.03, 0.17), (0.03, -0.03, 0.17) # Top face edges
]
try:
    sw_doc.chamfer_edges(on_line_points=top_edges_pts, distance=chamfer_dist, angle=45.0)
    print("Top block chamfers applied.")
except Exception as e:
    print(f"Warning: Chamfer on top block failed or partial: {e}")

# 10. 创建装配接口 (Interfaces)

# 面接口: bottom_side_face (Y- side of bottom block)
ref_plane_bot_side = sw_doc.create_ref_plane("XZ", -block_w/2, target_plane_name="bottom_side_face")
print("Interface 'bottom_side_face' created.")

# 面接口: top_side_face (Y+ side of top block)
ref_plane_top_side = sw_doc.create_ref_plane("XZ", block_w/2, target_plane_name="top_side_face")
print("Interface 'top_side_face' created.")

# 轴接口: bottom_hole_axis (Along Y, centered in bottom block side)
axis_bot_hole = sw_doc.create_axis(pt1=(0, -0.030, -0.010), pt2=(0, 0, -0.010), axis_name="bottom_hole_axis")
print("Interface 'bottom_hole_axis' created.")

# 轴接口: top_pin_axis (Along Y, centered in top block side)
axis_top_pin = sw_doc.create_axis(pt1=(0, 0.030, 0.160), pt2=(0, 0.050, 0.160), axis_name="top_pin_axis")
print("Interface 'top_pin_axis' created.")

# 11. 保存零件到指定路径
success = sw_doc.save_as(model_path)

if success:
    print(f"Link2 model saved successfully to {model_path}")
else:
    print("Failed to save Link2 model.")