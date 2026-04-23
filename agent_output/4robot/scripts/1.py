from pyswassem import SldWorksApp, PartDoc

def model_base_plate():
    """
    建模 Base Plate (底座)
    - 主体: 200x200x100mm 长方体
    - 顶部凸台1: phi80x20mm
    - 顶部凸台2: phi40x30mm
    - 接口: 
        - mount_face_bottom (底面)
        - interface_face_top_stage1 (第一级凸台顶面)
        - main_axis_z (Z轴旋转中心)
    """
    
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Base_Plate"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    # 定义尺寸 (转换为米)
    base_len = 0.200  # 200 mm
    base_wid = 0.200  # 200 mm
    base_hgt = 0.100  # 100 mm
    
    boss1_dia = 0.080 # 80 mm
    boss1_hgt = 0.020 # 20 mm
    
    boss2_dia = 0.040 # 40 mm
    boss2_hgt = 0.030 # 30 mm
    
    chamfer_dist = 0.002 # C2 = 2mm
    
    print(f"[Log] Starting modeling for {part_name}")

    # 2. 创建主体基座 (Base Block)
    # 在 XY 平面绘制中心矩形
    sketch_base = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(
        center_x=0, 
        center_y=0, 
        width=base_len, 
        height=base_wid, 
        sketch_ref="XY"
    )
    # 向上拉伸 100mm
    extrude_base = sw_doc.extrude(sketch_base, depth=base_hgt, single_direction=True, merge=True)
    print("[Log] Base block created.")

    # 3. 创建第一级凸台 (Boss Stage 1)
    # 需要在基座顶面 (Z = 0.1) 上创建草图。
    # 由于 API 限制，我们通常通过偏移平面或直接指定平面名称来操作。
    # 这里假设我们可以基于 "XY" 平面偏移，或者如果封装支持直接选择面，则更佳。
    # 根据知识库，create_workplane_p_d 可以创建偏移平面。
    plane_boss1 = sw_doc.create_workplane_p_d(plane="XY", offset_val=base_hgt)
    
    sketch_boss1 = sw_doc.insert_sketch_on_plane(plane_boss1)
    sw_doc.create_circle(
        center_x=0, 
        center_y=0, 
        radius=boss1_dia / 2, 
        sketch_ref="XY" # 注意：虽然是在偏移平面上，但参考系通常仍沿用主基准面的投影逻辑，或需确认封装行为。此处按常规XY处理圆心定位。
    )
    # 向上拉伸 20mm
    extrude_boss1 = sw_doc.extrude(sketch_boss1, depth=boss1_hgt, single_direction=True, merge=True)
    print("[Log] Boss Stage 1 created.")

    # 4. 创建第二级凸台 (Boss Stage 2)
    # 在第一级凸台顶面 (Z = 0.1 + 0.02 = 0.12) 上创建草图
    plane_boss2 = sw_doc.create_workplane_p_d(plane="XY", offset_val=base_hgt + boss1_hgt)
    
    sketch_boss2 = sw_doc.insert_sketch_on_plane(plane_boss2)
    sw_doc.create_circle(
        center_x=0, 
        center_y=0, 
        radius=boss2_dia / 2, 
        sketch_ref="XY"
    )
    # 向上拉伸 30mm
    extrude_boss2 = sw_doc.extrude(sketch_boss2, depth=boss2_hgt, single_direction=True, merge=True)
    print("[Log] Boss Stage 2 created.")

    # 5. 倒角处理 (Chamfers)
    # 设计规则要求 C2 倒角。为了稳定性，我们对基座的垂直边进行倒角。
    # 基座垂直边位于 x=±0.1, y=±0.1, z从0到0.1
    # 选取四个角上的点来定位边
    chamfer_points = [
        (0.1, 0.1, 0.05),   # Corner 1
        (-0.1, 0.1, 0.05),  # Corner 2
        (-0.1, -0.1, 0.05), # Corner 3
        (0.1, -0.1, 0.05)   # Corner 4
    ]
    try:
        sw_doc.chamfer_edges(on_line_points=chamfer_points, distance=chamfer_dist, angle=45.0)
        print("[Log] Chamfers applied to base edges.")
    except Exception as e:
        print(f"[Warning] Chamfer failed or skipped: {e}")

    # 6. 创建装配接口 (Interfaces)
    
    # 6.1 面接口: mount_face_bottom (底面, Z=0)
    # 使用 create_ref_plane 创建命名参考面，虽然底面就是 XY 平面，但为了语义清晰，创建一个重合的参考面或重命名
    # 实际上，XY 平面本身就可以作为参考。如果需要显式命名，可以尝试创建偏移为0的平面并重命名，或者直接依赖全局坐标系。
    # 这里我们创建一个偏移为0的平面并命名为 mount_face_bottom，以便装配时明确引用。
    ref_plane_bottom = sw_doc.create_ref_plane(plane="XY", offset_val=0.0, target_plane_name="mount_face_bottom")
    
    # 6.2 面接口: interface_face_top_stage1 (第一级凸台顶面, Z=0.12)
    # 这是 Link1 的安装面
    ref_plane_top_s1 = sw_doc.create_ref_plane(plane="XY", offset_val=base_hgt + boss1_hgt, target_plane_name="interface_face_top_stage1")
    
    # 6.3 轴接口: main_axis_z (Z轴)
    # 沿 Z 方向的轴，穿过原点
    axis_main_z = sw_doc.create_axis(
        pt1=(0, 0, 0), 
        pt2=(0, 0, 1), 
        axis_name="main_axis_z"
    )
    print("[Log] Interfaces created: mount_face_bottom, interface_face_top_stage1, main_axis_z")

    # 7. 保存文件
    output_path = "demo_session/assembly_case/parts/base_plate.SLDPRT"
    
    success = sw_doc.save_as(output_path)
    
    if success:
        print(f"[Success] Part saved to {output_path}")
    else:
        print("[Error] Failed to save part.")

if __name__ == "__main__":
    model_base_plate()