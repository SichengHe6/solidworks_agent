# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# ============================================================
# 桌面 (table_top) 建模代码
# ============================================================

# 输出路径
model_file = r"D:\a_src\python\sw_agent\agent_output\方桌餐桌-20260416_182041\parts\table_top\table_top.SLDPRT"

# 尺寸定义 (mm -> m)
table_length = 800 / 1000.0   # 0.8 m  X方向
table_width  = 800 / 1000.0   # 0.8 m  Y方向
table_thick  = 30  / 1000.0   # 0.03 m Z方向

hole_diameter = 20 / 1000.0   # 0.02 m
hole_radius   = hole_diameter / 2.0  # 0.01 m
hole_depth    = 15 / 1000.0   # 0.015 m

# 盲孔中心相对于桌面中心的偏移 (mm -> m)
hole_offset = 325 / 1000.0    # 0.325 m

# 四个盲孔中心坐标 (XY平面，相对于原点)
hole_centers = {
    "front_left":  (-hole_offset, -hole_offset),
    "front_right": ( hole_offset, -hole_offset),
    "rear_left":   (-hole_offset,  hole_offset),
    "rear_right":  ( hole_offset,  hole_offset),
}

# 1. 启动 SolidWorks 并创建零件文档
print("=== 开始创建桌面零件 ===")
app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("table_top"))
print("零件文档已创建: table_top")

# 2. 绘制桌面主体草图 (XY平面，以原点为中心的矩形)
print("步骤1: 在XY平面绘制800x800mm矩形草图")
sketch_main = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_centre_rectangle(
    center_x=0, center_y=0,
    width=table_length, height=table_width,
    sketch_ref="XY"
)

# 3. 沿Z轴正方向拉伸30mm形成桌面板体
print("步骤2: 拉伸30mm形成桌面板体")
extrude_main = sw_doc.extrude(sketch_main, depth=table_thick, single_direction=True, merge=True)
print("桌面板体拉伸完成")

# 4. 在底面 (Z=0平面，即XY平面) 绘制四个盲孔圆并切除
#    盲孔从底面向Z轴正方向切入15mm
print("步骤3: 在XY平面(底面Z=0)绘制四个盲孔圆")
sketch_holes = sw_doc.insert_sketch_on_plane("XY")
for name, (cx, cy) in hole_centers.items():
    sw_doc.create_circle(
        center_x=cx, center_y=cy,
        radius=hole_radius,
        sketch_ref="XY"
    )
    print(f"  盲孔圆已绘制: {name} at ({cx*1000:.0f}, {cy*1000:.0f}) mm")

# 5. 切除拉伸：从Z=0平面向Z正方向切入15mm
print("步骤4: 切除拉伸15mm形成盲孔")
cut_holes = sw_doc.extrude_cut(sketch_holes, depth=hole_depth, single_direction=True)
print("四个盲孔切除完成")

# 6. 创建参考面接口
#    bottom_face: 桌面底面参考面 (Z=0平面，即XY平面本身，偏移0)
print("步骤5: 创建参考面接口")
bottom_face_plane = sw_doc.create_ref_plane("XY", offset_val=0.0, target_plane_name="bottom_face")
print("  参考面 bottom_face 已创建 (Z=0, 底面)")

#    top_face: 桌面顶面参考面 (Z=30mm)
top_face_plane = sw_doc.create_ref_plane("XY", offset_val=table_thick, target_plane_name="top_face")
print("  参考面 top_face 已创建 (Z=30mm, 顶面)")

# 7. 创建参考轴接口 (四个盲孔轴线，沿Z方向)
print("步骤6: 创建四个盲孔参考轴")

axis_definitions = {
    "hole_axis_front_left":  (-hole_offset, -hole_offset),
    "hole_axis_front_right": ( hole_offset, -hole_offset),
    "hole_axis_rear_left":   (-hole_offset,  hole_offset),
    "hole_axis_rear_right":  ( hole_offset,  hole_offset),
}

for axis_name, (ax, ay) in axis_definitions.items():
    pt1 = (ax, ay, 0.0)
    pt2 = (ax, ay, table_thick)
    sw_doc.create_axis(pt1=pt1, pt2=pt2, axis_name=axis_name)
    print(f"  参考轴 {axis_name} 已创建: ({ax*1000:.0f}, {ay*1000:.0f}, 0) -> ({ax*1000:.0f}, {ay*1000:.0f}, {table_thick*1000:.0f})")

# 8. 保存零件
print("步骤7: 保存零件文件")
save_result = sw_doc.save_as(model_file)
if save_result:
    print(f"=== 桌面零件保存成功: {model_file} ===")
else:
    print(f"=== 桌面零件保存失败! ===")