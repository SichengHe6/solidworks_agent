from pysw import SldWorksApp, PartDoc
import os

# 1. 初始化与路径设置
app = SldWorksApp()
# 零件规格与工作区路径
part_name = "sun_gear"
workdir = r"D:\a_src\python\sw_agent\agent_output\planetary_gearbox_assembly-20260511_172615\parts\sun_gear\part_output\code"
model_path = os.path.join(workdir, "sun_gear.SLDPRT")
standard_gear_path = r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT"

# 2. 物化标准件并打开工作副本
sw_doc = PartDoc(app.copy_standard_part_to_workdir_and_open(
    standard_part_path=standard_gear_path,
    workdir=workdir,
    new_part_name="sun_gear.SLDPRT"
))

print(f"已物化标准齿轮模板至: {model_path}")

# 3. 设置齿轮主动参数
# 模数 M=2, 齿数 Z=18, 齿宽 B=20mm
sw_doc.set_global_variable("M", "2")
sw_doc.set_global_variable("Z", "18")
sw_doc.set_global_variable("B", "20")

# 4. 二次特征：中心通孔切除
bore_diameter = 0.015  # 15mm
gear_width = 0.02      # 20mm

# 在 XY 平面（齿轮底面）创建草图
sketch_hole = sw_doc.insert_sketch_on_plane("XY")
# 绘制圆
sw_doc.create_circle(center_x=0, center_y=0, radius=bore_diameter/2, sketch_ref="XY")

# 关键修复：显式退出草图编辑模式
sw_doc.partDoc.SketchManager.InsertSketch(True)

# 关键修复：使用 SelectByID2 显式选中草图，防止 extrude_cut 找不到上下文
# 草图在新建后通常命名为 "Sketch" + 序号，但在物化模板中，新插入的草图通常是最后一个
# 我们通过 Extension.SelectByID2 选中刚刚创建的草图对象
sketch_name = sketch_hole.Name
sw_doc.partDoc.Extension.SelectByID2(sketch_name, "SKETCH", 0, 0, 0, False, 0, None, 0)

# 执行拉伸切除
sw_doc.extrude_cut(sketch_hole, depth=gear_width, single_direction=True)
print(f"已完成中心通孔切除: 直径 {bore_diameter*1000}mm，使用草图: {sketch_name}")

# 5. 创建装配接口 (参考面与参考轴)
# 5.1 中心旋转轴
sw_doc.create_axis(pt1=(0, 0, 0), pt2=(0, 0, gear_width), axis_name="central_axis")

# 5.2 装配对齐基准面
# mid_plane: 位于齿宽中点 (10mm)
sw_doc.create_ref_plane(plane="XY", offset_val=gear_width/2, target_plane_name="mid_plane")
# front_face: 位于顶端面 (20mm)
sw_doc.create_ref_plane(plane="XY", offset_val=gear_width, target_plane_name="front_face")
# bottom_face: 位于底面 (0mm)
sw_doc.create_ref_plane(plane="XY", offset_val=0, target_plane_name="bottom_face")

print("已成功创建装配接口: central_axis, mid_plane, front_face, bottom_face")

# 6. 保存零件
sw_doc.save_as(model_path)
print(f"太阳轮建模修复完成（已添加 SelectByID2 逻辑），文件保存至: {model_path}")