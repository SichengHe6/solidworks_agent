# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc, AssemDoc
import os

def build_robot_arm_confirmed():
    # 1. 初始化环境与路径
    app = SldWorksApp()
    # 假设工作目录为当前脚本目录下的 robot_output
    workdir = os.path.join(os.getcwd(), "robot_output")
    if not os.path.exists(workdir):
        os.makedirs(workdir)

    # 定义零件路径 (单位转换：mm -> m)
    base_path = os.path.join(workdir, "J1_Base.SLDPRT")
    link1_path = os.path.join(workdir, "J2_Link1.SLDPRT")
    link2_path = os.path.join(workdir, "J3_Link2.SLDPRT")
    wrist_path = os.path.join(workdir, "J4_Wrist.SLDPRT")
    flange_path = os.path.join(workdir, "J5_Flange.SLDPRT")
    assem_path = os.path.join(workdir, "Robot_Assembly.SLDASM")

    # ==========================================
    # 2. J1 底座 (Base) - 直径 120, 高 60
    # ==========================================
    base_part = PartDoc(app.createAndActivate_sw_part("J1_Base"))
    # 主体圆柱
    sk_base = base_part.insert_sketch_on_plane("XZ")
    base_part.create_circle(0, 0, 0.06, "XZ")
    base_part.extrude(sk_base, depth=0.06)
    
    # 顶部轴承孔 (直径 20, 深 20)
    sk_hole = base_part.insert_sketch_on_plane("XZ")
    base_part.create_circle(0, 0, 0.01, "XZ")
    base_part.extrude_cut(sk_hole, depth=0.02)

    # NEMA17 电机接口留空 (孔距 31mm, 4个孔)
    # 在侧面 ZY 平面投影切除
    sk_nema = base_part.insert_sketch_on_plane("ZY")
    pts = [(0.0155, 0.0155), (0.0155, -0.0155), (-0.0155, -0.0155), (-0.0155, 0.0155)]
    for p in pts:
        base_part.create_circle(p[0], p[1] + 0.03, 0.0015, "ZY") # 抬高到中心高度
    base_part.extrude_cut(sk_nema, depth=0.1)

    # 基准
    base_part.create_axis((0, 0, 0), (0, 0.1, 0), "Axis_J1")
    base_part.create_ref_plane("XZ", offset_val=0.06, target_plane_name="Mate_Top")
    base_part.save_as(base_path)

    # ==========================================
    # 3. J2 大臂 (Link 1) - 双板结构 60x200x10
    # ==========================================
    link1_part = PartDoc(app.createAndActivate_sw_part("J2_Link1"))
    # 第一片板
    sk_l1_1 = link1_part.insert_sketch_on_plane("XY")
    link1_part.create_centre_rectangle(0, 0.1, 0.06, 0.2, "XY")
    link1_part.extrude(sk_l1_1, depth=0.01)
    
    # 第二片板 (偏移 40mm)
    wp_l1_2 = link1_part.create_workplane_p_d("XY", 0.04)
    sk_l1_2 = link1_part.insert_sketch_on_plane(wp_l1_2)
    link1_part.create_centre_rectangle(0, 0.1, 0.06, 0.2, "XY")
    link1_part.extrude(sk_l1_2, depth=0.01)

    # 关节孔
    sk_l1_holes = link1_part.insert_sketch_on_plane("XY")
    link1_part.create_circle(0, 0, 0.01, "XY") # 底部关节
    link1_part.create_circle(0, 0.2, 0.01, "XY") # 顶部关节
    link1_part.extrude_cut(sk_l1_holes, depth=0.1)

    # 基准
    link1_part.create_axis((0, 0, -0.1), (0, 0, 0.1), "Axis_Bottom")
    link1_part.create_axis((0, 0.2, -0.1), (0, 0.2, 0.1), "Axis_Top")
    link1_part.create_ref_plane("XY", offset_val=0.025, target_plane_name="Mate_Mid")
    link1_part.save_as(link1_path)

    # ==========================================
    # 4. J3 小臂 (Link 2) - 40x30 中空管, 长 180
    # ==========================================
    link2_part = PartDoc(app.createAndActivate_sw_part("J3_Link2"))
    sk_l2 = link2_part.insert_sketch_on_plane("XY")
    link2_part.create_centre_rectangle(0, 0.09, 0.04, 0.18, "XY")
    link2_part.extrude(sk_l2, depth=0.03)
    
    # 中空切除
    sk_l2_cut = link2_part.insert_sketch_on_plane("XY")
    link2_part.create_centre_rectangle(0, 0.09, 0.03, 0.16, "XY")
    link2_part.extrude_cut(sk_l2_cut, depth=0.03)

    link2_part.create_axis((0, 0, -0.1), (0, 0, 0.1), "Axis_Start")
    link2_part.create_axis((0, 0.18, -0.1), (0, 0.18, 0.1), "Axis_End")
    link2_part.create_ref_plane("XY", offset_val=0.015, target_plane_name="Mate_Mid")
    link2_part.save_as(link2_path)

    # ==========================================
    # 5. J4 手腕 (Wrist) - 直径 40, 长 80
    # ==========================================
    wrist_part = PartDoc(app.createAndActivate_sw_part("J4_Wrist"))
    sk_wrist = wrist_part.insert_sketch_on_plane("ZY")
    wrist_part.create_circle(0, 0, 0.02, "ZY")
    wrist_part.extrude(sk_wrist, depth=0.08)

    wrist_part.create_axis((0, 0, -0.1), (0, 0, 0.1), "Axis_Joint") # 摆动轴
    wrist_part.create_axis((0, 0, 0), (0, 0, 0.1), "Axis_Rotate") # 旋转轴
    wrist_part.create_ref_plane("ZY", offset_val=0.0, target_plane_name="Mate_Base")
    wrist_part.create_ref_plane("ZY", offset_val=0.08, target_plane_name="Mate_End")
    wrist_part.save_as(wrist_path)

    # ==========================================
    # 6. J5 法兰 (Flange) - 直径 50, 厚 10
    # ==========================================
    flange_part = PartDoc(app.createAndActivate_sw_part("J5_Flange"))
    sk_flange = flange_part.insert_sketch_on_plane("ZY")
    flange_part.create_circle(0, 0, 0.025, "ZY")
    flange_part.extrude(sk_flange, depth=0.01)

    # 4孔阵列
    sk_f_holes = flange_part.insert_sketch_on_plane("ZY")
    f_pts = [(0.015, 0), (-0.015, 0), (0, 0.015), (0, -0.015)]
    for fp in f_pts:
        flange_part.create_circle(fp[0], fp[1], 0.0025, "ZY")
    flange_part.extrude_cut(sk_f_holes, depth=0.01)

    flange_part.create_axis((0, 0, 0), (0, 0, 0.1), "Axis_Main")
    flange_part.create_ref_plane("ZY", offset_val=0.0, target_plane_name="Mate_Face")
    flange_part.save_as(flange_path)

    # ==========================================
    # 7. 总装配 (Assembly)
    # ==========================================
    assem_obj = app.createAndActivate_sw_assembly("Robot_Assembly")
    assem = AssemDoc(assem_obj)

    # 导入组件
    c_base   = assem.add_component(base_path, 0, 0, 0)
    c_link1  = assem.add_component(link1_path, 0, 0.1, 0)
    c_link2  = assem.add_component(link2_path, 0, 0.3, 0)
    c_wrist  = assem.add_component(wrist_path, 0, 0.5, 0)
    c_flange = assem.add_component(flange_path, 0, 0.6, 0)

    # --- 配合关系 ---
    # J1-J2 (底座与大臂)
    assem.mate_axes("Robot_Assembly", c_base, c_link1, "Axis_J1", "Axis_Bottom", True)
    assem.mate_faces("Robot_Assembly", c_base, c_link1, "Mate_Top", "Mate_Mid", True)

    # J2-J3 (大臂与小臂)
    assem.mate_axes("Robot_Assembly", c_link1, c_link2, "Axis_Top", "Axis_Start", True)
    assem.mate_faces("Robot_Assembly", c_link1, c_link2, "Mate_Mid", "Mate_Mid", True)

    # J3-J4 (小臂与手腕)
    assem.mate_axes("Robot_Assembly", c_link2, c_wrist, "Axis_End", "Axis_Joint", True)
    assem.mate_faces("Robot_Assembly", c_link2, c_wrist, "Mate_Mid", "Mate_Base", True)

    # J4-J5 (手腕与法兰)
    assem.mate_axes("Robot_Assembly", c_wrist, c_flange, "Axis_Rotate", "Axis_Main", True)
    assem.mate_faces("Robot_Assembly", c_wrist, c_flange, "Mate_End", "Mate_Face", True)

    assem.save_as(assem_path)
    print(f"建模与装配完成！文件保存在: {workdir}")

if __name__ == "__main__":
    build_robot_arm_confirmed()