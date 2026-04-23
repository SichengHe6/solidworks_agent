# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 1. 启动与创建零件文档
app = SldWorksApp()
part_name = "elbow_joint_shell"
sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
print(f"已创建并激活零件文档: {part_name}")

# 2. 尺寸定义 (输入为mm，需换算为m)
diameter_mm = 80
height_mm = 50
radius_m = (diameter_mm / 2) / 1000  # 0.04 m
height_m = height_mm / 1000          # 0.05 m

# 3. 建模主体：在XY面绘制圆并沿Z轴正向拉伸
print("步骤1: 在XY面绘制直径80mm的圆")
sketch1 = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_circle(center_x=0, center_y=0, radius=radius_m, sketch_ref="XY")

print("步骤2: 沿Z轴正向拉伸50mm")
extrude1 = sw_doc.extrude(sketch1, depth=height_m, single_direction=True, merge=True)

# 4. 创建装配所需的接口特征
print("步骤3: 创建接口参考面和参考轴")

# 底面接口 mount_face_bottom (Z=0)
sw_doc.create_ref_plane("XY", offset_val=0, target_plane_name="mount_face_bottom")

# 顶面接口 mount_face_top (Z=0.05m)
sw_doc.create_ref_plane("XY", offset_val=height_m, target_plane_name="mount_face_top")

# 主轴接口 main_axis_z (沿Z轴方向)
sw_doc.create_axis(pt1=(0, 0, 0), pt2=(0, 0, height_m), axis_name="main_axis_z")

# 5. 保存零件到指定路径
model_file_path = r"D:\a_src\python\sw_agent\agent_output\五轴机械臂-20260420_164320\parts\elbow_joint_shell\elbow_joint_shell.SLDPRT"
print(f"步骤4: 保存零件到 {model_file_path}")
sw_doc.save_as(model_file_path)

print("肘部关节壳建模完成！")