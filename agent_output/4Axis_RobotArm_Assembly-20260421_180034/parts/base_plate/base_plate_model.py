# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 1. 启动与创建
app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("Base Plate"))

# 2. 建模参数 (单位: m)
base_length = 0.200  # 200mm
base_width = 0.200   # 200mm
base_height = 0.100  # 100mm
boss_diam = 0.040    # 40mm
boss_height = 0.030  # 30mm

print(f"开始建模 Base Plate...")

# 3. 主体底座 (Rectangular Prism)
# 在 XY 平面绘制中心矩形
sketch_base = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_centre_rectangle(
    center_x=0, 
    center_y=0, 
    width=base_length, 
    height=base_width, 
    sketch_ref="XY"
)
# 向上拉伸 100mm
extrude_base = sw_doc.extrude(sketch_base, depth=base_height, single_direction=True, merge=True)
print("底座主体拉伸完成。")

# 4. 顶部凸台 (Cylindrical Boss)
# 在顶面 (Z = base_height) 创建偏移平面或直接在该高度建草图
# 这里使用 create_workplane_p_d 创建一个平行于 XY 的平面，偏移量为 base_height
top_plane = sw_doc.create_workplane_p_d("XY", offset_val=base_height)

# 在新建的平面上绘制圆
sketch_boss = sw_doc.insert_sketch_on_plane(top_plane)
sw_doc.create_circle(
    center_x=0, 
    center_y=0, 
    radius=boss_diam / 2, 
    sketch_ref="XY" # 注意：虽然是在自定义平面上，但参考系通常仍沿用主基准面的投影逻辑，或者API内部处理了映射。根据文档，sketch_ref 需与平面方向一致，XY平面的法向是Z，所以用XY参考是合理的。
)
# 向上拉伸 30mm
extrude_boss = sw_doc.extrude(sketch_boss, depth=boss_height, single_direction=True, merge=True)
print("顶部凸台拉伸完成。")

# 5. 创建装配接口 (Interfaces)

# 5.1 面接口: base_bottom_face (Z=0, Normal -Z)
# 底面就是原始 XY 平面，或者实体底面。为了明确引用，我们可以创建一个参考面或者直接依赖几何特征。
# 根据要求，优先创建命名参考面。
# 底面位于 Z=0，法向向下。SolidWorks 中通常选择面来配合。
# 这里我们创建参考面以便后续装配脚本通过名称查找。
ref_bottom_face = sw_doc.create_ref_plane("XY", offset_val=0, target_plane_name="base_bottom_face")

# 5.2 面接口: base_top_face (Z=base_height + boss_height, Normal +Z)
# 顶面是凸台的顶面。
total_height = base_height + boss_height
ref_top_face = sw_doc.create_ref_plane("XY", offset_val=total_height, target_plane_name="base_top_face")

# 5.3 轴接口: base_top_axis (Along Z, through origin)
# 旋转轴沿 Z 轴，穿过原点 (0,0,0) 到 (0,0,1)
axis_top = sw_doc.create_axis(
    pt1=(0, 0, 0), 
    pt2=(0, 0, 1), 
    axis_name="base_top_axis"
)

print("装配接口创建完成。")

# 6. 保存零件
output_path = r"D:\a_src\python\sw_agent\agent_output\4Axis_RobotArm_Assembly-20260421_180034\parts\base_plate\base_plate.SLDPRT"
success = sw_doc.save_as(output_path)

if success:
    print(f"零件已成功保存至: {output_path}")
else:
    print("零件保存失败。")