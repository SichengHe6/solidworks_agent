from pysw import SldWorksApp, PartDoc
import os

# 零件信息
part_name = "spur_gear_m2_z40_b10"
print(f"开始建模零件: {part_name}")

# 工作区路径
workdir = r"D:\a_src\python\sw_agent\agent_output\模数2齿数40带中心通孔的直齿轮-20260513_154006\part_output\code"
model_file = os.path.join(workdir, f"{part_name}.SLDPRT")

# 标准齿轮模板路径
standard_part_path = r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT"

# 启动 SW 应用并物化标准齿轮
swapp = SldWorksApp()
sgear = PartDoc(swapp.copy_standard_part_to_workdir_and_open(
    standard_part_path=standard_part_path,
    workdir=workdir,
    new_part_name=f"{part_name}.SLDPRT"
))
print(f"标准齿轮模板已复制并打开: {part_name}.SLDPRT")

# 1. 设置主动全局变量（方程式单位）
gear_params = {
    "M": "2mm",         # 模数
    "Z": "40",          # 齿数（无量纲）
    "B": "10mm",        # 齿宽
    # Alpha, Hax, Cx 保持模板默认值（20deg, 1, 0.25）
}
for var, val in gear_params.items():
    sgear.set_global_variable(var, val)
    print(f"全局变量 {var} = {val} 已设置。")

# 尺寸换算（mm -> m）
bore_radius = 0.0125          # 12.5 mm（直径25mm）
gear_width = 0.01             # 10 mm 齿宽
half_width = gear_width / 2   # 5 mm 半齿宽

# 2. 中心通孔（直径25mm，贯穿整个齿宽）
# 齿轮模板从Z=0开始正向拉伸，占据Z=0到Z=B(0.01m)
# 在XY平面（Z=0）上绘制圆，向Z正向切除B深度即可完全贯穿
sketch_bore = sgear.insert_sketch_on_plane("XY")
sgear.create_circle(0.0, 0.0, bore_radius, "XY")
sgear.extrude_cut(sketch_bore, gear_width)  # 切除深度=齿宽，从Z=0到Z=0.01完全贯穿
print(f"中心通孔直径 25mm 已拉伸切除，贯穿整个齿宽。")

# 3. 端面倒角（内孔边缘，1mm × 45°）
chamfer_dist = 0.001          # 1 mm
chamfer_angle = 45.0

# 内孔边缘上的点（光滑圆柱面边缘，确定性高）
# 前端面（Z≈+half_width）内孔边缘点
front_bore_points = [
    (bore_radius, 0.0, half_width),
    (0.0, bore_radius, half_width),
    (-bore_radius, 0.0, half_width),
    (0.0, -bore_radius, half_width),
]
# 后端面（Z≈-half_width）内孔边缘点
back_bore_points = [
    (bore_radius, 0.0, -half_width),
    (0.0, bore_radius, -half_width),
    (-bore_radius, 0.0, -half_width),
    (0.0, -bore_radius, -half_width),
]

sgear.chamfer_edges(front_bore_points, chamfer_dist, chamfer_angle)
print("前端面内孔边缘倒角完成。")
sgear.chamfer_edges(back_bore_points, chamfer_dist, chamfer_angle)
print("后端面内孔边缘倒角完成。")

# 4. 创建装配接口
sgear.create_axis([0.0, 0.0, 0.0], [0.0, 0.0, 0.01], "shaft_axis")
print("参考轴 shaft_axis 已创建。")

sgear.create_ref_plane("XY", half_width, "front_face")        # Z = +5mm
print("参考面 front_face 已创建。")
sgear.create_ref_plane("XY", -half_width, "back_face")        # Z = -5mm
print("参考面 back_face 已创建。")
sgear.create_ref_plane("XY", 0.0, "gear_mid_plane")           # Z = 0
print("参考面 gear_mid_plane 已创建。")
# bore_cylindrical_face 为切除后自动生成的内圆柱面，装配时可通过 shaft_axis 定位

# 5. 保存最终模型
sgear.save_as(model_file)
print(f"模型 {part_name} 已保存至：{model_file}")