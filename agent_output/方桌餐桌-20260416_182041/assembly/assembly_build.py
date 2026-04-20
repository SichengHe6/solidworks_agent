# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, AssemDoc
import os

# ========== 路径配置（严格使用规划中的路径） ==========
table_top_path = r"D:\a_src\python\sw_agent\agent_output\方桌餐桌-20260416_182041\parts\table_top\table_top.SLDPRT"
table_leg_path = r"D:\a_src\python\sw_agent\agent_output\方桌餐桌-20260416_182041\parts\table_leg\table_leg.SLDPRT"
assembly_save_path = r"D:\a_src\python\sw_agent\agent_output\方桌餐桌-20260416_182041\assembly\方桌餐桌.SLDASM"

assem_name = "方桌餐桌"

print("=" * 60)
print(f"[装配开始] 装配体: {assem_name}")
print(f"  桌面零件路径: {table_top_path}")
print(f"  桌腿零件路径: {table_leg_path}")
print(f"  装配体保存路径: {assembly_save_path}")
print("=" * 60)

# ========== 1. 创建装配文档 ==========
sw_app = SldWorksApp()
sw_assem = AssemDoc(sw_app.createAndActivate_sw_assembly(assem_name))
print("[步骤1] 装配文档创建成功")

# ========== 2. 插入零件 ==========
# 2.1 插入桌面（基准件）
# 桌面零件原点在底面中心，装配中桌面底面位于全局Z=0.72m
table_top = sw_assem.add_component(table_top_path, 0, 0, 0.72)
if table_top:
    print(f"[步骤2.1] 桌面插入成功, comp_name = {table_top}")
else:
    print("[错误] 桌面插入失败!")

# 2.2 插入前左桌腿
leg_front_left = sw_assem.add_component(table_leg_path, -0.325, -0.325, 0)
if leg_front_left:
    print(f"[步骤2.2] 前左桌腿插入成功, comp_name = {leg_front_left}")
else:
    print("[错误] 前左桌腿插入失败!")

# 2.3 插入前右桌腿
leg_front_right = sw_assem.add_component(table_leg_path, 0.325, -0.325, 0)
if leg_front_right:
    print(f"[步骤2.3] 前右桌腿插入成功, comp_name = {leg_front_right}")
else:
    print("[错误] 前右桌腿插入失败!")

# 2.4 插入后左桌腿
leg_rear_left = sw_assem.add_component(table_leg_path, -0.325, 0.325, 0)
if leg_rear_left:
    print(f"[步骤2.4] 后左桌腿插入成功, comp_name = {leg_rear_left}")
else:
    print("[错误] 后左桌腿插入失败!")

# 2.5 插入后右桌腿
leg_rear_right = sw_assem.add_component(table_leg_path, 0.325, 0.325, 0)
if leg_rear_right:
    print(f"[步骤2.5] 后右桌腿插入成功, comp_name = {leg_rear_right}")
else:
    print("[错误] 后右桌腿插入失败!")

# ========== 3. 施加配合约束 ==========
if table_top and leg_front_left and leg_front_right and leg_rear_left and leg_rear_right:
    print("[步骤3] 开始施加配合约束...")

    # 定义四条桌腿的配合信息：(桌腿comp, 桌面盲孔轴名, 描述)
    leg_mate_info = [
        (leg_front_left,  "hole_axis_front_left",  "前左桌腿"),
        (leg_front_right, "hole_axis_front_right", "前右桌腿"),
        (leg_rear_left,   "hole_axis_rear_left",   "后左桌腿"),
        (leg_rear_right,  "hole_axis_rear_right",  "后右桌腿"),
    ]

    for idx, (leg_comp, hole_axis_name, desc) in enumerate(leg_mate_info, start=1):
        # 轴同心配合：桌腿凸台轴线 boss_axis <-> 桌面盲孔轴线
        print(f"  [3.{idx}a] {desc} - 轴同心配合: boss_axis <-> {hole_axis_name}")
        sw_assem.mate_axes(assem_name, leg_comp, table_top, "boss_axis", hole_axis_name, aligned=True)
        print(f"  [3.{idx}a] {desc} - 轴同心配合完成")

        # 面重合配合：桌腿顶面 leg_top_face <-> 桌面底面 bottom_face（法线相反，aligned=False）
        print(f"  [3.{idx}b] {desc} - 面重合配合: leg_top_face <-> bottom_face")
        sw_assem.mate_faces(assem_name, leg_comp, table_top, "leg_top_face", "bottom_face", aligned=False)
        print(f"  [3.{idx}b] {desc} - 面重合配合完成")

    print("[步骤3] 所有配合约束施加完成")
else:
    missing = []
    if not table_top: missing.append("桌面")
    if not leg_front_left: missing.append("前左桌腿")
    if not leg_front_right: missing.append("前右桌腿")
    if not leg_rear_left: missing.append("后左桌腿")
    if not leg_rear_right: missing.append("后右桌腿")
    print(f"[错误] 部分零件插入失败，无法执行配合! 缺失: {', '.join(missing)}")

# ========== 4. 保存装配体 ==========
assembly_dir = os.path.dirname(assembly_save_path)
if not os.path.exists(assembly_dir):
    os.makedirs(assembly_dir)
    print(f"[步骤4] 创建输出目录: {assembly_dir}")

sw_assem.save_as(assembly_save_path)
print(f"[步骤4] 装配体已保存至: {assembly_save_path}")

print("=" * 60)
print("[装配完成] 方桌餐桌装配流程结束")
print("=" * 60)