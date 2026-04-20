from pyswassem import SldWorksApp, PartDoc, AssemDoc

def build_slot_screw_assembly():
    sw = SldWorksApp()
    workdir = sw.create_workdir("slot_screw_job")

    bottom_path = sw.get_part_path(workdir, "bottom_block")
    top_path = sw.get_part_path(workdir, "top_block")
    screw_path = sw.get_part_path(workdir, "screw")
    assem_path = sw.get_assembly_path(workdir, "final_assembly")

    # ==========================================
    # 1. 下层方块 (Bottom Block)
    # ==========================================
    bottom_part = PartDoc(sw.createAndActivate_sw_part("bottom_block"))
    
    # 主体: 100x100, 向上拉伸 50mm
    sk_bottom = bottom_part.insert_sketch_on_plane("XZ")
    bottom_part.create_centre_rectangle(0, 0, 0.1, 0.1, sketch_ref="XZ")
    bottom_part.extrude(sk_bottom, depth=0.05, single_direction=True, merge=True)

    # 螺孔
    sk_hole_plane = bottom_part.create_workplane_p_d("XZ", offset_val=0.05) # 在顶部创建工作面
    sk_hole = bottom_part.insert_sketch_on_plane(sk_hole_plane)
    bottom_part.create_circle(0, 0, radius=0.005, sketch_ref="XZ") # 草图参考建议与基础面一致或省略
    bottom_part.extrude_cut(sk_hole, depth=-0.05)

    # [基准预埋]
    # 中心主轴 (-Y -> +Y)
    bottom_part.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_Main")
    # 边缘防转轴 (位于 X=0.05 的棱上, -Y -> +Y)
    bottom_part.create_axis((0.05, -0.1, 0), (0.05, 0.1, 0), "Axis_Edge")
    # 顶面接触基准面 (Y=0.05)
    bottom_part.create_ref_plane("XZ", offset_val=0.05, target_plane_name="Mate_Top")
    
    bottom_part.save_as(bottom_path)

    # ==========================================
    # 2. 上层带槽与沉头孔方块 (Top Block)
    # ==========================================
    top_part = PartDoc(sw.createAndActivate_sw_part("top_block"))
    
    # 主体: 120x120, 向上拉伸 30mm
    sk_top = top_part.insert_sketch_on_plane("XZ")
    top_part.create_centre_rectangle(0, 0, 0.12, 0.12, sketch_ref="XZ")
    top_part.extrude(sk_top, depth=0.03, single_direction=True, merge=True)

    # 挖槽: 底部 100x100, 向上切除 10mm (深度0.01)
    sk_groove = top_part.insert_sketch_on_plane("XZ")
    top_part.create_centre_rectangle(0, 0, 0.1, 0.1, sketch_ref="XZ")
    top_part.extrude_cut(sk_groove, depth=0.01, single_direction=True)

    # 螺钉沉头大孔: 在顶部 (Y=0.03) 挖半径 10mm 的圆，向下切除 5mm
    wp_top = top_part.create_workplane_p_d("XZ", offset_val=0.03)
    sk_cb_head = top_part.insert_sketch_on_plane(wp_top)
    top_part.create_circle(0, 0, radius=0.01, sketch_ref="XZ") # 草图参考建议与基础面一致或省略
    top_part.extrude_cut(sk_cb_head, depth=-0.005, single_direction=True) # 负值向下切除

    # 螺钉穿透小孔: 在沉头底面 (Y=0.025) 挖半径 5mm 的圆，向下贯穿剩余的 25mm
    wp_cb_bottom = top_part.create_workplane_p_d("XZ", offset_val=0.025)
    sk_thru_hole = top_part.insert_sketch_on_plane(wp_cb_bottom)
    top_part.create_circle(0, 0, radius=0.005, sketch_ref="XZ")
    top_part.extrude_cut(sk_thru_hole, depth=-0.025, single_direction=True)

    # [基准预埋]
    # 中心主轴与防转轴 (-Y -> +Y)
    top_part.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_Main")
    top_part.create_axis((0.05, -0.1, 0), (0.05, 0.1, 0), "Axis_Edge")
    # 槽内顶面基准 (Y=0.01)
    top_part.create_ref_plane("XZ", offset_val=0.01, target_plane_name="Mate_Groove_Roof")
    # 沉头孔底面基准 (Y=0.025，即 0.03 - 0.005)
    top_part.create_ref_plane("XZ", offset_val=0.025, target_plane_name="Mate_Hole_Bottom")

    top_part.save_as(top_path)

    # ==========================================
    # 3. 螺钉 (Screw)
    # ==========================================
    screw_part = PartDoc(sw.createAndActivate_sw_part("screw"))
    
    # 螺钉头: 半径 10-0.5 mm, 向上拉伸 5mm (从 Y=0 到 Y=0.005)
    sk_head = screw_part.insert_sketch_on_plane("XZ")
    screw_part.create_circle(0, 0, radius=0.0095, sketch_ref="XZ")
    screw_part.extrude(sk_head, depth=0.005, single_direction=True, merge=True)

    # 螺钉杆: 半径 5mm, 向下拉伸 40mm (从 Y=0 到 Y=-0.04)
    sk_body = screw_part.insert_sketch_on_plane("XZ")
    screw_part.create_circle(0, 0, radius=0.005, sketch_ref="XZ")
    screw_part.extrude(sk_body, depth=-0.04, single_direction=True, merge=True)

    # 顶部切除一字
    wp_head = screw_part.create_workplane_p_d("XZ", offset_val=0.005)
    sk_cross = screw_part.insert_sketch_on_plane(wp_head)
    screw_part.create_centre_rectangle(0, 0, 0.010, 0.001, sketch_ref="XZ")
    screw_part.extrude_cut(sk_cross, depth=-0.001)


    # [基准预埋]
    screw_part.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_Main")
    # 螺钉头底面基准 (Y=0)
    screw_part.create_ref_plane("XZ", offset_val=0.0, target_plane_name="Mate_Head_Bottom")

    screw_part.save_as(screw_path)

    # ==========================================
    # 4. 装配 (Assembly)
    # ==========================================
    assem_name = "final_assembly"
    assem = AssemDoc(sw.createAndActivate_sw_assembly(assem_name))

    # 导入组件
    comp_bottom = assem.add_component(bottom_path, 0, 0, 0)
    comp_top = assem.add_component(top_path, 0, 0.1, 0) # 初始稍微抬高
    comp_screw = assem.add_component(screw_path, 0, 0.2, 0)

    # --- 装配 1：下层方块 与 上层方块 ---
    # 1. 约束中心轴 (对齐)
    assem.mate_axes(assem_name, comp_bottom, comp_top, "Axis_Main", "Axis_Main", aligned=True)
    # 2. 约束边缘防转轴 (对齐，彻底锁死旋转自由度)
    assem.mate_axes(assem_name, comp_bottom, comp_top, "Axis_Edge", "Axis_Edge", aligned=True)
    # 3. 约束高度 (下块顶部 贴 上块槽顶)
    assem.mate_faces(assem_name, comp_bottom, comp_top, "Mate_Top", "Mate_Groove_Roof", aligned=True)

    # --- 装配 2：上层方块 与 螺钉 ---
    # 1. 约束中心轴
    assem.mate_axes(assem_name, comp_top, comp_screw, "Axis_Main", "Axis_Main", aligned=True)
    # 2. 约束高度 (沉头孔底面 贴 螺丝头底面)
    assem.mate_faces(assem_name, comp_top, comp_screw, "Mate_Hole_Bottom", "Mate_Head_Bottom", aligned=True)

    assem.save_as(assem_path)
    print(f"装配成功！组合体已保存至: {assem_path}")

if __name__ == "__main__":
    build_slot_screw_assembly()