# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 1. 启动与创建
print("启动SolidWorks应用并创建零件文档...")
app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("shoulder_joint_shell"))

# 2. 参数定义 (单位: m)
diameter_mm = 100
height_mm = 60
radius_m = diameter_mm / 2 / 1000  # 0.05 m
height_m = height_mm / 1000        # 0.06 m

# 3. 建模：在XY面绘制圆并沿Z轴正向拉伸
print("在XY面绘制草图圆...")
sketch1 = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_circle(center_x=0, center_y=0, radius=radius_m, sketch_ref="XY")

print("沿Z轴正向拉伸圆柱体...")
sw_doc.extrude(sketch1, depth=height_m, single_direction=True)

# 4. 创建装配接口
print("创建装配接口参考面与参考轴...")

# 底面接口 (Z=0平面，即XY面偏移0)
sw_doc.create_ref_plane(plane="XY", offset_val=0, target_plane_name="mount_face_bottom")

# 顶面接口 (Z=0.06平面)
sw_doc.create_ref_plane(plane="XY", offset_val=height_m, target_plane_name="mount_face_top")

# 主轴接口 (沿Z轴方向)
sw_doc.create_axis(pt1=(0, 0, 0), pt2=(0, 0, height_m), axis_name="main_axis_z")

# 5. 保存零件到指定路径
model_file_path = r"D:\a_src\python\sw_agent\agent_output\五轴机械臂-20260420_164320\parts\shoulder_joint_shell\shoulder_joint_shell.SLDPRT"
print(f"保存零件至: {model_file_path}")
sw_doc.save_as(model_file_path)

print("肩部关节壳 (shoulder_joint_shell) 建模完成！")