# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 1. 启动与创建
app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("cell_18650"))

# 2. 参数定义 (单位: m)
diameter_m = 0.018  # 18 mm
radius_m = diameter_m / 2
height_m = 0.065    # 65 mm

# 3. 建模步骤
print("开始建模 18650 电池...")

# 3.1 在 XY 平面绘制圆形草图
sketch_circle = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_circle(center_x=0, center_y=0, radius=radius_m, sketch_ref="XY")
print(f"已创建直径 {diameter_m*1000}mm 的圆形草图")

# 3.2 拉伸生成圆柱体
extrude_feat = sw_doc.extrude(sketch_circle, depth=height_m, single_direction=True, merge=True)
print(f"已拉伸高度 {height_m*1000}mm")

# 4. 创建装配接口
print("创建装配接口...")

# 4.1 创建中心轴 (axis_center)
# 从底部中心 (0,0,0) 指向顶部中心 (0,0,height)
axis_center = sw_doc.create_axis(
    pt1=(0, 0, 0), 
    pt2=(0, 0, height_m), 
    axis_name="axis_center"
)
print("已创建中心轴: axis_center")

# 4.2 创建参考面用于装配约束
# face_bottom_neg: 底部端面 (Z=0)，法向 -Z
# 虽然 SolidWorks 原生基准面可能不直接支持重命名为特定语义，但我们可以创建偏移平面或依赖几何特征。
# 为了稳健性，我们创建命名参考平面。
# 注意：create_ref_plane 基于现有平面偏移。
# 底部面即为 Z=0 平面，通常对应 "XY" 基准面。
# 顶部面即为 Z=height 平面。

# 创建底部参考面 (face_bottom_neg)
# 基于 XY 平面偏移 0
ref_plane_bottom = sw_doc.create_ref_plane(plane="XY", offset_val=0, target_plane_name="face_bottom_neg")
print("已创建底部参考面: face_bottom_neg")

# 创建顶部参考面 (face_top_pos)
# 基于 XY 平面偏移 height
ref_plane_top = sw_doc.create_ref_plane(plane="XY", offset_val=height_m, target_plane_name="face_top_pos")
print("已创建顶部参考面: face_top_pos")

# 5. 保存文件
output_path = r"D:\a_src\python\sw_agent\agent_output\Battery_Pack_2P4S_Assembly-20260423_155518\parts\cell_18650\cell_18650.SLDPRT"
success = sw_doc.save_as(output_path)

if success:
    print(f"零件已成功保存至: {output_path}")
else:
    print("零件保存失败")