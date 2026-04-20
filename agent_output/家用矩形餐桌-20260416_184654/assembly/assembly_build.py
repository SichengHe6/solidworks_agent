# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, AssemDoc
import os

# 初始化 SolidWorks 应用
sw_app = SldWorksApp()

# 从装配规划中显式提取路径（严格使用输入路径）
table_top_model_file = r"D:\a_src\python\sw_agent\agent_output\家用矩形餐桌-20260416_184654\parts\table_top\table_top.SLDPRT"
table_leg_model_file = r"D:\a_src\python\sw_agent\agent_output\家用矩形餐桌-20260416_184654\parts\table_leg\table_leg.SLDPRT"
assembly_output_model_file = r"D:\a_src\python\sw_agent\agent_output\家用矩形餐桌-20260416_184654\assembly\家用矩形餐桌.SLDASM"

assem_name = "家用矩形餐桌"
print(f"[INFO] 开始装配：{assem_name}")

# 创建并激活装配文档
sw_assem = AssemDoc(sw_app.createAndActivate_sw_assembly(assem_name))
print(f"[INFO] 装配文档已创建并激活")

# 插入桌面（作为基准件）
table_top_comp = sw_assem.add_component(table_top_model_file, 0, 0, 0)
if not table_top_comp:
    raise RuntimeError(f"[ERROR] 桌面插入失败: {table_top_model_file}")
print(f"[INFO] 桌面已插入: {table_top_model_file}")

# 插入四条桌腿（单位：米）
# 桌面底面中心为原点，安装孔中心位于 (±0.55, ±0.35, 0)
# 桌腿高 0.72m，顶面需贴合桌面底面（Z=0），故插入 Z = -0.72
leg_positions = [
    ("front_left",  0.55,  0.35, -0.72),
    ("front_right", 0.55, -0.35, -0.72),
    ("back_left",  -0.55,  0.35, -0.72),
    ("back_right", -0.55, -0.35, -0.72)
]

leg_components = []
for name, x, y, z in leg_positions:
    comp = sw_assem.add_component(table_leg_model_file, x, y, z)
    if not comp:
        raise RuntimeError(f"[ERROR] 桌腿 {name} 插入失败: {table_leg_model_file}")
    leg_components.append(comp)
    print(f"[INFO] 桌腿 {name} 已插入: {table_leg_model_file}")

# 配合接口名称（严格按规划）
hole_axes = [
    "mount_hole_axis_fl",
    "mount_hole_axis_fr",
    "mount_hole_axis_bl",
    "mount_hole_axis_br"
]

print("[INFO] 开始施加配合约束...")

# 对每条桌腿施加两个配合：面重合 + 轴同心
for i, (leg_comp, hole_axis) in enumerate(zip(leg_components, hole_axes)):
    # 面配合：桌腿顶面 ↔ 桌面底面
    face_success = sw_assem.mate_faces(
        assem_name,
        leg_comp,
        table_top_comp,
        "top_face",
        "bottom_face",
        aligned=True
    )
    if face_success:
        print(f"[INFO] 面配合成功：桌腿 {i} 顶面 ↔ 桌面底面")
    else:
        print(f"[WARNING] 面配合失败：桌腿 {i}")

    # 轴配合：桌腿安装轴 ↔ 桌面对应孔轴
    axis_success = sw_assem.mate_axes(
        assem_name,
        leg_comp,
        table_top_comp,
        "mount_axis",
        hole_axis,
        aligned=True
    )
    if axis_success:
        print(f"[INFO] 轴配合成功：桌腿 {i} mount_axis ↔ {hole_axis}")
    else:
        print(f"[WARNING] 轴配合失败：桌腿 {i} ↔ {hole_axis}")

# 严格使用 assembly_output.model_file 指定的路径保存
sw_assem.save_as(assembly_output_model_file)
print(f"[INFO] 装配完成，已保存至: {assembly_output_model_file}")