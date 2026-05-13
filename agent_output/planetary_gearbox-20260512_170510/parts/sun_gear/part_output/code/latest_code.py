from pysw import SldWorksApp, PartDoc
import os

# 1. 初始化应用和路径
swapp = SldWorksApp()

# 定义路径变量
standard_part_path = r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT"
workdir = r"D:\a_src\python\sw_agent\agent_output\planetary_gearbox-20260512_170510\parts\sun_gear\part_output\code"
model_file = r"D:\a_src\python\sw_agent\agent_output\planetary_gearbox-20260512_170510\parts\sun_gear\part_output\code\sun_gear.SLDPRT"

# 确保工作目录存在
if not os.path.exists(workdir):
    os.makedirs(workdir)

print(f"正在从标准件物化太阳轮: {standard_part_path}")

# 2. 物化标准件并打开工作副本
sgear_doc = swapp.copy_standard_part_to_workdir_and_open(
    standard_part_path=standard_part_path,
    workdir=workdir,
    new_part_name="sun_gear.SLDPRT"
)
sgear = PartDoc(sgear_doc)

# 3. 驱动参数设置 (M=2, Z=18, B=10mm)
print("正在设置齿轮主动参数: M=2, Z=18, B=10mm")
sgear.set_global_variable("M", "2")
sgear.set_global_variable("Z", "18")
sgear.set_global_variable("B", "10")

# 4. 二次特征 - 中心通孔 (Hole_Dia=12mm)
# 修复逻辑：针对连续出现的“草图选择失败”，采用更鲁棒的特征创建流程。
# 1. 显式清除所有选择。
# 2. 在 XY 平面创建草图并绘制圆。
# 3. 显式退出草图编辑模式（InsertSketch2(True)）。
# 4. 再次显式选中该草图对象，然后执行 extrude_cut。
print("正在创建中心通孔: 直径 12mm")
sgear_doc.ClearSelection2(True)
hole_radius = 0.012 / 2  # 换算为米
sketch_hole = sgear.insert_sketch_on_plane("XY")
sgear.create_circle(0, 0, hole_radius, "XY")

# 显式退出草图编辑模式
sgear_doc.InsertSketch2(True) 

# 显式选中刚刚创建的草图
# 获取草图名称并使用 SelectByID2 选中它
sketch_name = sketch_hole.Name
sgear_doc.Extension.SelectByID2(sketch_name, "SKETCH", 0, 0, 0, False, 0, None, 0)

# 执行拉伸切除，深度匹配齿宽 10mm (0.01m)
sgear.extrude_cut(sketch_hole, 0.01)

# 5. 创建接口 (Interfaces)
print("正在创建装配接口...")

# 轴接口: rotation_axis
sgear.create_axis((0, 0, 0), (0, 0, 0.01), "rotation_axis")

# 面接口: front_face (Z=0.01) 和 back_face (Z=0)
sgear.create_ref_plane("XY", 0.01, "front_face")
sgear.create_ref_plane("XY", 0, "back_face")

# 6. 保存零件
print(f"正在保存零件到: {model_file}")
sgear.save_as(model_file)

print("太阳轮建模完成。接口列表: rotation_axis, front_face, back_face")