# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 解析输入参数
model_file = r"D:\a_src\python\sw_agent\agent_output\家用矩形餐桌-20260416_184654\parts\table_leg\table_leg.SLDPRT"

# 1. 启动 SolidWorks 并创建零件文档
app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("table_leg"))
print("已创建桌腿零件文档")

# 2. 建模主体：50×50mm 截面，720mm 高方柱
# 所有尺寸转换为米
leg_width = 0.05  # 50 mm
leg_height = 0.72  # 720 mm

# 在 XY 基准面绘制中心正方形
sketch1 = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=leg_width, height=leg_width, sketch_ref="XY")
print("已绘制桌腿截面草图")

# 沿 +Z 方向拉伸 0.72m
body = sw_doc.extrude(sketch1, depth=leg_height, single_direction=True, merge=True)
print("已拉伸形成桌腿主体")

# 3. 创建顶部安装孔：Φ5.0mm，深15mm（简化M6螺纹孔）
hole_diameter = 0.005  # 5.0 mm
hole_depth = 0.015     # 15 mm

# 在顶面（Z=0.72）创建草图，中心点 (0,0)
sketch2 = sw_doc.insert_sketch_on_plane("XY")  # 顶面与XY平行，Z=0.72
sw_doc.create_circle(center_x=0, center_y=0, radius=hole_diameter/2, sketch_ref="XY")
print("已绘制顶部安装孔草图")

# 向下切除（-Z方向），深度0.015m
cut_feature = sw_doc.extrude_cut(sketch2, depth=-hole_depth, single_direction=True)
print("已切除顶部安装孔")

# 4. 创建装配所需接口

# 4.1 创建顶面参考面（用于装配贴合）
# 顶面位于 Z = 0.72，基于 XY 平面偏移
top_face_plane = sw_doc.create_ref_plane("XY", leg_height, target_plane_name="top_face")
print("已创建顶面参考面: top_face")

# 4.2 创建底面参考面（可选，但按接口要求）
bottom_face_plane = sw_doc.create_ref_plane("XY", 0.0, target_plane_name="bottom_face")
print("已创建底面参考面: bottom_face")

# 4.3 创建安装孔轴线：从孔底到孔顶，方向 +Z
# 孔底点：(0, 0, 0.72 - 0.015) = (0, 0, 0.705)
# 孔顶点：(0, 0, 0.72)
pt1 = (0.0, 0.0, leg_height - hole_depth)  # 孔底
pt2 = (0.0, 0.0, leg_height)               # 孔顶（顶面中心）
mount_axis = sw_doc.create_axis(pt1, pt2, axis_name="mount_axis")
print("已创建安装孔参考轴: mount_axis，方向沿 +Z")

# 5. 保存零件
success = sw_doc.save_as(model_file)
if success:
    print("桌腿零件建模完成并成功保存")
else:
    print("保存失败！")