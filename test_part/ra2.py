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
    finger_path = sw.get_part_path(workdir, "06_gripper_finger") # 新增夹爪指路径
    assem_path = sw.get_assembly_path(workdir, "robot_arm_assembly")

    # ==========================================
    # 1. 基座 (Base)
    # ==========================================
    base_part = PartDoc(sw.createAndActivate_sw_part("01_base"))
    sk_base = base_part.insert_sketch_on_plane("XZ")
    base_part.create_circle(0, 0, radius=0.15, sketch_ref="XZ")
    base_part.extrude(sk_base, depth=0.1, single_direction=True, merge=True)

    base_part.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_J1_Yaw")
    base_part.create_ref_plane("XZ", offset_val=0.1, target_plane_name="Mate_Top")
    base_part.save_as(base_path)

    # ==========================================
    # 2. 肩部关节 (Shoulder)
    # ==========================================
    shoulder_part = PartDoc(sw.createAndActivate_sw_part("02_shoulder"))
    sk_shoulder = shoulder_part.insert_sketch_on_plane("XZ")
    shoulder_part.create_centre_rectangle(0, 0, 0.12, 0.12, sketch_ref="XZ")
    shoulder_part.extrude(sk_shoulder, depth=0.12, single_direction=True, merge=True)

    sk_shoulder_hole = shoulder_part.insert_sketch_on_plane("XY")
    shoulder_part.create_circle(0, 0.08, radius=0.03, sketch_ref="XY")
    shoulder_part.extrude_cut(sk_shoulder_hole, depth=0.2, single_direction=False)

    shoulder_part.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_J1_Yaw")
    shoulder_part.create_axis((0, 0.08, -0.1), (0, 0.08, 0.1), "Axis_J2_Pitch")
    shoulder_part.create_ref_plane("XZ", offset_val=0.0, target_plane_name="Mate_Bottom")
    shoulder_part.create_ref_plane("XY", offset_val=0.0, target_plane_name="Mate_Center") 
    shoulder_part.save_as(shoulder_path)

    # ==========================================
    # 3. 大臂 (Upper Arm) + 径向倒圆角
    # ==========================================
    upper_arm = PartDoc(sw.createAndActivate_sw_part("03_upper_arm"))
    sk_upper = upper_arm.insert_sketch_on_plane("XZ")
    upper_arm.create_centre_rectangle(0, 0, 0.08, 0.06, sketch_ref="XZ")
    upper_arm.extrude(sk_upper, depth=0.4, single_direction=True, merge=True)

    sk_holes_upper = upper_arm.insert_sketch_on_plane("XY")
    upper_arm.create_circle(0, 0.04, radius=0.03, sketch_ref="XY")
    upper_arm.create_circle(0, 0.36, radius=0.025, sketch_ref="XY")
    upper_arm.extrude_cut(sk_holes_upper, depth=0.1, single_direction=False)

    # [新增] 大臂径向倒圆角 (半径 10mm)
    # 取四条竖直长边在中点 (Y=0.2) 处的坐标
    edge_pts_up = [(0.04, 0.2, 0.03), (-0.04, 0.2, 0.03), (0.04, 0.2, -0.03), (-0.04, 0.2, -0.03)]
    upper_arm.fillet_edges(edge_pts_up, radius=0.01)

    upper_arm.create_axis((0, 0.04, -0.1), (0, 0.04, 0.1), "Axis_J2_Pitch")
    upper_arm.create_axis((0, 0.36, -0.1), (0, 0.36, 0.1), "Axis_J3_Pitch")
    upper_arm.create_ref_plane("XY", offset_val=0.0, target_plane_name="Mate_Center")
    upper_arm.save_as(upper_arm_path)

    # ==========================================
    # 4. 小臂 (Forearm) + 径向倒圆角
    # ==========================================
    forearm = PartDoc(sw.createAndActivate_sw_part("04_forearm"))
    sk_forearm = forearm.insert_sketch_on_plane("XZ")
    forearm.create_centre_rectangle(0, 0, 0.06, 0.05, sketch_ref="XZ")
    forearm.extrude(sk_forearm, depth=0.3, single_direction=True, merge=True)

    sk_holes_fore = forearm.insert_sketch_on_plane("XY")
    forearm.create_circle(0, 0.03, radius=0.025, sketch_ref="XY")
    forearm.create_circle(0, 0.27, radius=0.02, sketch_ref="XY")
    forearm.extrude_cut(sk_holes_fore, depth=0.1, single_direction=False)

    # [新增] 小臂径向倒圆角 (半径 10mm)
    # 取四条竖直长边在中点 (Y=0.15) 处的坐标
    edge_pts_fore = [(0.03, 0.15, 0.025), (-0.03, 0.15, 0.025), (0.03, 0.15, -0.025), (-0.03, 0.15, -0.025)]
    forearm.fillet_edges(edge_pts_fore, radius=0.01)

    forearm.create_axis((0, 0.03, -0.1), (0, 0.03, 0.1), "Axis_J3_Pitch")
    forearm.create_axis((0, 0.27, -0.1), (0, 0.27, 0.1), "Axis_J5_Pitch")
    forearm.create_ref_plane("XY", offset_val=0.0, target_plane_name="Mate_Center")
    forearm.save_as(forearm_path)

    # ==========================================
    # 5. 夹爪快换座 (Gripper Mount) + 夹爪安装接口
    # ==========================================
    gripper_mount = PartDoc(sw.createAndActivate_sw_part("05_gripper_mount"))
    sk_mount = gripper_mount.insert_sketch_on_plane("XZ")
    gripper_mount.create_centre_rectangle(0, 0, 0.08, 0.04, sketch_ref="XZ")
    gripper_mount.extrude(sk_mount, depth=0.08, single_direction=True, merge=True)

    sk_mount_hole = gripper_mount.insert_sketch_on_plane("XY")
    gripper_mount.create_circle(0, 0.04, radius=0.02, sketch_ref="XY")
    gripper_mount.extrude_cut(sk_mount_hole, depth=0.1, single_direction=False)

    gripper_mount.create_axis((0, 0.04, -0.1), (0, 0.04, 0.1), "Axis_J5_Pitch")
    gripper_mount.create_ref_plane("XY", offset_val=0.0, target_plane_name="Mate_Center")
    
    # [新增] 为两个夹爪指预埋安装接口 (在快换座顶部 Y=0.08 处，分别偏置 20mm)
    gripper_mount.create_axis((-0.02, -0.1, 0), (-0.02, 0.1, 0), "Axis_Finger_L")
    gripper_mount.create_axis((0.02, -0.1, 0), (0.02, 0.1, 0), "Axis_Finger_R")
    gripper_mount.create_ref_plane("XZ", offset_val=0.08, target_plane_name="Mate_Top")
    gripper_mount.save_as(gripper_path)

    # ==========================================
    # 6. 夹爪指 (Gripper Finger) - 新增零件
    # ==========================================
    finger = PartDoc(sw.createAndActivate_sw_part("06_gripper_finger"))
    sk_finger = finger.insert_sketch_on_plane("XZ")
    finger.create_centre_rectangle(0, 0, 0.01, 0.02, sketch_ref="XZ") # 截面 10x20
    finger.extrude(sk_finger, depth=0.06, single_direction=True, merge=True) # 长 60mm

    finger.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_Main")
    finger.create_ref_plane("XZ", offset_val=0.0, target_plane_name="Mate_Bottom")
    finger.create_ref_plane("XY", offset_val=0.0, target_plane_name="Mate_Center") # 防转基准
    finger.save_as(finger_path)

    # ==========================================
    # 7. 总装配 (Assembly)
    # ==========================================
    assem_name = "robot_arm_assembly"
    assem = AssemDoc(sw.createAndActivate_sw_assembly(assem_name))

    c_base     = assem.add_component(base_path, 0, 0, 0)
    c_shoulder = assem.add_component(shoulder_path, 0.2, 0, 0)
    c_upper    = assem.add_component(upper_arm_path, 0.4, 0, 0)
    c_forearm  = assem.add_component(forearm_path, 0.6, 0, 0)
    c_gripper  = assem.add_component(gripper_path, 0.8, 0, 0)
    
    # 导入两个夹爪指
    c_finger_l = assem.add_component(finger_path, 1.0, 0, 0)
    c_finger_r = assem.add_component(finger_path, 1.1, 0, 0)

    # --- 机械臂主干装配 (保持不变) ---
    assem.mate_axes(assem_name, c_base, c_shoulder, "Axis_J1_Yaw", "Axis_J1_Yaw", aligned=True)
    assem.mate_faces(assem_name, c_base, c_shoulder, plane_name1="Mate_Top", plane_name2="Mate_Bottom", aligned=True)

    assem.mate_axes(assem_name, c_shoulder, c_upper, "Axis_J2_Pitch", "Axis_J2_Pitch", aligned=True)
    assem.mate_faces(assem_name, c_shoulder, c_upper, plane_name1="Mate_Center", plane_name2="Mate_Center", aligned=True)

    assem.mate_axes(assem_name, c_upper, c_forearm, "Axis_J3_Pitch", "Axis_J3_Pitch", aligned=True)
    assem.mate_faces(assem_name, c_upper, c_forearm, plane_name1="Mate_Center", plane_name2="Mate_Center", aligned=True)

    assem.mate_axes(assem_name, c_forearm, c_gripper, "Axis_J5_Pitch", "Axis_J5_Pitch", aligned=True)
    assem.mate_faces(assem_name, c_forearm, c_gripper, plane_name1="Mate_Center", plane_name2="Mate_Center", aligned=True)

    # --- [新增] 夹爪指装配 ---
    # 左夹爪：轴对齐 + 底部贴合顶部 + 中心面对齐(防止绕着轴自转)
    assem.mate_axes(assem_name, c_gripper, c_finger_l, "Axis_Finger_L", "Axis_Main", aligned=True)
    assem.mate_faces(assem_name, c_gripper, c_finger_l, plane_name1="Mate_Top", plane_name2="Mate_Bottom", aligned=True)
    assem.mate_faces(assem_name, c_gripper, c_finger_l, plane_name1="Mate_Center", plane_name2="Mate_Center", aligned=True)

    # 右夹爪：轴对齐 + 底部贴合顶部 + 中心面对齐
    assem.mate_axes(assem_name, c_gripper, c_finger_r, "Axis_Finger_R", "Axis_Main", aligned=True)
    assem.mate_faces(assem_name, c_gripper, c_finger_r, plane_name1="Mate_Top", plane_name2="Mate_Bottom", aligned=True)
    assem.mate_faces(assem_name, c_gripper, c_finger_r, plane_name1="Mate_Center", plane_name2="Mate_Center", aligned=True)

    assem.save_as(assem_path)
    print(f"带倒圆角与双端夹爪的机械臂装配体生成完毕！文件保存至: {assem_path}")

if __name__ == "__main__":
    build_robotic_arm_assembly()