from pysw import SldWorksApp, PartDoc
import os

# 1. 初始化应用
swapp = SldWorksApp()

# 2. 定义路径与参数
# 标准件源文件路径
standard_part_path = r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT"
# 工作区与目标文件名
workdir = r"D:\a_src\python\sw_agent\agent_output\直齿轮带中心孔-20260512_183100\part_output\code"
new_part_name = "spur_gear_m2_z24_h12.SLDPRT"
model_file = os.path.join(workdir, new_part_name)

# 齿轮规格参数 (单位: mm -> m)
M = 2 / 1000        # 模数 2mm
Z = 24              # 齿数 24
B = 10 / 1000       # 齿宽 10mm
hole_radius = 6 / 1000  # 中心孔半径 6mm (直径12mm)

# 3. 物化标准件并打开工作副本
print(f"Copying standard part to {model_file}...")
sgear = PartDoc(swapp.copy_standard_part_to_workdir_and_open(
    standard_part_path=standard_part_path,
    workdir=workdir,
    new_part_name=new_part_name
))

# 4. 修改齿轮主动全局变量
# 必须先更新主体尺寸，确保后续切除特征在正确的几何范围内
print("Updating global variables: M=2, Z=24, B=10...")
sgear.set_global_variable("M", "2")
sgear.set_global_variable("Z", "24")
sgear.set_global_variable("B", "10")

# 5. 二次特征：创建中心通孔
# 严格遵循封装流程：insert_sketch_on_plane -> create_circle -> extrude_cut
# 齿轮模板通常从 Z=0 开始拉伸，XY 平面即为底面
print("Creating center bore (12mm)...")
sketch_bore = sgear.insert_sketch_on_plane("XY")

# 绘制中心圆
# 注意：在 insert_sketch_on_plane 之后立即调用 create_circle，确保在活动草图中绘制
sgear.create_circle(0, 0, hole_radius, "XY")

# 执行拉伸切除
# 深度设为齿宽 B，确保完全贯穿。封装函数内部会处理草图的选择。
sgear.extrude_cut(sketch_bore, B)

# 6. 创建命名接口（用于装配引用）
print("Creating named interfaces...")
# 中心旋转轴
sgear.create_axis((0, 0, 0), (0, 0, B), "shaft_axis")
# 顶端面 (Z = B)
sgear.create_ref_plane("XY", B, "front_face")
# 底端面 (Z = 0)
sgear.create_ref_plane("XY", 0, "back_face")
# 齿轮中面 (Z = B/2)
sgear.create_ref_plane("XY", B/2, "gear_mid_plane")

# 7. 保存最终零件
print(f"Saving part to {model_file}")
sgear.save_as(model_file)

print("Modeling completed successfully.")