import math
from pysw import SldWorksApp, PartDoc

# 1. 初始化与创建零件
app = SldWorksApp()
# 零件名称：行星架 (Planet Carrier)
# 目标路径：D:\a_src\python\sw_agent\agent_output\Planetary_Gearbox_Assembly-20260512_160944\parts\planet_carrier\planet_carrier.SLDPRT
model_path = r"D:\a_src\python\sw_agent\agent_output\Planetary_Gearbox_Assembly-20260512_160944\parts\planet_carrier\planet_carrier.SLDPRT"

sw_doc = PartDoc(app.createAndActivate_sw_part("planet_carrier"))
print("开始建模：行星架...")

# 2. 定义尺寸参数 (单位换算为米)
plate_diameter = 100 / 1000.0  # 100mm
plate_thickness = 5 / 1000.0   # 5mm
pin_diameter = 8 / 1000.0      # 8mm
pin_height = 20 / 1000.0       # 20mm
pin_radius = 36 / 1000.0       # 36mm

# 3. 建模底盘
print("步骤1：创建底盘...")
sketch_plate = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_circle(0, 0, plate_diameter / 2.0, "XY")
# 向 Z 负方向拉伸，使顶面位于 Z=0，方便后续装配对齐
sw_doc.extrude(sketch_plate, depth=-plate_thickness, single_direction=True)

# 4. 建模三个支撑轴 (Pins)
print("步骤2：创建三个支撑轴...")
# 支撑轴位置计算 (0, 120, 240 度)
angles = [0, 120, 240]
pin_positions = []
for angle in angles:
    rad = math.radians(angle)
    x = pin_radius * math.cos(rad)
    y = pin_radius * math.sin(rad)
    pin_positions.append((x, y))

# 在底盘顶面 (XY平面) 绘制销轴
sketch_pins = sw_doc.insert_sketch_on_plane("XY")
for x, y in pin_positions:
    sw_doc.create_circle(x, y, pin_diameter / 2.0, "XY")

# 向上拉伸销轴
sw_doc.extrude(sketch_pins, depth=pin_height, single_direction=True)

# 5. 创建装配接口 (Interfaces)
print("步骤3：创建参考接口...")

# 5.1 面接口: top_surface (行星轮承载面，即底盘顶面 Z=0)
# 由于底盘是向 -Z 拉伸的，XY 平面即为顶面
sw_doc.create_ref_plane("XY", 0, target_plane_name="top_surface")

# 5.2 轴接口: main_axis (主旋转轴)
sw_doc.create_axis((0, 0, 0), (0, 0, 0.05), axis_name="main_axis")

# 5.3 轴接口: pin_axis_1, pin_axis_2, pin_axis_3
for i, (x, y) in enumerate(pin_positions):
    axis_name = f"pin_axis_{i+1}"
    # 轴从底面指向销轴顶端
    sw_doc.create_axis((x, y, 0), (x, y, pin_height), axis_name=axis_name)

# 6. 保存零件
print(f"正在保存零件至: {model_path}")
sw_doc.save_as(model_path)
print("行星架建模完成。")