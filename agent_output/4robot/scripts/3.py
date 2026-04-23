from pyswassem import SldWorksApp, PartDoc

def model_link_2():
    """
    建模 Link 2 Arm (第二机械臂)
    - 底部方块: 60x60x20mm，侧面(Y-)孔 phi10.2mm
    - 中间圆柱: phi30x120mm
    - 顶部方块: 60x60x20mm
    - 顶部销轴: phi10x20mm，沿Y轴正向伸出
    - 接口: 
        - mate_face_bottom_side_y_minus (底部方块Y-侧面)
        - mate_face_top_side_y_plus (顶部方块Y+侧面)
        - bottom_hole_axis (Y轴，穿过底部孔中心)
        - top_pin_axis (Y轴，穿过顶部销轴中心)
    """
    
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Link_2_Arm"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    # 定义尺寸 (转换为米)
    block_size = 0.060  # 60 mm
    block_height = 0.020 # 20 mm
    
    cyl_dia = 0.030     # 30 mm
    cyl_len = 0.120     # 120 mm
    
    hole_dia = 0.0102   # 10.2 mm (Clearance fit for 10mm pin)
    
    pin_dia = 0.010     # 10 mm
    pin_len = 0.020     # 20 mm
    
    chamfer_dist = 0.002 # C2 = 2mm
    
    print(f"[Log] Starting modeling for {part_name}")

    # 2. 创建底部方块 (Bottom Block)
    # 在 XY 平面绘制中心矩形
    sketch_bot_block = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(
        center_x=0, 
        center_y=0, 
        width=block_size, 
        height=block_size, 
        sketch_ref="XY"
    )
    # 向上拉伸 20mm
    extrude_bot_block = sw_doc.extrude(sketch_bot_block, depth=block_height, single_direction=True, merge=True)
    print("[Log] Bottom block created.")

    # 3. 切割底部侧面孔 (Bottom Side Hole)
    # 孔位于 Y- 侧面。
    # 底部方块范围: X[-0.03, 0.03], Y[-0.03, 0.03], Z[0, 0.02]
    # Y- 侧面中心点: (0, -0.03, 0.01)
    # 需要在 Y- 侧面上建草图。平行于 XZ 平面。
    # 基于 "XZ" 平面，偏移 Y = -0.03 (即 block_size/2 的负值)
    
    plane_bot_hole = sw_doc.create_workplane_p_d(plane="XZ", offset_val=-block_size/2)
    
    sketch_bot_hole = sw_doc.insert_sketch_on_plane(plane_bot_hole)
    # 在 XZ 平面上，圆心应该在 (X=0, Z=0.01) 相对于该局部坐标系
    # center_x (全局X) = 0, center_y (全局Z) = 0.01
    sw_doc.create_circle(
        center_x=0, 
        center_y=block_height/2, # Z = 0.01
        radius=hole_dia / 2, 
        sketch_ref="XZ"
    )
    # 向 Y+ 方向切除 (即朝向实体内部)，贯穿整个方块宽度 (0.06m)
    # 注意：extrude_cut 的 depth 正负取决于法线方向。
    # XZ 平面法线通常指向 +Y。我们要切向 +Y 方向（进入方块）。
    cut_bot_hole = sw_doc.extrude_cut(sketch_bot_hole, depth=block_size, single_direction=True)
    print("[Log] Bottom side hole cut.")

    # 4. 创建中间圆柱 (Central Cylinder)
    # 在底部方块顶面 (Z = 0.02) 上创建草图
    z_bot_top = block_height
    plane_cyl_base = sw_doc.create_workplane_p_d(plane="XY", offset_val=z_bot_top)
    
    sketch_cyl = sw_doc.insert_sketch_on_plane(plane_cyl_base)
    sw_doc.create_circle(
        center_x=0, 
        center_y=0, 
        radius=cyl_dia / 2, 
        sketch_ref="XY"
    )
    # 向上拉伸 120mm
    extrude_cyl = sw_doc.extrude(sketch_cyl, depth=cyl_len, single_direction=True, merge=True)
    print("[Log] Central cylinder created.")

    # 5. 创建顶部方块 (Top Block)
    # 圆柱顶面高度 Z = 0.02 + 0.12 = 0.14
    z_top_cyl = z_bot_top + cyl_len
    plane_top_cyl = sw_doc.create_workplane_p_d(plane="XY", offset_val=z_top_cyl)
    
    sketch_top_block = sw_doc.insert_sketch_on_plane(plane_top_cyl)
    sw_doc.create_centre_rectangle(
        center_x=0, 
        center_y=0, 
        width=block_size, 
        height=block_size, 
        sketch_ref="XY"
    )
    # 向上拉伸 20mm
    extrude_top_block = sw_doc.extrude(sketch_top_block, depth=block_height, single_direction=True, merge=True)
    print("[Log] Top block created.")

    # 6. 创建顶部销轴 (Top Pin)
    # 销轴位于顶部方块的 Y+ 侧面。
    # 顶部方块范围: X[-0.03, 0.03], Y[-0.03, 0.03], Z[0.14, 0.16]
    # Y+ 侧面中心点: (0, 0.03, 0.15)
    # 基于 "XZ" 平面，偏移 Y = 0.03
    
    plane_pin_side = sw_doc.create_workplane_p_d(plane="XZ", offset_val=block_size/2)
    
    sketch_pin = sw_doc.insert_sketch_on_plane(plane_pin_side)
    # 圆心在全局坐标 (0, 0.03, 0.15)。
    # 在该草图平面上，X对应全局X，Y(草图内)对应全局Z。
    # center_x (全局X) = 0, center_y (全局Z) = 0.15
    sw_doc.create_circle(
        center_x=0, 
        center_y=z_top_cyl + block_height/2, # Z = 0.14 + 0.01 = 0.15
        radius=pin_dia / 2, 
        sketch_ref="XZ"
    )
    # 向 Y+ 方向拉伸 (远离 XZ 平面的正方向)
    extrude_pin = sw_doc.extrude(sketch_pin, depth=pin_len, single_direction=True, merge=True)
    print("[Log] Top pin created.")

    # 7. 倒角处理 (Chamfers)
    # 对两个方块的边缘进行 C2 倒角。
    # 底部方块垂直边: x=±0.03, y=±0.03, z~0.01
    # 顶部方块垂直边: x=±0.03, y=±0.03, z~0.15
    
    chamfer_points_bot = [
        (0.03, 0.03, 0.01),
        (-0.03, 0.03, 0.01),
        (-0.03, -0.03, 0.01),
        (0.03, -0.03, 0.01)
    ]
    
    chamfer_points_top = [
        (0.03, 0.03, 0.15),
        (-0.03, 0.03, 0.15),
        (-0.03, -0.03, 0.15),
        (0.03, -0.03, 0.15)
    ]
    
    try:
        sw_doc.chamfer_edges(on_line_points=chamfer_points_bot, distance=chamfer_dist, angle=45.0)
        sw_doc.chamfer_edges(on_line_points=chamfer_points_top, distance=chamfer_dist, angle=45.0)
        print("[Log] Chamfers applied to blocks.")
    except Exception as e:
        print(f"[Warning] Chamfer failed or skipped: {e}")

    # 8. 创建装配接口 (Interfaces)
    
    # 8.1 面接口: mate_face_bottom_side_y_minus (底部方块 Y- 侧面, Y=-0.03)
    ref_plane_bot_side = sw_doc.create_ref_plane(plane="XZ", offset_val=-block_size/2, target_plane_name="mate_face_bottom_side_y_minus")
    
    # 8.2 面接口: mate_face_top_side_y_plus (顶部方块 Y+ 侧面, Y=0.03)
    ref_plane_top_side = sw_doc.create_ref_plane(plane="XZ", offset_val=block_size/2, target_plane_name="mate_face_top_side_y_plus")
    
    # 8.3 轴接口: bottom_hole_axis (Y轴, 穿过底部孔中心)
    # 孔中心线: X=0, Z=0.01, 沿 Y 方向
    axis_bottom_hole = sw_doc.create_axis(
        pt1=(0, -1, 0.01), 
        pt2=(0, 1, 0.01), 
        axis_name="bottom_hole_axis"
    )
    
    # 8.4 轴接口: top_pin_axis (Y轴, 穿过顶部销轴中心)
    # 销轴中心线: X=0, Z=0.15, 沿 Y 方向
    axis_top_pin = sw_doc.create_axis(
        pt1=(0, -1, 0.15), 
        pt2=(0, 1, 0.15), 
        axis_name="top_pin_axis"
    )
    
    print("[Log] Interfaces created: mate_face_bottom_side_y_minus, mate_face_top_side_y_plus, bottom_hole_axis, top_pin_axis")

    # 9. 保存文件
    output_path = "demo_session/assembly_case/parts/link_2.SLDPRT"
    success = sw_doc.save_as(output_path)
    
    if success:
        print(f"[Success] Part saved to {output_path}")
    else:
        print("[Error] Failed to save part.")

if __name__ == "__main__":
    model_link_2()