from pyswassem import SldWorksApp, PartDoc, AssemDoc

def build_table_assembly():
    sw = SldWorksApp()
    workdir = sw.create_workdir("table_assembly_job")

    # 路径生成
    top_path = sw.get_part_path(workdir, "tabletop")
    leg_path = sw.get_part_path(workdir, "tableleg")
    screw_path = sw.get_part_path(workdir, "screw")
    assem_path = sw.get_assembly_path(workdir, "table_assem")

    # ==========================================
    # 1. 制作桌面 (Tabletop)
    # ==========================================
    top_part = PartDoc(sw.createAndActivate_sw_part("tabletop"))
    
    # 桌面轮廓：1m x 0.6m
    sk_top = top_part.insert_sketch_on_plane("XZ")
    top_part.create_centre_rectangle(
        center_x=0.0, center_y=0.0, 
        width=1.0, height=0.6, 
        sketch_ref="XZ"
    )
    # 向上拉伸 30mm
    top_part.extrude(sk_top, depth=0.03, single_direction=True, merge=True)

    # 挖 4 个螺丝通孔
    sk_holes = top_part.insert_sketch_on_plane("XZ")
    hole_coords = [(0.4, 0.2), (-0.4, 0.2), (0.4, -0.2), (-0.4, -0.2)]
    for x, z in hole_coords:
        top_part.create_circle(x, z, radius=0.005, sketch_ref="XZ")
    # 确保切透
    top_part.extrude_cut(sk_holes, depth=0.04, single_direction=True)

    # 为 4 个孔建立向上的装配轴 (-Y -> +Y)
    for i, (x, z) in enumerate(hole_coords, 1):
        top_part.create_axis(
            pt1=(x, -0.1, z), 
            pt2=(x, 0.1, z), 
            axis_name=f"Axis_Hole_{i}"
        )
        
    # 创建一个命名基准面，用于定位螺丝头部 (位于桌面顶部 Y=0.03 处)
    top_part.create_ref_plane("XZ", offset_val=0.03, target_plane_name="MatePlane_Screw")

    top_part.save_as(top_path)

    # ==========================================
    # 2. 制作桌腿 (Table Leg)
    # ==========================================
    leg_part = PartDoc(sw.createAndActivate_sw_part("tableleg"))
    
    # 桌腿轮廓：直径 40mm
    sk_leg = leg_part.insert_sketch_on_plane("XZ")
    leg_part.create_circle(0.0, 0.0, radius=0.02, sketch_ref="XZ")
    # 向下拉伸 700mm (-Y方向)
    leg_part.extrude(sk_leg, depth=-0.7, single_direction=True, merge=True)

    # 桌腿顶部挖螺丝孔
    sk_leg_hole = leg_part.insert_sketch_on_plane("XZ")
    leg_part.create_circle(0.0, 0.0, radius=0.005, sketch_ref="XZ")
    # 向下切除 50mm
    leg_part.extrude_cut(sk_leg_hole, depth=-0.05, single_direction=True)

    # 建立向上的装配轴 (-Y -> +Y)
    leg_part.create_axis((0.0, -0.8, 0.0), (0.0, 0.8, 0.0), axis_name="Axis_Main")

    leg_part.save_as(leg_path)

    # ==========================================
    # 3. 制作螺丝 (Screw)
    # ==========================================
    screw_part = PartDoc(sw.createAndActivate_sw_part("screw"))
    
    # 螺丝头：直径 20mm，向上拉伸 5mm
    sk_screw_head = screw_part.insert_sketch_on_plane("XZ")
    screw_part.create_circle(0.0, 0.0, radius=0.01, sketch_ref="XZ")
    screw_part.extrude(sk_screw_head, depth=0.005, single_direction=True, merge=True)

    # 螺丝杆：直径 10mm，向下拉伸 50mm
    sk_screw_body = screw_part.insert_sketch_on_plane("XZ")
    screw_part.create_circle(0.0, 0.0, radius=0.005, sketch_ref="XZ")
    screw_part.extrude(sk_screw_body, depth=-0.05, single_direction=True, merge=True)

    # 建立向上的装配轴 (-Y -> +Y)
    screw_part.create_axis((0.0, -0.1, 0.0), (0.0, 0.1, 0.0), axis_name="Axis_Main")
    
    # 创建同名基准面，用于和桌面的顶部配合 (位于螺丝本体 Y=0 处)
    screw_part.create_ref_plane("XZ", offset_val=0.0, target_plane_name="MatePlane_Screw")

    screw_part.save_as(screw_path)

    # ==========================================
    # 4. 组装 (Assembly)
    # ==========================================
    assem_name = "table_assem"
    assem = AssemDoc(sw.createAndActivate_sw_assembly(assem_name))

    # 导入桌面作为基准件
    comp_top = assem.add_component(top_path, 0, 0, 0)

    # 导入并装配 4 条桌腿
    for i, (x, z) in enumerate(hole_coords, 1):
        # 初始位置稍微错开，方便 SW 引擎计算
        comp_leg = assem.add_component(leg_path, x, -0.5, z)
        
        # 1) 同轴配合：桌腿的 Axis_Main 对齐 桌面的 Axis_Hole_i
        assem.mate_axes(assem_name, comp_top, comp_leg, f"Axis_Hole_{i}", "Axis_Main", aligned=True)
        # 2) 表面配合：桌面的底部(Y=0) 贴合 桌腿的顶部(Y=0)
        assem.mate_faces(assem_name, comp_top, comp_leg, plane_name="上视基准面", aligned=True)

    # 导入并装配 4 颗螺丝
    for i, (x, z) in enumerate(hole_coords, 1):
        comp_screw = assem.add_component(screw_path, x, 0.1, z)
        
        # 1) 同轴配合：螺丝的 Axis_Main 对齐 桌面的 Axis_Hole_i
        assem.mate_axes(assem_name, comp_top, comp_screw, f"Axis_Hole_{i}", "Axis_Main", aligned=True)
        # 2) 表面配合：螺丝的底切面 贴合 桌面的顶端命名面
        assem.mate_faces(assem_name, comp_top, comp_screw, plane_name="MatePlane_Screw", aligned=True)

    assem.save_as(assem_path)
    print(f"桌子装配体已成功生成并保存至: {assem_path}")

if __name__ == "__main__":
    build_table_assembly()