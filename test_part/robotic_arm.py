from pyswassem import SldWorksApp, PartDoc, AssemDoc

def build_robotic_arm_assembly():
    sw = SldWorksApp()
    workdir = sw.create_workdir("robot_arm_job")

    # 定义所有零件路径
    base_path = sw.get_part_path(workdir, "01_base")
    shoulder_path = sw.get_part_path(workdir, "02_shoulder")
    upper_arm_path = sw.get_part_path(workdir, "03_upper_arm")
    forearm_path = sw.get_part_path(workdir, "04_forearm")
    gripper_path = sw.get_part_path(workdir, "05_gripper_mount")
    assem_path = sw.get_assembly_path(workdir, "robot_arm_assembly")

    # ==========================================
    # 1. 基座 (Base) - 图中黑色底座
    # 简化为：半径 150mm，高 100mm 的圆柱体
    # ==========================================
    base_part = PartDoc(sw.createAndActivate_sw_part("01_base"))
    sk_base = base_part.insert_sketch_on_plane("XZ")
    base_part.create_circle(0, 0, radius=0.15, sketch_ref="XZ")
    base_part.extrude(sk_base, depth=0.1, single_direction=True, merge=True)

    # 预埋基准：偏航主轴 (J1) 和顶部接触面
    base_part.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_J1_Yaw") # -Y -> +Y
    base_part.create_ref_plane("XZ", offset_val=0.1, target_plane_name="Mate_Top")
    base_part.save_as(base_path)

    # ==========================================
    # 2. 肩部关节 (Shoulder) - 图中底座上方的橙色回转体
    # 简化为：一个 U 型座或带横向孔的方块
    # ==========================================
    shoulder_part = PartDoc(sw.createAndActivate_sw_part("02_shoulder"))
    sk_shoulder = shoulder_part.insert_sketch_on_plane("XZ")
    shoulder_part.create_centre_rectangle(0, 0, 0.12, 0.12, sketch_ref="XZ")
    shoulder_part.extrude(sk_shoulder, depth=0.12, single_direction=True, merge=True)

    # 挖出肩部俯仰轴 (J2) 的安装孔
    sk_shoulder_hole = shoulder_part.insert_sketch_on_plane("XY")
    shoulder_part.create_circle(0, 0.08, radius=0.03, sketch_ref="XY")
    shoulder_part.extrude_cut(sk_shoulder_hole, depth=0.2, single_direction=False) # 双向切透

    # 预埋基准：对接底座的 J1 轴，提供大臂的 J2 轴
    shoulder_part.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_J1_Yaw")      # -Y -> +Y
    shoulder_part.create_axis((0, 0.08, -0.1), (0, 0.08, 0.1), "Axis_J2_Pitch") # -Z -> +Z
    shoulder_part.create_ref_plane("XZ", offset_val=0.0, target_plane_name="Mate_Bottom")
    # 用于全局居中的对称面 (XY平面偏置为0)
    shoulder_part.create_ref_plane("XY", offset_val=0.0, target_plane_name="Mate_Center") 
    shoulder_part.save_as(shoulder_path)

    # ==========================================
    # 3. 大臂 (Upper Arm) - 图中较长的橙色连杆
    # 简化为：长方体，两端有连接孔
    # ==========================================
    upper_arm = PartDoc(sw.createAndActivate_sw_part("03_upper_arm"))
    sk_upper = upper_arm.insert_sketch_on_plane("XZ")
    upper_arm.create_centre_rectangle(0, 0, 0.08, 0.06, sketch_ref="XZ") # X宽80, Z厚60
    upper_arm.extrude(sk_upper, depth=0.4, single_direction=True, merge=True) # 向上长 400mm

    # 下端 J2 安装孔 (Y=0.04) 和上端 J3 安装孔 (Y=0.36)
    sk_holes_upper = upper_arm.insert_sketch_on_plane("XY")
    upper_arm.create_circle(0, 0.04, radius=0.03, sketch_ref="XY")
    upper_arm.create_circle(0, 0.36, radius=0.025, sketch_ref="XY")
    upper_arm.extrude_cut(sk_holes_upper, depth=0.1, single_direction=False)

    # 预埋基准
    upper_arm.create_axis((0, 0.04, -0.1), (0, 0.04, 0.1), "Axis_J2_Pitch") # -Z -> +Z
    upper_arm.create_axis((0, 0.36, -0.1), (0, 0.36, 0.1), "Axis_J3_Pitch") # -Z -> +Z
    upper_arm.create_ref_plane("XY", offset_val=0.0, target_plane_name="Mate_Center")
    upper_arm.save_as(upper_arm_path)

    # ==========================================
    # 4. 小臂 (Forearm) - 图中前段下弯的连杆
    # 简化为：长方体，带肘部孔和腕部孔
    # ==========================================
    forearm = PartDoc(sw.createAndActivate_sw_part("04_forearm"))
    sk_forearm = forearm.insert_sketch_on_plane("XZ")
    forearm.create_centre_rectangle(0, 0, 0.06, 0.05, sketch_ref="XZ")
    forearm.extrude(sk_forearm, depth=0.3, single_direction=True, merge=True)

    # 下端 J3 安装孔 (Y=0.03) 和前端腕部 J5 安装孔 (Y=0.27)
    sk_holes_fore = forearm.insert_sketch_on_plane("XY")
    forearm.create_circle(0, 0.03, radius=0.025, sketch_ref="XY")
    forearm.create_circle(0, 0.27, radius=0.02, sketch_ref="XY")
    forearm.extrude_cut(sk_holes_fore, depth=0.1, single_direction=False)

    # 预埋基准
    forearm.create_axis((0, 0.03, -0.1), (0, 0.03, 0.1), "Axis_J3_Pitch") # -Z -> +Z
    forearm.create_axis((0, 0.27, -0.1), (0, 0.27, 0.1), "Axis_J5_Pitch") # -Z -> +Z
    forearm.create_ref_plane("XY", offset_val=0.0, target_plane_name="Mate_Center")
    forearm.save_as(forearm_path)

    # ==========================================
    # 5. 夹爪快换座 (Gripper Mount) - 图中灰色夹爪的基部
    # 简化为：挂在 J5 上的十字架结构
    # ==========================================
    gripper_mount = PartDoc(sw.createAndActivate_sw_part("05_gripper_mount"))
    sk_mount = gripper_mount.insert_sketch_on_plane("XZ")
    gripper_mount.create_centre_rectangle(0, 0, 0.08, 0.04, sketch_ref="XZ")
    gripper_mount.extrude(sk_mount, depth=0.08, single_direction=True, merge=True)

    # 安装孔 (Y=0.04)
    sk_mount_hole = gripper_mount.insert_sketch_on_plane("XY")
    gripper_mount.create_circle(0, 0.04, radius=0.02, sketch_ref="XY")
    gripper_mount.extrude_cut(sk_mount_hole, depth=0.1, single_direction=False)

    gripper_mount.create_axis((0, 0.04, -0.1), (0, 0.04, 0.1), "Axis_J5_Pitch") # -Z -> +Z
    gripper_mount.create_ref_plane("XY", offset_val=0.0, target_plane_name="Mate_Center")
    gripper_mount.save_as(gripper_path)

    # ==========================================
    # 6. 总装配 (Assembly) - 骨架驱动装配
    # ==========================================
    assem_name = "robot_arm_assembly"
    assem = AssemDoc(sw.createAndActivate_sw_assembly(assem_name))

    # 导入组件 (将其散落在空间中)
    c_base     = assem.add_component(base_path, 0, 0, 0)
    c_shoulder = assem.add_component(shoulder_path, 0.2, 0, 0)
    c_upper    = assem.add_component(upper_arm_path, 0.4, 0, 0)
    c_forearm  = assem.add_component(forearm_path, 0.6, 0, 0)
    c_gripper  = assem.add_component(gripper_path, 0.8, 0, 0)

    # --- 配合 1: 底座 与 肩部 (J1 偏航关节) ---
    assem.mate_axes(assem_name, c_base, c_shoulder, "Axis_J1_Yaw", "Axis_J1_Yaw", aligned=True)
    assem.mate_faces(assem_name, c_base, c_shoulder, plane_name1="Mate_Top", plane_name2="Mate_Bottom", aligned=True)

    # --- 配合 2: 肩部 与 大臂 (J2 俯仰关节) ---
    assem.mate_axes(assem_name, c_shoulder, c_upper, "Axis_J2_Pitch", "Axis_J2_Pitch", aligned=True)
    assem.mate_faces(assem_name, c_shoulder, c_upper, plane_name1="Mate_Center", plane_name2="Mate_Center", aligned=True)

    # --- 配合 3: 大臂 与 小臂 (J3 肘部俯仰关节) ---
    assem.mate_axes(assem_name, c_upper, c_forearm, "Axis_J3_Pitch", "Axis_J3_Pitch", aligned=True)
    assem.mate_faces(assem_name, c_upper, c_forearm, plane_name1="Mate_Center", plane_name2="Mate_Center", aligned=True)

    # --- 配合 4: 小臂 与 夹爪座 (J5 腕部俯仰关节) ---
    assem.mate_axes(assem_name, c_forearm, c_gripper, "Axis_J5_Pitch", "Axis_J5_Pitch", aligned=True)
    assem.mate_faces(assem_name, c_forearm, c_gripper, plane_name1="Mate_Center", plane_name2="Mate_Center", aligned=True)

    assem.save_as(assem_path)
    print(f"机械臂装配体生成完毕！文件保存至: {assem_path}")

if __name__ == "__main__":
    build_robotic_arm_assembly()