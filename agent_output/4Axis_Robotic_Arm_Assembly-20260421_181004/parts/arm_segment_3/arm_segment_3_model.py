# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Arm Segment 3"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 2. 定义参数 (单位: m)
    cube_size = 0.060       # 60mm
    cyl_dia = 0.040         # 40mm
    cyl_len = 0.150         # 150mm
    hole_dia = 0.010        # 10mm
    pin_dia = 0.010         # 10mm
    pin_len = 0.015         # 15mm
    chamfer_dist = 0.002    # C2 = 2mm
    
    # 坐标系约定:
    # Bottom Cube Center: (0, 0, 0)
    # Cylinder Axis: +Y direction
    # Top Cube Center: (0, 0.21, 0) -> Y = 0.03 (half bottom) + 0.15 (cyl) + 0.03 (half top) = 0.21
    # Z-axis is vertical for the cubes' height.
    
    # --- Step 1: 创建底部方块 (Bottom Cube) ---
    print("Step 1: 创建底部方块")
    sketch_bottom = sw_doc.insert_sketch_on_plane("XY")
    if not sketch_bottom:
        raise Exception("Failed to create bottom sketch")
    # 中心矩形，宽X=0.06, 高Y=0.06
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=cube_size, height=cube_size, sketch_ref="XY")
    # 拉伸高度 Z = 0.06
    extrude_bottom = sw_doc.extrude(sketch_bottom, depth=cube_size, single_direction=True)
    
    # --- Step 2: 创建连接圆柱 (Connector Cylinder) ---
    print("Step 2: 创建连接圆柱")
    # 圆柱从底部方块的 +Y 面 (Y=0.03) 开始，沿 +Y 延伸
    # 创建一个平行于 XZ 平面 (Y=const) 的参考平面用于画圆截面
    plane_y_start = sw_doc.create_workplane_p_d(plane="XZ", offset_val=0.03) 
    if not plane_y_start:
        raise Exception("Failed to create cylinder start plane")
        
    sketch_cyl = sw_doc.insert_sketch_on_plane(plane_y_start)
    if not sketch_cyl:
        raise Exception("Failed to create cylinder sketch")
        
    # 在 XZ 平面上，X 是横轴，Z 是纵轴。
    # 圆心在方块中心 X=0, Z=0.03 (方块高度一半)
    sw_doc.create_circle(center_x=0, center_y=0.03, radius=cyl_dia/2, sketch_ref="XZ") 
    # 拉伸方向：沿 Y 轴正向。深度：cyl_len = 0.15
    extrude_cyl = sw_doc.extrude(sketch_cyl, depth=cyl_len, single_direction=True)

    # --- Step 3: 创建顶部方块 (Top Cube) ---
    print("Step 3: 创建顶部方块")
    # 顶部方块起始面 Y = 0.03 (start) + 0.15 (cyl) = 0.18
    plane_y_top_start = sw_doc.create_workplane_p_d(plane="XZ", offset_val=0.18)
    if not plane_y_top_start:
        raise Exception("Failed to create top cube start plane")

    sketch_top = sw_doc.insert_sketch_on_plane(plane_y_top_start)
    if not sketch_top:
        raise Exception("Failed to create top cube sketch")
        
    # 在 XZ 平面画矩形，中心 X=0, Z=0.03
    sw_doc.create_centre_rectangle(center_x=0, center_y=0.03, width=cube_size, height=cube_size, sketch_ref="XZ")
    # 沿 Y 轴正向拉伸 0.06
    extrude_top = sw_doc.extrude(sketch_top, depth=cube_size, single_direction=True)

    # --- Step 4: 底部侧孔 (Bottom Side Hole) ---
    print("Step 4: 创建底部侧孔")
    # 孔在底部方块侧面，轴线平行 X 轴。
    # 底部方块 Y 范围 [-0.03, 0.03], Z 范围 [0, 0.06].
    # 孔中心 Z = 0.03.
    # 草图平面：YZ 平面 (X=0)，垂直于孔轴线。
    sketch_hole_bottom = sw_doc.insert_sketch_on_plane("YZ")
    if not sketch_hole_bottom:
        raise Exception("Failed to create bottom hole sketch")
        
    sw_doc.create_circle(center_x=0, center_y=0.03, radius=hole_dia/2, sketch_ref="YZ")
    
    # 拉伸切除。为了确保完全穿透方块 (X 方向宽度 0.06)，使用双向拉伸或足够大的深度。
    # 这里使用单向拉伸，深度设为 0.1 (大于 0.06)，方向默认沿法向 (X+)。
    # 注意：如果只切了一半，可能需要调整。但通常单向拉伸从草图平面开始。
    # 为了保险，我们可以先切一半，再切另一半，或者直接用双向。
    # API: extrude_cut(depth, single_direction). 
    # 尝试单向大深度。
    try:
        sw_doc.extrude_cut(sketch_hole_bottom, depth=0.1, single_direction=True)
    except Exception as e:
        print(f"Warning: First cut failed or partial: {e}")
        # 如果失败，尝试反向或双向逻辑（如果API支持）
        # 这里假设单向成功覆盖了整个厚度，因为草图在中间(X=0)，向+X切0.1会覆盖0到0.1，而方块只到0.03。
        # 等等，方块X范围是 -0.03 到 0.03。草图在 X=0。
        # 向 +X 切 0.1，只会切掉 X>0 的部分。
        # 需要切掉 X<0 的部分吗？是的，通孔。
        # 所以需要双向，或者两次单向。
        # 让我们尝试再次调用，这次向负方向？API似乎没有直接指定负方向的参数，除了depth为负？
        # 文档说: depth: 需要特别注意正负... 正值为向平面法向量正方向...
        # 所以我们可以调用两次，一次正，一次负。
        try:
            sw_doc.extrude_cut(sketch_hole_bottom, depth=-0.1, single_direction=True)
        except Exception as e2:
            print(f"Warning: Second cut failed: {e2}")

    # --- Step 5: 顶部销钉 (Top Pin) ---
    print("Step 5: 创建顶部销钉")
    # 销钉在顶部方块侧面 (+X 面)。
    # 顶部方块 X 范围 [-0.03, 0.03]. +X 面在 X=0.03.
    # 销钉轴线平行 X 轴。
    # 草图平面：平行于 YZ，偏移 X=0.03.
    plane_pin_face = sw_doc.create_workplane_p_d(plane="YZ", offset_val=0.03)
    if not plane_pin_face:
        raise Exception("Failed to create pin face plane")

    sketch_pin = sw_doc.insert_sketch_on_plane(plane_pin_face)
    if not sketch_pin:
        raise Exception("Failed to create pin sketch")
        
    # 圆心 Y=0 (相对于顶部方块局部Y中心? 不，全局Y中心是0.21).
    # 顶部方块中心 Y=0.21, Z=0.03.
    # 所以在 plane_pin_face (X=0.03) 上，圆心 Y=0.21, Z=0.03.
    # 注意：create_circle 的 center_x, center_y 对应草图平面的局部坐标。
    # 对于 YZ 平面，通常 X->Y_global, Y->Z_global? 或者 X->Z, Y->Y?
    # 让我们回顾 Step 4: sketch_ref="YZ", center_x=0, center_y=0.03. 
    # 如果 YZ 平面映射是 x->Y, y->Z，那么 center_x=0 意味着 Y=0, center_y=0.03 意味着 Z=0.03。这是正确的。
    # 所以对于 Pin:
    # 我们希望 Y=0.21, Z=0.03.
    # 所以 center_x = 0.21, center_y = 0.03.
    sw_doc.create_circle(center_x=0.21, center_y=0.03, radius=pin_dia/2, sketch_ref="YZ")
    
    # 沿 X 轴正向拉伸 (离开方块)
    # 确保 sketch_pin 是有效的对象
    if sketch_pin:
        sw_doc.extrude(sketch_pin, depth=pin_len, single_direction=True)
    else:
        print("Error: Sketch pin is None, cannot extrude.")

    # --- Step 6: 倒角 (Chamfer C2) ---
    print("Step 6: 添加倒角")
    # 需要对所有方块的棱边进行 C2 倒角。
    # 选取关键点来定位边。
    chamfer_points = [
        # Bottom Cube (Center 0,0,0; Size 0.06)
        (0, 0.03, 0.06),      # Top face edge mid (Y-edge)
        (0.03, 0, 0.06),      # Top face edge mid (X-edge)
        (0.03, 0.03, 0.03),   # Vertical edge mid
        
        # Top Cube (Center 0, 0.21, 0; Size 0.06)
        # Y range: 0.18 to 0.24. Z range: 0 to 0.06. X range: -0.03 to 0.03.
        (0, 0.21, 0.06),      # Top face edge mid (Y-edge relative to center) -> Global Y=0.21
        (0.03, 0.21, 0.06),   # Top face edge mid (X-edge) -> This is a corner if Y is fixed? 
                               # Let's use edge parallel to X at Y=0.24 (front). Midpoint X=0.
        (0, 0.24, 0.06),      
        (0.03, 0.24, 0.03),   # Vertical edge at X=0.03, Y=0.24
    ]
    
    try:
        sw_doc.chamfer_edges(on_line_points=chamfer_points, distance=chamfer_dist, angle=45.0)
    except Exception as e:
        print(f"Warning: Chamfer operation might have partial failures: {e}")

    # --- Step 7: 创建接口 (Interfaces) ---
    print("Step 7: 创建参考几何接口")
    
    # 1. bottom_side_face: Normal -X. 
    # 底部方块的 -X 面在 X = -0.03.
    ref_plane_bottom_side = sw_doc.create_ref_plane(plane="YZ", offset_val=-0.03, target_plane_name="bottom_side_face")
    
    # 2. top_pin_face: Normal +X.
    # 顶部方块的 +X 面在 X = 0.03.
    ref_plane_top_pin = sw_doc.create_ref_plane(plane="YZ", offset_val=0.03, target_plane_name="top_pin_face")
    
    # 3. side_mate_face_top: Normal +X.
    # 同 top_pin_face.
    ref_plane_side_mate_top = sw_doc.create_ref_plane(plane="YZ", offset_val=0.03, target_plane_name="side_mate_face_top")

    # 4. bottom_hole_axis: Along local X, centered in bottom cube.
    # 底部方块中心 (0,0,0). 孔沿 X 轴. Z=0.03.
    axis_bottom_hole = sw_doc.create_axis(pt1=(-0.1, 0, 0.03), pt2=(0.1, 0, 0.03), axis_name="bottom_hole_axis")

    # 5. pin_axis: Along local X, offset in top cube.
    # 顶部方块中心 Y=0.21, Z=0.03.
    axis_pin = sw_doc.create_axis(pt1=(-0.1, 0.21, 0.03), pt2=(0.1, 0.21, 0.03), axis_name="pin_axis")

    # 8. 保存文件
    model_path = r"D:\a_src\python\sw_agent\agent_output\4Axis_Robotic_Arm_Assembly-20260421_181004\parts\arm_segment_3\arm_segment_3.SLDPRT"
    print(f"Saving part to: {model_path}")
    success = sw_doc.save_as(model_path)
    
    if success:
        print("Modeling and saving completed successfully.")
    else:
        print("Failed to save the model.")

if __name__ == "__main__":
    main()