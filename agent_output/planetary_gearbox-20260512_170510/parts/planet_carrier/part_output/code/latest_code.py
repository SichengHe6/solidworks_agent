from pysw import SldWorksApp, PartDoc
import math

# 1. 初始化应用和文档
app = SldWorksApp()
# 零件名称：行星架 (Planet Carrier)
model_file = r"D:\a_src\python\sw_agent\agent_output\planetary_gearbox-20260512_170510\parts\planet_carrier\part_output\code\planet_carrier.SLDPRT"
sw_doc = PartDoc(app.createAndActivate_sw_part("planet_carrier"))

print("开始建模：行星架 (Planet Carrier)")

# 2. 参数定义 (单位：米)
thickness = 0.008  # 8mm
pin_circle_dia = 0.072  # 72mm
pin_radius = pin_circle_dia / 2
pin_dia = 0.010  # 10mm
base_plate_dia = 0.090  # 90mm 基盘直径
pin_height = 0.012  # 12mm 销轴高度

# 3. 建模步骤 1：主体圆盘
print("步骤 1：创建主体圆盘")
sketch_base = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_circle(0, 0, base_plate_dia / 2, "XY")
sw_doc.extrude(sketch_base, thickness)

# 4. 建模步骤 2：行星轮销轴
print("步骤 2：创建三个行星轮销轴")
# 在圆盘顶面创建草图
# 顶面位于 Z = thickness
top_plane = sw_doc.create_workplane_p_d("XY", thickness)
sketch_pins = sw_doc.insert_sketch_on_plane(top_plane)

# 计算三个销轴的中心坐标 (0, 120, 240 度)
coords = [
    (pin_radius * math.cos(0), pin_radius * math.sin(0)),
    (pin_radius * math.cos(math.radians(120)), pin_radius * math.sin(math.radians(120))),
    (pin_radius * math.cos(math.radians(240)), pin_radius * math.sin(math.radians(240)))
]

for i, (x, y) in enumerate(coords):
    sw_doc.create_circle(x, y, pin_dia / 2, top_plane)
    print(f"绘制销轴 {i+1} 草图：({x:.5f}, {y:.5f})")

# 拉伸销轴
sw_doc.extrude(sketch_pins, pin_height)

# 5. 创建命名接口 (用于装配)
print("步骤 3：创建命名接口")

# 轴接口：中心输出轴
sw_doc.create_axis((0, 0, 0), (0, 0, thickness), "output_axis")

# 轴接口：三个销轴轴线
for i, (x, y) in enumerate(coords):
    axis_name = f"pin_{i+1}_axis"
    sw_doc.create_axis((x, y, thickness), (x, y, thickness + pin_height), axis_name)
    print(f"创建接口轴：{axis_name}")

# 面接口：主支撑底面
# 已经在 Z=0 处，通过 XY 平面定义
sw_doc.create_ref_plane("XY", 0, "base_face")

# 点接口：中心点
# (通过变量记录，SolidWorks API 内部通常使用轴和面配合)

# 6. 保存零件
sw_doc.save_as(model_file)
print(f"建模完成，文件已保存至：{model_file}")