# -*- coding: utf-8 -*-
import os
from pyswassem import SldWorksApp, PartDoc

# 1. 启动应用与创建零件文档
app = SldWorksApp()
part_name = "lower_arm_link"
print(f"[{part_name}] 正在创建零件文档: {part_name}")
sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))

# 2. 定义尺寸参数 (输入为mm，需换算为m)
diameter_mm = 55
height_mm = 180
radius_m = (diameter_mm / 2) / 1000.0  # 0.0275 m
height_m = height_mm / 1000.0          # 0.18 m

print(f"[{part_name}] 尺寸参数: 直径={diameter_mm}mm, 高度={height_mm}mm, 半径={radius_m}m, 拉伸高度={height_m}m")

# 3. 在 XY 面绘制圆形草图
print(f"[{part_name}] 在 XY 面绘制圆形草图...")
sketch_xy = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_circle(center_x=0, center_y=0, radius=radius_m, sketch_ref="XY")

# 4. 沿 Z 轴正向拉伸
print(f"[{part_name}] 沿 Z 轴正向拉伸，高度: {height_m} m...")
sw_doc.extrude(sketch_xy, depth=height_m, single_direction=True, merge=True)

# 5. 创建装配所需的接口特征
print(f"[{part_name}] 创建装配接口特征...")

# 面接口: mount_face_bottom (底面贴合面，Z=0，与XY面重合)
sw_doc.create_ref_plane("XY", 0, "mount_face_bottom")
print(f"[{part_name}] 已创建面接口: mount_face_bottom (偏移 XY 0m)")

# 面接口: mount_face_top (顶面贴合面，Z=height_m)
sw_doc.create_ref_plane("XY", height_m, "mount_face_top")
print(f"[{part_name}] 已创建面接口: mount_face_top (偏移 XY {height_m}m)")

# 轴接口: main_axis_z (圆柱体中心轴，沿全局Z轴方向)
sw_doc.create_axis(pt1=(0, 0, 0), pt2=(0, 0, height_m), axis_name="main_axis_z")
print(f"[{part_name}] 已创建轴接口: main_axis_z (从 (0,0,0) 到 (0,0,{height_m}))")

# 点接口: center_point_bottom (底面圆心，局部坐标系原点)
# 无专门命名点API，记录坐标供装配参考
print(f"[{part_name}] 点接口记录: center_point_bottom 坐标为 (0, 0, 0)")

# 6. 保存零件到指定路径
model_file_path = r"D:\a_src\python\sw_agent\agent_output\五轴机械臂-20260420_164320\parts\lower_arm_link\lower_arm_link.SLDPRT"
print(f"[{part_name}] 准备保存零件至: {model_file_path}")

# 确保输出目录存在
os.makedirs(os.path.dirname(model_file_path), exist_ok=True)

# 执行保存
sw_doc.save_as(model_file_path)
print(f"[{part_name}] 零件建模与保存完成！")