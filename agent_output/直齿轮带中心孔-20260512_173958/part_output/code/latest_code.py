from pysw import SldWorksApp, PartDoc
import os

# 1. 初始化 SolidWorks 应用
swapp = SldWorksApp()

# 2. 定义路径与参数
# 标准件源文件路径
standard_part_path = r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT"
# 工作目录与目标文件名
workdir = r"D:\a_src\python\sw_agent\agent_output\直齿轮带中心孔-20260512_173958\part_output\code"
new_part_name = "spur_gear_m2_z24_h12.SLDPRT"
model_file = os.path.join(workdir, new_part_name)

# 齿轮参数 (单位: mm)
M = 2
Z = 24
B = 15
Alpha = 20
bore_diameter = 12

# 3. 物化标准件并打开工作副本
print(f"Copying standard part to {model_file}...")
sgear = PartDoc(swapp.copy_standard_part_to_workdir_and_open(
    standard_part_path=standard_part_path,
    workdir=workdir,
    new_part_name=new_part_name
))

# 4. 修改全局变量驱动齿轮几何
print("Setting global variables: M=2, Z=24, B=15...")
sgear.set_global_variable("M", str(M))
sgear.set_global_variable("Z", str(Z))
sgear.set_global_variable("B", str(B))
sgear.set_global_variable("Alpha", str(Alpha))

# 5. 二次特征：拉伸切除中心通孔
# 注意：pysw 内部建模使用米(m)
bore_radius_m = (bore_diameter / 2) / 1000.0
depth_m = B / 1000.0

print(f"Creating center bore with diameter {bore_diameter}mm...")
# 在 XY 平面（齿轮底面）创建草图
sketch_bore = sgear.insert_sketch_on_plane("XY")
# 绘制圆心在原点的圆
sgear.create_circle(0, 0, bore_radius_m, "XY")
# 执行拉伸切除（向上贯穿齿宽）
sgear.extrude_cut(sketch_bore, depth_m)

# 6. 创建命名参考接口
print("Creating named interfaces for assembly...")
# 中心旋转轴
sgear.create_axis((0, 0, 0), (0, 0, depth_m), "shaft_axis")

# 关键参考面
# back_face 位于 Z=0 (XY平面)
sgear.create_ref_plane("XY", 0, "back_face")
# front_face 位于 Z=B
sgear.create_ref_plane("XY", depth_m, "front_face")
# gear_mid_plane 位于 Z=B/2
sgear.create_ref_plane("XY", depth_m / 2, "gear_mid_plane")

# 7. 保存零件
sgear.save_as(model_file)
print(f"Part saved successfully to {model_file}")