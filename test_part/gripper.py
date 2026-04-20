from pyswassem import SldWorksApp, PartDoc, AssemDoc

def build_gripper_assembly():
    sw = SldWorksApp()
    workdir = sw.create_workdir("gripper_assembly_job")

    base_path = sw.get_part_path(workdir, "gripper_base")
    finger_path = sw.get_part_path(workdir, "gripper_finger")
    assem_path = sw.get_assembly_path(workdir, "gripper_assem")

    # ==========================================
    # 1. 制作夹爪基座 (Gripper Base)
    # 尺寸: 100mm(X) x 40mm(Z) x 20mm(Y)
    # ==========================================
    base_part = PartDoc(sw.createAndActivate_sw_part("gripper_base"))
    
    # 基座主实体
    sk_base = base_part.insert_sketch_on_plane("XZ")
    base_part.create_centre_rectangle(
        center_x=0.0, center_y=0.0, 
        width=0.1, height=0.04, 
        sketch_ref="XZ"
    )
    base_part.extrude(sk_base, depth=0.02, single_direction=True, merge=True)

    # 挖 2 个用于安装手指的铰链孔 (孔径 10mm)
    sk_holes = base_part.insert_sketch_on_plane("XZ")
    pivot_coords = [(-0.03, 0.0), (0.03, 0.0)]
    for x, z in pivot_coords:
        base_part.create_circle(x, z, radius=0.005, sketch_ref="XZ")
    base_part.extrude_cut(sk_holes, depth=0.03, single_direction=True)

    # 为铰链孔建立装配轴 (-Y -> +Y)
    base_part.create_axis((-0.03, -0.1, 0.0), (-0.03, 0.1, 0.0), "Axis_Pivot_L")
    base_part.create_axis((0.03, -0.1, 0.0), (0.03, 0.1, 0.0), "Axis_Pivot_R")
        
    # 创建命名基准面，高度在基座顶面(Y=0.02处)，专用于装配接触
    base_part.create_ref_plane("XZ", offset_val=0.02, target_plane_name="MatePlane_Contact")
    base_part.save_as(base_path)

    # ==========================================
    # 2. 制作通用夹爪指 (Gripper Finger)
    # 尺寸: 20mm(X) x 80mm(Z) x 10mm(Y)
    # ==========================================
    finger_part = PartDoc(sw.createAndActivate_sw_part("gripper_finger"))
    
    # 手指主实体
    sk_finger = finger_part.insert_sketch_on_plane("XZ")
    finger_part.create_centre_rectangle(
        center_x=0.0, center_y=0.0, 
        width=0.02, height=0.08, 
        sketch_ref="XZ"
    )
    finger_part.extrude(sk_finger, depth=0.01, single_direction=True, merge=True)

    # 在手指尾部挖铰链孔 (Z=-0.025处，留出足够的前端抓取长度)
    sk_finger_hole = finger_part.insert_sketch_on_plane("XZ")
    finger_part.create_circle(0.0, -0.025, radius=0.005, sketch_ref="XZ")
    finger_part.extrude_cut(sk_finger_hole, depth=0.02, single_direction=True)

    # 建立装配轴 (-Y -> +Y)，位置对齐手指上的孔心
    finger_part.create_axis((0.0, -0.1, -0.025), (0.0, 0.1, -0.025), axis_name="Axis_Main")
    
    # 创建同名基准面，高度在手指底面(Y=0处)，用于和基座接触
    finger_part.create_ref_plane("XZ", offset_val=0.0, target_plane_name="MatePlane_Contact")
    finger_part.save_as(finger_path)

    # ==========================================
    # 3. 夹爪组装 (Assembly)
    # ==========================================
    assem_name = "gripper_assem"
    assem = AssemDoc(sw.createAndActivate_sw_assembly(assem_name))

    # 导入基座作为固定件
    comp_base = assem.add_component(base_path, 0, 0, 0)

    # 导入并装配左指 (复用 finger_part)
    comp_finger_l = assem.add_component(finger_path, -0.05, 0.05, 0)
    # 同轴与面配合
    assem.mate_axes(assem_name, comp_base, comp_finger_l, "Axis_Pivot_L", "Axis_Main", aligned=True)
    assem.mate_faces(assem_name, comp_base, comp_finger_l, plane_name="MatePlane_Contact", aligned=True)

    # 导入并装配右指 (再次复用 finger_part)
    comp_finger_r = assem.add_component(finger_path, 0.05, 0.05, 0)
    # 同轴与面配合
    assem.mate_axes(assem_name, comp_base, comp_finger_r, "Axis_Pivot_R", "Axis_Main", aligned=True)
    assem.mate_faces(assem_name, comp_base, comp_finger_r, plane_name="MatePlane_Contact", aligned=True)

    assem.save_as(assem_path)
    print(f"夹爪装配体已成功生成并保存至: {assem_path}")

if __name__ == "__main__":
    build_gripper_assembly()