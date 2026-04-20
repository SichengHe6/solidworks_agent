# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# ============================================================
# 桌腿 (table_leg) 建模代码
# 零件原点：桌腿底面中心
# 方柱 50×50×720mm + 顶部凸台 φ20×15mm
# ============================================================

# 输出路径
model_file = r"D:\a_src\python\sw_agent\agent_output\方桌餐桌-20260416_182041\parts\table_leg\table_leg.SLDPRT"

# 尺寸定义（mm → m）
leg_width = 50 / 1000.0       # 0.05 m
leg_depth = 50 / 1000.0       # 0.05 m
leg_height = 720 / 1000.0     # 0.72 m
boss_diameter = 20 / 1000.0   # 0.02 m
boss_radius = boss_diameter / 2  # 0.01 m
boss_height = 15 / 1000.0     # 0.015 m

print("=" * 60)
print("开始建模：桌腿 (table_leg)")
print(f"  方柱截面: {leg_width*1000}×{leg_depth*1000} mm")
print(f"  方柱高度: {leg_height*1000} mm")
print(f"  凸台直径: {boss_diameter*1000} mm, 高度: {boss_height*1000} mm")
print("=" * 60)

# 1. 启动 SolidWorks 并创建零件文档
app = SldWorksApp()
sw_part = PartDoc(app.createAndActivate_sw_part("table_leg"))
print("[步骤1] 零件文档已创建: table_leg")

# 2. 在 XY 平面绘制方柱截面草图（以原点为中心的 50×50mm 矩形）
sketch1 = sw_part.insert_sketch_on_plane("XY")
sw_part.create_centre_rectangle(
    center_x=0, center_y=0,
    width=leg_width, height=leg_depth,
    sketch_ref="XY"
)
print("[步骤2] 方柱截面草图已绘制 (50×50mm 中心矩形)")

# 3. 沿 Z 轴正方向拉伸 720mm 形成方柱主体
extrude1 = sw_part.extrude(sketch1, depth=leg_height, single_direction=True, merge=True)
print(f"[步骤3] 方柱主体已拉伸, 高度={leg_height*1000}mm")

# 4. 在方柱顶面（Z=720mm）创建偏移平面，绘制凸台圆草图
top_plane = sw_part.create_workplane_p_d("XY", leg_height)
print(f"[步骤4] 顶面偏移平面已创建, 偏移={leg_height*1000}mm")

sketch2 = sw_part.insert_sketch_on_plane(top_plane)
sw_part.create_circle(
    center_x=0, center_y=0,
    radius=boss_radius,
    sketch_ref="XY"
)
print(f"[步骤5] 凸台圆草图已绘制, 直径={boss_diameter*1000}mm")

# 5. 沿 Z 轴正方向拉伸 15mm 形成凸台（不与方柱合并，保持独立便于识别；但实际合并也可以）
extrude2 = sw_part.extrude(sketch2, depth=boss_height, single_direction=True, merge=True)
print(f"[步骤6] 凸台已拉伸, 高度={boss_height*1000}mm")

# 6. 创建参考轴 boss_axis（凸台圆柱轴线，沿Z方向，通过方柱顶面中心）
#    从底面中心 (0,0,0) 到凸台顶面中心 (0,0,0.735)
total_height = leg_height + boss_height  # 0.735 m
sw_part.create_axis(
    pt1=(0, 0, 0),
    pt2=(0, 0, total_height),
    axis_name="boss_axis"
)
print(f"[步骤7] 参考轴 'boss_axis' 已创建, 从(0,0,0)到(0,0,{total_height})")

# 7. 创建参考面用于装配接口
# leg_top_face: 方柱顶面，Z=720mm 处的平面
sw_part.create_ref_plane("XY", leg_height, target_plane_name="leg_top_face")
print(f"[步骤8] 参考面 'leg_top_face' 已创建, 偏移={leg_height*1000}mm")

# leg_bottom_face: 桌腿底面，Z=0 处（即 XY 平面本身），创建零偏移参考面
sw_part.create_ref_plane("XY", 0.0, target_plane_name="leg_bottom_face")
print(f"[步骤9] 参考面 'leg_bottom_face' 已创建, 偏移=0mm")

# 8. 保存零件
result = sw_part.save_as(model_file)
if result:
    print(f"[完成] 桌腿零件已成功保存至: {model_file}")
else:
    print(f"[错误] 桌腿零件保存失败!")

print("=" * 60)
print("桌腿 (table_leg) 建模完成")
print(f"  接口面: leg_top_face, leg_bottom_face")
print(f"  接口轴: boss_axis")
print(f"  关键点: bottom_center(0,0,0), top_center(0,0,720mm), boss_top_center(0,0,735mm)")
print("=" * 60)