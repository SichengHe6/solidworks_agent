import math
from pysw import SldWorksApp, PartDoc

# 1. 初始化与创建零件
app = SldWorksApp()
# 零件名称与保存路径
part_name = "carrier"
save_path = r"D:\a_src\python\sw_agent\agent_output\planetary_gearbox_assembly-20260511_172615\parts\carrier\part_output\code\carrier.SLDPRT"

sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))

# 2. 参数定义 (单位换算为 m)
disk_diameter = 0.112
disk_thickness = 0.010
shaft_diameter = 0.020
shaft_length = 0.030
pin_dist_diameter = 0.072
pin_hole_diameter = 0.010
pin_radius = pin_dist_diameter / 2

# 3. 建模步骤

# 步骤 1: 创建主体圆盘
print("正在创建主体圆盘...")
sketch1 = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_circle(0, 0, disk_diameter / 2, "XY")
sw_doc.extrude(sketch1, disk_thickness, single_direction=True)

# 步骤 2: 创建输出轴
print("正在创建输出轴...")
# 在圆盘顶面创建草图 (Z = 0.010)
# 使用偏移平面或直接在XY偏移
plane_top = sw_doc.create_workplane_p_d("XY", disk_thickness)
sketch2 = sw_doc.insert_sketch_on_plane(plane_top)
sw_doc.create_circle(0, 0, shaft_diameter / 2, "XY")
sw_doc.extrude(sketch2, shaft_length, single_direction=True)

# 步骤 3: 创建三个销轴通孔
print("正在创建销轴孔...")
sketch3 = sw_doc.insert_sketch_on_plane(plane_top)

# 计算三个孔的坐标 (0, 120, 240 度)
angles = [0, 120, 240]
hole_coords = []
for angle in angles:
    rad = math.radians(angle)
    x = pin_radius * math.cos(rad)
    y = pin_radius * math.sin(rad)
    hole_coords.append((x, y))
    sw_doc.create_circle(x, y, pin_hole_diameter / 2, "XY")

# 拉伸切除通孔 (向下切除圆盘厚度)
sw_doc.extrude_cut(sketch3, -disk_thickness, single_direction=True)

# 4. 创建装配接口

print("正在定义装配接口...")
# 4.1 主旋转轴接口
sw_doc.create_axis((0, 0, 0), (0, 0, 0.05), "output_axis")

# 4.2 销轴孔轴线接口
for i, (x, y) in enumerate(hole_coords):
    axis_name = f"pin_axis_{i+1}"
    sw_doc.create_axis((x, y, 0), (x, y, 0.01), axis_name)

# 4.3 行星轮限位面接口 (圆盘顶面)
sw_doc.create_ref_plane("XY", disk_thickness, "mounting_face")

# 5. 保存零件
print(f"正在保存零件到: {save_path}")
sw_doc.save_as(save_path)

print("行星架建模完成。")