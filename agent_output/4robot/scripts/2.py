from pyswassem import SldWorksApp, PartDoc

def model_link_1():
    """
    建模 Link 1 Arm (第一机械臂)
    - 底部方块: 60x60x20mm，中心孔 phi40mm
    - 中间圆柱: phi30x150mm
    - 顶部方块: 60x60x20mm
    - 顶部销轴: phi10x20mm，沿Y轴正向伸出
    - 接口: 
        - mate_face_bottom (底面)
        - mate_face_top_side_y_plus (顶部方块Y+侧面)
        - bottom_hole_axis (Z轴)
        - top_pin_axis (Y轴)
    """
    
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Link_1_Arm"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    # 定义尺寸 (转换为米)
    block_size = 0.060  # 60 mm
    block_height = 0.020 # 20 mm
    
    cyl_dia = 0.030     # 30 mm
    cyl_len = 0.150     # 150 mm
    
    hole_dia = 0.040    # 40 mm
    
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

    # 3. 切割底部中心孔 (Bottom Hole)
    # 在底部方块顶面 (Z = 0.02) 上创建草图
    plane_bot_top = sw_doc.create_workplane_p_d(plane="XY", offset_val=block_height)
    sketch_bot_hole = sw_doc.insert_sketch_on_plane(plane_bot_top)
    sw_doc.create_circle(
        center_x=0, 
        center_y=0, 
        radius=hole_dia / 2, 
        sketch_ref="XY"
    )
    # 向下切除，贯穿底部方块 (深度至少 0.02m，这里给稍大一点确保切透)
    cut_bot_hole = sw_doc.extrude_cut(sketch_bot_hole, depth=-0.025, single_direction=True)
    print("[Log] Bottom hole cut.")

    # 4. 创建中间圆柱 (Central Cylinder)
    # 在底部方块顶面 (Z = 0.02) 上创建草图
    sketch_cyl = sw_doc.insert_sketch_on_plane(plane_bot_top)
    sw_doc.create_circle(
        center_x=0, 
        center_y=0, 
        radius=cyl_dia / 2, 
        sketch_ref="XY"
    )
    # 向上拉伸 150mm
    extrude_cyl = sw_doc.extrude(sketch_cyl, depth=cyl_len, single_direction=True, merge=True)
    print("[Log] Central cylinder created.")

    # 5. 创建顶部方块 (Top Block)
    # 圆柱顶面高度 Z = 0.02 + 0.15 = 0.17
    z_top_cyl = block_height + cyl_len
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
    # 顶部方块范围: X[-0.03, 0.03], Y[-0.03, 0.03], Z[0.17, 0.19]
    # Y+ 侧面中心点: (0, 0.03, 0.18)
    # 需要在 Y+ 侧面上建草图。由于 API 主要支持基于基准面的偏移，我们需要创建一个平行于 XZ 平面的参考面，或者使用 create_workplane_p_d 基于 "XZ" 或 "ZY"？
    # 注意：create_workplane_p_d 的 plane 参数可以是 "XY"/"XZ"/"ZY"。
    # Y+ 侧面法向是 +Y。平行于 XZ 平面。
    # 我们可以基于 "XZ" 平面偏移 Y 值来创建草图平面吗？
    # 知识库中 create_workplane_p_d(plane: str, offset_val: float)。如果 plane="XZ"，offset_val 应该是 Y 方向的偏移。
    # 让我们尝试基于 "XZ" 平面，偏移 Y=0.03 (即顶部方块 Y+ 面的位置)。
    
    plane_pin_side = sw_doc.create_workplane_p_d(plane="XZ", offset_val=block_size/2) # Y = 0.03
    
    sketch_pin = sw_doc.insert_sketch_on_plane(plane_pin_side)
    # 在 XZ 平面上，圆心应该在 (X=0, Z=0.18) 相对于该局部坐标系？
    # insert_sketch_on_plane 后的坐标系：
    # 如果基于 XZ 平面偏移，通常 U=X, V=Z。
    # 销轴中心在全局坐标 (0, 0.03, 0.18)。
    # 在该草图平面上，X对应全局X，Y(草图内)对应全局Z。
    # 所以 center_x (全局X) = 0, center_y (全局Z) = 0.18。
    sw_doc.create_circle(
        center_x=0, 
        center_y=z_top_cyl + block_height/2, # Z = 0.17 + 0.01 = 0.18
        radius=pin_dia / 2, 
        sketch_ref="XZ" # 参考系需匹配平面类型
    )
    # 向 Y+ 方向拉伸 (即远离 XZ 平面的正方向，取决于封装定义，通常 offset_val 为正表示法向正向)
    # 对于 XZ 平面，法向通常是 +Y。
    extrude_pin = sw_doc.extrude(sketch_pin, depth=pin_len, single_direction=True, merge=True)
    print("[Log] Top pin created.")

    # 7. 倒角处理 (Chamfers)
    # 对两个方块的边缘进行 C2 倒角。
    # 底部方块垂直边: x=±0.03, y=±0.03, z~0.01
    # 顶部方块垂直边: x=±0.03, y=±0.03, z~0.18
    
    chamfer_points_bot = [
        (0.03, 0.03, 0.01),
        (-0.03, 0.03, 0.01),
        (-0.03, -0.03, 0.01),
        (0.03, -0.03, 0.01)
    ]
    
    chamfer_points_top = [
        (0.03, 0.03, 0.18),
        (-0.03, 0.03, 0.18),
        (-0.03, -0.03, 0.18),
        (0.03, -0.03, 0.18)
    ]
    
    try:
        sw_doc.chamfer_edges(on_line_points=chamfer_points_bot, distance=chamfer_dist, angle=45.0)
        sw_doc.chamfer_edges(on_line_points=chamfer_points_top, distance=chamfer_dist, angle=45.0)
        print("[Log] Chamfers applied to blocks.")
    except Exception as e:
        print(f"[Warning] Chamfer failed or skipped: {e}")

    # 8. 创建装配接口 (Interfaces)
    
    # 8.1 面接口: mate_face_bottom (底面, Z=0)
    ref_plane_bottom = sw_doc.create_ref_plane(plane="XY", offset_val=0.0, target_plane_name="mate_face_bottom")
    
    # 8.2 面接口: mate_face_top_side_y_plus (顶部方块 Y+ 侧面, Y=0.03)
    # 这是一个平行于 XZ 的平面
    ref_plane_top_side = sw_doc.create_ref_plane(plane="XZ", offset_val=block_size/2, target_plane_name="mate_face_top_side_y_plus")
    
    # 8.3 轴接口: bottom_hole_axis (Z轴, 穿过原点)
    axis_bottom = sw_doc.create_axis(
        pt1=(0, 0, 0), 
        pt2=(0, 0, 1), 
        axis_name="bottom_hole_axis"
    )
    
    # 8.4 轴接口: top_pin_axis (Y轴, 穿过销轴中心)
    # 销轴中心线: X=0, Z=0.18, 沿 Y 方向
    axis_top_pin = sw_doc.create_axis(
        pt1=(0, 0, 0.18), 
        pt2=(0, 1, 0.18), 
        axis_name="top_pin_axis"
    )
    
    print("[Log] Interfaces created: mate_face_bottom, mate_face_top_side_y_plus, bottom_hole_axis, top_pin_axis")

    # 9. 保存文件
    output_path = "demo_session/assembly_case/parts/link_1.SLDPRT"
    success = sw_doc.save_as(output_path)
    
    if success:
        print(f"[Success] Part saved to {output_path}")
    else:
        print("[Error] Failed to save part.")

if __name__ == "__main__":
    model_link_1()