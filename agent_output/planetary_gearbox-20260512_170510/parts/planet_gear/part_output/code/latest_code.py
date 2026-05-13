from pysw import SldWorksApp, PartDoc
import os

# 1. 初始化应用
swapp = SldWorksApp()

# 2. 定义路径与参数
# 零件保存路径
model_file = r"D:\a_src\python\sw_agent\agent_output\planetary_gearbox-20260512_170510\parts\planet_gear\part_output\code\planet_gear.SLDPRT"
workdir = os.path.dirname(model_file)
# 标准件源路径
standard_part_path = r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT"

# 零件规格参数 (单位: m)
M = 2 / 1000        # 模数 2mm
Z = 18              # 齿数
B = 10 / 1000       # 齿宽 10mm
Hole_Dia = 10 / 1000 # 中心孔直径 10mm

# 3. 物化标准件并打开工作副本
sgear = PartDoc(swapp.copy_standard_part_to_workdir_and_open(
    standard_part_path=standard_part_path,
    workdir=workdir,
    new_part_name="planet_gear.SLDPRT"
))

print(f"Step 1: Standard part materialized and opened at {model_file}")

# 4. 设置齿轮主动参数
# 齿轮模板由全局变量控制，修改后会自动更新几何
sgear.set_global_variable("M", "2")
sgear.set_global_variable("Z", "18")
sgear.set_global_variable("B", "10")
sgear.set_global_variable("Hax", "1")  # 确保齿顶高系数为标准值

print("Step 2: Global variables updated (M=2, Z=18, B=10)")

# 5. 二次特征：中心通孔
# 修复逻辑：
# 在 pysw 封装中，extrude_cut 依赖于当前选中的草图。
# 1. insert_sketch_on_plane 会进入草图编辑模式。
# 2. create_circle 在当前激活草图中绘制几何。
# 3. 必须显式退出草图编辑模式，使草图成为一个可被特征操作引用的 Feature。
# 4. 确保草图被选中后再执行 extrude_cut。

sketch_obj = sgear.insert_sketch_on_plane("XY")
sgear.create_circle(0, 0, Hole_Dia / 2, "XY")

# 显式退出草图模式（通过调用底层 API 确保草图特征被创建并关闭编辑状态）
# pysw 的 PartDoc 实例通常持有底层 swModel 对象
sgear.sw_doc.InsertSketch2(True) 

# 显式选中刚刚创建的草图特征，确保 extrude_cut 作用于正确的对象
# 这里的 sketch_obj.Name 通常是 "Sketch1" 或类似名称
sketch_name = sketch_obj.Name
sgear.sw_doc.Extension.SelectByID2(sketch_name, "SKETCH", 0, 0, 0, False, 0, None, 0)

# 执行拉伸切除，深度为齿宽 B
sgear.extrude_cut(sketch_obj, B)

print(f"Step 3: Center hole (Dia={Hole_Dia*1000}mm) created via extrude_cut on {sketch_name}")

# 6. 创建命名接口
# 旋转中心轴：从原点到 Z 正向
sgear.create_axis((0, 0, 0), (0, 0, B), "rotation_axis")
# 轴向对齐面：Z=0 的端面 (front_face)
sgear.create_ref_plane("XY", 0, "front_face")
# 轴向对齐面：Z=B 的端面 (back_face)
sgear.create_ref_plane("XY", B, "back_face")

print("Step 4: Interfaces created: rotation_axis, front_face, back_face")

# 7. 保存零件
sgear.save_as(model_file)
print(f"Step 5: Part saved successfully to {model_file}")