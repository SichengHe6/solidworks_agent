# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 解析输入参数
model_file = r"D:\a_src\python\sw_agent\agent_output\家用矩形餐桌-20260416_184654\parts\table_top\table_top.SLDPRT"

# 启动 SolidWorks 并创建零件文档
app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("table_top"))
print("已创建桌面零件文档")

# 1. 创建主体：在 XY 基准面绘制中心矩形并拉伸
sketch1 = sw_doc.insert_sketch_on_plane("XY")
length = 1.2  # m
width = 0.8   # m
thickness = 0.02  # m
sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=length, height=width, sketch_ref="XY")
body = sw_doc.extrude(sketch1, depth=thickness, single_direction=True)
print("已完成桌面主体拉伸")

# 2. 顶面四周边缘添加 R5mm 圆角（R=0.005m）
# 圆角边位于顶面（Z=0.02）四边，需选取边上点
fillet_radius = 0.005  # m
top_z = thickness
# 四条长边中点（前后边）
edge_points_long = [
    (length/2, 0, top_z),      # 前边中点
    (-length/2, 0, top_z),     # 后边中点
]
# 四条短边中点（左右边）
edge_points_short = [
    (0, width/2, top_z),       # 左边中点
    (0, -width/2, top_z),      # 右边中点
]
# 合并所有边上点
edge_points = edge_points_long + edge_points_short
sw_doc.fillet_edges(on_line_points=edge_points, radius=fillet_radius)
print("已完成顶面四周边缘圆角")

# 3. 在底面四角创建安装孔（Φ8mm，贯穿）
hole_diameter = 0.008  # m
hole_radius = hole_diameter / 2
# 安装孔中心坐标（单位：m），相对于桌面底面中心（Z=0）
# 根据设计规则：距长边50mm → x = ±(1200/2 - 50)/1000 = ±0.55
#               距宽边50mm → y = ±(800/2 - 50)/1000 = ±0.35
hole_centers = [
    (0.55, 0.35, 0),   # 前左 (fl)
    (0.55, -0.35, 0),  # 前右 (fr)
    (-0.55, 0.35, 0),  # 后左 (bl)
    (-0.55, -0.35, 0)  # 后右 (br)
]
hole_axis_names = [
    "mount_hole_axis_fl",
    "mount_hole_axis_fr",
    "mount_hole_axis_bl",
    "mount_hole_axis_br"
]

for i, (cx, cy, cz) in enumerate(hole_centers):
    # 在底面（XY平面）创建孔草图
    sketch_hole = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=cx, center_y=cy, radius=hole_radius, sketch_ref="XY")
    # 贯穿切除（沿+Z方向，但底面在Z=0，需向下切？注意：桌面从Z=0拉伸到Z=0.02）
    # 切除方向：从底面（Z=0）向上贯穿到顶面（Z=0.02），所以 depth = +0.02
    sw_doc.extrude_cut(sketch_hole, depth=thickness, single_direction=True)
    print(f"已创建安装孔 {hole_axis_names[i]}")

    # 为每个孔创建参考轴（沿+Z方向）
    pt1 = (cx, cy, 0)
    pt2 = (cx, cy, 0.01)  # 稍微向上一点，确保方向为+Z
    sw_doc.create_axis(pt1, pt2, axis_name=hole_axis_names[i])
    print(f"已创建参考轴 {hole_axis_names[i]}")

# 4. 创建顶面和底面参考面（用于装配）
# 顶面：Z = 0.02，基于 XY 平面偏移 +0.02
sw_doc.create_ref_plane("XY", offset_val=thickness, target_plane_name="top_face")
# 底面：Z = 0，即 XY 平面本身，但为明确命名，可创建偏移0的平面（或直接使用XY）
# 但根据接口要求，需命名 bottom_face，故创建一个偏移0的命名平面
sw_doc.create_ref_plane("XY", offset_val=0.0, target_plane_name="bottom_face")
print("已创建 top_face 和 bottom_face 参考面")

# 5. 保存零件
success = sw_doc.save_as(model_file)
if success:
    print("桌面零件建模完成并成功保存")
else:
    print("保存失败！")