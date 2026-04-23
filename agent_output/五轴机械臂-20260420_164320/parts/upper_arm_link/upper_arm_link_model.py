# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 1. 启动与创建
app = SldWorksApp()
part_id = "upper_arm_link"
part_name = "大臂连杆"
sw_doc = PartDoc(app.createAndActivate_sw_part(part_id))

print(f"[{part_id}] 开始建模零件: {part_name}")

# 2. 参数定义 (mm转m)
diameter_mm = 70
height_mm = 250
radius_m = diameter_mm / 1000 / 2  # 0.035m
height_m = height_mm / 1000        # 0.25m

print(f"[{part_id}] 尺寸参数: 直径={diameter_mm}mm, 高度={height_mm}mm -> 半径={radius_m}m, 拉伸深度={height_m}m")

# 3. 建模 - 在XY面画圆并沿Z轴正向拉伸
sketch1 = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_circle(center_x=0, center_y=0, radius=radius_m, sketch_ref="XY")
extrude1 = sw_doc.extrude(sketch1, depth=height_m, single_direction=True)
print(f"[{part_id}] 主体圆柱拉伸完成")

# 4. 创建装配接口
# 4.1 参考面接口
# mount_face_bottom: 底面贴合面 (XY面偏移0)
sw_doc.create_ref_plane(plane="XY", offset_val=0, target_plane_name="mount_face_bottom")
# mount_face_top: 顶面贴合面 (XY面偏移height_m)
sw_doc.create_ref_plane(plane="XY", offset_val=height_m, target_plane_name="mount_face_top")
print(f"[{part_id}] 参考面接口创建完成: mount_face_bottom, mount_face_top")

# 4.2 参考轴接口
# main_axis_z: 圆柱体中心轴，沿Z轴向上
sw_doc.create_axis(pt1=(0, 0, 0), pt2=(0, 0, height_m), axis_name="main_axis_z")
print(f"[{part_id}] 参考轴接口创建完成: main_axis_z")

# 4.3 点接口 (日志标注)
print(f"[{part_id}] 点接口标注: center_point_bottom 位于 (0, 0, 0)")

# 5. 保存零件到指定路径
model_file_path = r"D:\a_src\python\sw_agent\agent_output\五轴机械臂-20260420_164320\parts\upper_arm_link\upper_arm_link.SLDPRT"
sw_doc.save_as(model_file_path)
print(f"[{part_id}] 零件已保存至: {model_file_path}")