# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 1. 初始化应用与零件文档
app = SldWorksApp()
part_name = "Base"
sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))

# 定义输出路径
model_file_path = r"D:\a_src\python\sw_agent\agent_output\4Axis_RobotArm_Assembly-20260421_171347\parts\base\base.SLDPRT"

print(f"开始建模零件: {part_name}")

# 2. 建模步骤

# --- 步骤 1: 创建底座主体 (200x200x100 mm) ---
# 尺寸转换: mm -> m
body_width = 0.200
body_depth = 0.200
body_height = 0.100

# 在 XY 平面创建草图
sketch_body = sw_doc.insert_sketch_on_plane("XY")
# 创建中心矩形，宽200mm，高200mm
sw_doc.create_centre_rectangle(
    center_x=0, 
    center_y=0, 
    width=body_width, 
    height=body_depth, 
    sketch_ref="XY"
)
# 拉伸主体，高度100mm
extrude_body = sw_doc.extrude(sketch_body, depth=body_height, single_direction=True, merge=True)
print("底座主体创建完成")

# --- 步骤 2: 创建下部台阶 (D80 x H20 mm) ---
# 需要在 Z=0.100 处创建参考平面或直接使用面？
# API 中 extrude 是基于当前草图平面的。我们需要在顶面上建草图。
# 由于封装限制，我们通常通过创建偏移平面来定位新草图，或者如果API支持直接选面则更好。
# 这里假设我们需要创建一个位于 Z=0.100 的参考平面用于绘制下一个圆。
plane_z100 = sw_doc.create_workplane_p_d(plane="XY", offset_val=body_height)

sketch_lower_frustum = sw_doc.insert_sketch_on_plane(plane_z100)
# 直径80mm -> 半径0.04m
radius_lower = 0.040
sw_doc.create_circle(center_x=0, center_y=0, radius=radius_lower, sketch_ref="XY") # 注意：虽然是在偏移平面上，但sketch_ref通常仍指代局部坐标系的XY投影关系，或者根据封装实现可能需要调整。根据知识库，sketch_ref需与平面方向一致。对于平行于XY的平面，ref应为"XY"。
height_lower = 0.020
extrude_lower = sw_doc.extrude(sketch_lower_frustum, depth=height_lower, single_direction=True, merge=True)
print("下部台阶创建完成")

# --- 步骤 3: 创建上部台阶 (D60 x H20 mm) ---
# 当前位置 Z = 0.100 + 0.020 = 0.120
current_z = body_height + height_lower
plane_z120 = sw_doc.create_workplane_p_d(plane="XY", offset_val=current_z)

sketch_upper_frustum = sw_doc.insert_sketch_on_plane(plane_z120)
# 直径60mm -> 半径0.03m
radius_upper = 0.030
sw_doc.create_circle(center_x=0, center_y=0, radius=radius_upper, sketch_ref="XY")
height_upper = 0.020
extrude_upper = sw_doc.extrude(sketch_upper_frustum, depth=height_upper, single_direction=True, merge=True)
print("上部台阶创建完成")

# --- 步骤 4: 创建顶部凸台 (D50 x H20 mm) ---
# 当前位置 Z = 0.120 + 0.020 = 0.140
current_z += height_upper
plane_z140 = sw_doc.create_workplane_p_d(plane="XY", offset_val=current_z)

sketch_top_boss = sw_doc.insert_sketch_on_plane(plane_z140)
# 直径50mm -> 半径0.025m
radius_boss = 0.025
sw_doc.create_circle(center_x=0, center_y=0, radius=radius_boss, sketch_ref="XY")
height_boss = 0.020
extrude_boss = sw_doc.extrude(sketch_top_boss, depth=height_boss, single_direction=True, merge=True)
print("顶部凸台创建完成")

# 3. 创建装配接口 (Interfaces)

# --- 面接口 ---
# mount_face_bottom: 底面 (Z=0)，法向 -Z
# 我们可以通过选择底面上的点来创建参考面，或者直接利用已有的基准面。
# 为了明确命名，我们创建一个重合的参考面并命名。
# 底面是 XY 平面 (Z=0)。
mount_face_bottom = sw_doc.create_ref_plane(plane="XY", offset_val=0, target_plane_name="mount_face_bottom")

# top_face_main: 顶部凸台的顶面 (Z=0.160)，法向 +Z
# 总高度 = 100 + 20 + 20 + 20 = 160 mm = 0.160 m
total_height = body_height + height_lower + height_upper + height_boss
top_face_main = sw_doc.create_ref_plane(plane="XY", offset_val=total_height, target_plane_name="top_face_main")

# --- 轴接口 ---
# main_axis_z: 沿 Z 轴，穿过中心
# 起点 (0,0,0), 终点 (0,0,1) 或任意长度
main_axis_z = sw_doc.create_axis(pt1=(0, 0, 0), pt2=(0, 0, total_height), axis_name="main_axis_z")

print("装配接口创建完成")

# 4. 保存零件
success = sw_doc.save_as(model_file_path)
if success:
    print(f"零件成功保存至: {model_file_path}")
else:
    print("零件保存失败")