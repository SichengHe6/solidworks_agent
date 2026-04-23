# -*- coding: utf-8 -*-
import os
from pyswassem import SldWorksApp, PartDoc

# --- 输入参数 ---
part_id = "base"
part_name = "底座"
diameter_mm = 150
height_mm = 50
model_file = r"D:\a_src\python\sw_agent\agent_output\五轴机械臂-20260420_164320\parts\base\base.SLDPRT"

# 单位换算: mm -> m
diameter_m = diameter_mm / 1000.0
radius_m = diameter_m / 2.0
height_m = height_mm / 1000.0

print(f"[{part_id}] 开始建模零件: {part_name}")
print(f"[{part_id}] 尺寸: 直径={diameter_mm}mm, 高度={height_mm}mm")
print(f"[{part_id}] 换算后(米): 半径={radius_m}m, 高度={height_m}m")

# 1. 启动与创建文档
app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
print(f"[{part_id}] 零件文档 '{part_name}' 已创建并激活。")

# 2. 在XY面绘制草图
sketch1 = sw_doc.insert_sketch_on_plane("XY")
print(f"[{part_id}] 已在XY面插入草图。")

# 绘制中心圆 (圆心在原点，即底面圆心)
sw_doc.create_circle(center_x=0, center_y=0, radius=radius_m, sketch_ref="XY")
print(f"[{part_id}] 已绘制圆，半径={radius_m}m。")

# 3. 拉伸特征 (沿Z轴正向拉伸)
extrude1 = sw_doc.extrude(sketch1, depth=height_m, single_direction=True)
print(f"[{part_id}] 已拉伸实体，深度={height_m}m。")

# 4. 创建装配接口
# 面: mount_face_top (顶面，偏移高度)
sw_doc.create_ref_plane("XY", height_m, "mount_face_top")
print(f"[{part_id}] 已创建参考面: mount_face_top，偏移={height_m}m。")

# 面: base_face_bottom (底面，即XY面本身，偏移0以命名)
sw_doc.create_ref_plane("XY", 0, "base_face_bottom")
print(f"[{part_id}] 已创建参考面: base_face_bottom，偏移=0m。")

# 轴: main_axis_z (沿Z轴方向，从底面圆心到顶面圆心)
sw_doc.create_axis(pt1=(0, 0, 0), pt2=(0, 0, height_m), axis_name="main_axis_z")
print(f"[{part_id}] 已创建参考轴: main_axis_z，从(0,0,0)到(0,0,{height_m})。")

# 点: center_point_bottom (0,0,0) - 由main_axis_z的起点隐式提供
print(f"[{part_id}] 隐式点接口: center_point_bottom 位于 (0,0,0)。")

# 5. 保存零件
save_dir = os.path.dirname(model_file)
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

success = sw_doc.save_as(model_file)
if success:
    print(f"[{part_id}] 零件 '{part_name}' 已成功保存至: {model_file}")
else:
    print(f"[{part_id}] 零件 '{part_name}' 保存失败，请检查路径或SolidWorks状态。")