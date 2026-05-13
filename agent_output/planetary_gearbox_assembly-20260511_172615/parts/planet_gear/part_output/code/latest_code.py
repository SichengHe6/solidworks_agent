from pysw import SldWorksApp, PartDoc
import os

# 1. 初始化与路径设置
app = SldWorksApp()
# 标准件源文件路径
standard_part_path = r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT"
# 目标工作目录与文件名
workdir = r"D:\a_src\python\sw_agent\agent_output\planetary_gearbox_assembly-20260511_172615\parts\planet_gear\part_output\code"
new_part_name = "planet_gear.SLDPRT"
target_full_path = os.path.join(workdir, new_part_name)

# 确保工作目录存在
if not os.path.exists(workdir):
    os.makedirs(workdir)

# 2. 物化标准件并打开工作副本
sgear = PartDoc(app.copy_standard_part_to_workdir_and_open(
    standard_part_path=standard_part_path,
    workdir=workdir,
    new_part_name=new_part_name
))

print(f"已物化标准件至: {target_full_path}")

# 3. 参数驱动修改 (模数2, 齿数18, 齿宽20mm)
sgear.set_global_variable("M", "2")      # 模数
sgear.set_global_variable("Z", "18")     # 齿数
sgear.set_global_variable("B", "20")     # 齿宽 (mm)

# 4. 二次特征加工：中心通孔 (直径 10mm)
# 4.1 创建草图
sketch_hole = sgear.insert_sketch_on_plane("XY")
# 直径 10mm -> 半径 0.005m
sgear.create_circle(center_x=0, center_y=0, radius=0.005, sketch_ref="XY")

# 4.2 退出草图编辑模式并获取草图名称
sketch_name = sketch_hole.Name
sgear.partDoc.SketchManager.InsertSketch(True)

# 4.3 显式选中草图以确保切除成功
# 使用 SelectByID2 选中草图，确保后续特征操作能识别到该草图
sgear.partDoc.Extension.SelectByID2(sketch_name, "SKETCH", 0, 0, 0, False, 0, None, 0)

# 4.4 执行拉伸切除
# 深度 20mm (0.02m) 确保贯穿齿宽
sgear.extrude_cut(sketch_hole, depth=0.02, single_direction=True)

# 5. 创建装配接口
# 5.1 中心旋转轴 (rotation_axis)
sgear.create_axis(pt1=(0, 0, 0), pt2=(0, 0, 0.02), axis_name="rotation_axis")

# 5.2 轴向对齐中面 (mid_plane)
# 齿宽 20mm，中面位于偏移 XY 平面 10mm (0.01m) 处
sgear.create_ref_plane(plane="XY", offset_val=0.01, target_plane_name="mid_plane")

# 6. 保存零件
save_status = sgear.save_as(target_full_path)
if save_status:
    print("行星轮建模修复完成并成功保存。")
else:
    print("行星轮保存失败。")