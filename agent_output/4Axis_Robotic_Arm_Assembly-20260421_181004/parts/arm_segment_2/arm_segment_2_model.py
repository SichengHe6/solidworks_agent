# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def model_arm_segment_2():
    """
    生成 Arm Segment 2 零件模型。
    结构：两个 60x60x60mm 立方体，中间由 Φ40x150mm 圆柱连接。
    底部立方体侧面有 Φ10 通孔（用于与上一级臂的销轴配合）。
    顶部立方体侧面有 Φ10x15mm 销轴（用于与下一级臂配合）。
    所有立方体棱边倒角 C2。
    """
    
    # 1. 初始化应用和文档
    app = SldWorksApp()
    part_name = "Arm_Segment_2"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 定义尺寸 (转换为米)
    cube_size = 0.060      # 60 mm
    cyl_dia = 0.040        # 40 mm
    cyl_len = 0.150        # 150 mm
    pin_dia = 0.010        # 10 mm
    pin_len = 0.015        # 15 mm
    chamfer_dist = 0.002   # C2 -> 2 mm
    
    # 坐标系约定：
    # 局部 Z 轴为臂的延伸方向（从 Bottom Cube 到 Top Cube）
    # 局部 X 轴为销轴/孔的方向
    # 局部 Y 轴垂直于 X 和 Z
    
    # --- 步骤 1: 创建底部立方体 (Bottom Cube) ---
    # 在 XY 平面绘制中心矩形，拉伸形成底部立方体
    sketch_bottom_cube = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(
        center_x=0, 
        center_y=0, 
        width=cube_size, 
        height=cube_size, 
        sketch_ref="XY"
    )
    # 向上拉伸 (Z+)
    extrude_bottom = sw_doc.extrude(sketch_bottom_cube, depth=cube_size, single_direction=True, merge=True)
    print("底部立方体创建完成")

    # --- 步骤 2: 创建连接圆柱 (Connector Cylinder) ---
    # 在底部立方体的顶面 (Z = cube_size) 创建草图
    # 为了准确定位，我们创建一个偏移平面或直接使用现有面。
    # 这里使用 create_workplane_p_d 创建位于 Z=cube_size 的平面，或者直接在顶面操作。
    # 由于 API 限制，我们通常在基准面上操作。我们可以创建一个位于 Z=cube_size 的工作平面。
    plane_top_of_bottom = sw_doc.create_workplane_p_d("XY", offset_val=cube_size)
    
    sketch_cyl_base = sw_doc.insert_sketch_on_plane(plane_top_of_bottom)
    sw_doc.create_circle(center_x=0, center_y=0, radius=cyl_dia / 2, sketch_ref="XY")
    # 向上拉伸圆柱
    extrude_cyl = sw_doc.extrude(sketch_cyl_base, depth=cyl_len, single_direction=True, merge=True)
    print("连接圆柱创建完成")

    # --- 步骤 3: 创建顶部立方体 (Top Cube) ---
    # 顶部立方体底面位于 Z = cube_size + cyl_len
    z_top_cube_start = cube_size + cyl_len
    plane_top_cube_base = sw_doc.create_workplane_p_d("XY", offset_val=z_top_cube_start)
    
    sketch_top_cube = sw_doc.insert_sketch_on_plane(plane_top_cube_base)
    sw_doc.create_centre_rectangle(
        center_x=0, 
        center_y=0, 
        width=cube_size, 
        height=cube_size, 
        sketch_ref="XY"
    )
    # 向上拉伸
    extrude_top = sw_doc.extrude(sketch_top_cube, depth=cube_size, single_direction=True, merge=True)
    print("顶部立方体创建完成")

    # --- 步骤 4: 创建底部侧孔 (Bottom Side Hole) ---
    # 孔位于底部立方体侧面，沿 X 轴方向，穿过 YZ 平面中心。
    # 底部立方体范围: X[-0.03, 0.03], Y[-0.03, 0.03], Z[0, 0.06]
    # 孔中心应在 Z=0.03 (立方体高度一半), Y=0, X 贯穿。
    # 我们在 YZ 平面 (X=0) 上绘制圆，然后沿 X 轴拉伸切除。
    # 注意：YZ 平面对应 SolidWorks 中的 "ZY" 或类似，需确认 sketch_ref。
    # 根据知识库，sketch_ref 可以是 "XY", "XZ", "ZY"。
    # 如果要在 YZ 平面画图，通常对应 "ZY" (Z up, Y right/left)。
    # 让我们尝试在 "ZY" 平面画圆，圆心在 (Y=0, Z=0.03)。
    # 但是 "ZY" 平面的原点是全局原点。我们需要确保草图位置正确。
    # 更稳妥的方式：创建一个通过 X 轴的平面？不，直接在右视基准面 (Right Plane, 通常是 YZ) 操作。
    # 假设 "ZY" 是右视基准面。
    
    sketch_bottom_hole = sw_doc.insert_sketch_on_plane("ZY")
    # 在 ZY 平面上，坐标是 (Y, Z) 还是 (Z, Y)? 
    # 通常 SolidWorks 中 Right Plane (YZ) 的草图坐标：水平是 Y，垂直是 Z。
    # 圆心位置：Y=0, Z=0.03 (底部立方体中心高度)
    sw_doc.create_circle(center_x=0, center_y=0.03, radius=pin_dia / 2, sketch_ref="ZY")
    # 沿 X 轴双向拉伸切除，确保穿透整个立方体 (宽度 0.06)
    # 深度设为大于 0.06 即可，例如 0.1，单向或双向。
    # 为了对称，使用双向拉伸 (single_direction=False) 或者单向但深度足够。
    # 这里使用单向，向 +X 方向切穿，再向 -X 方向切穿？
    # 简单起见，双向拉伸切除，深度 0.1 (总长)，这样肯定穿透。
    cut_bottom_hole = sw_doc.extrude_cut(sketch_bottom_hole, depth=0.1, single_direction=False)
    print("底部侧孔创建完成")

    # --- 步骤 5: 创建顶部销轴 (Top Pin) ---
    # 销轴位于顶部立方体侧面，沿 X 轴方向。
    # 顶部立方体范围: Z [z_top_cube_start, z_top_cube_start + cube_size]
    # 中心高度 Z_pin_center = z_top_cube_start + cube_size / 2
    z_pin_center = z_top_cube_start + cube_size / 2
    
    # 同样在 YZ 平面 ("ZY") 绘制圆
    sketch_top_pin = sw_doc.insert_sketch_on_plane("ZY")
    sw_doc.create_circle(center_x=0, center_y=z_pin_center, radius=pin_dia / 2, sketch_ref="ZY")
    # 向 +X 方向拉伸凸台 (Pin protrudes from face)
    # 假设销轴从 +X 面伸出。
    # 顶部立方体 X 范围 [-0.03, 0.03]。+X 面在 X=0.03。
    # 如果我们从 YZ 平面 (X=0) 开始拉伸，需要拉伸到 X=0.03 + pin_len。
    # 或者，更简单的逻辑：在 +X 面上画圆并拉伸。
    # 让我们改变策略：在顶部立方体的 +X 面上创建草图。
    # +X 面是一个平面，我们可以通过偏移 XZ 平面来模拟，或者直接使用特征选择。
    # 由于 API 限制，我们继续使用基准面方法。
    # 在 YZ 平面画圆，然后单向拉伸 +X 方向。
    # 起点 X=0。终点 X = 0.03 (立方体表面) + 0.015 (销长) = 0.045。
    # 所以深度 = 0.045。
    # 但是这样会填充立方体内部的一部分。因为立方体已经存在，merge=True 会合并。
    # 这是正确的，销轴是实体的一部分。
    
    # 重新插入草图以清除之前的状态（如果需要），或者直接新建
    sketch_top_pin_2 = sw_doc.insert_sketch_on_plane("ZY")
    sw_doc.create_circle(center_x=0, center_y=z_pin_center, radius=pin_dia / 2, sketch_ref="ZY")
    # 向 +X 拉伸
    extrude_pin = sw_doc.extrude(sketch_top_pin_2, depth=0.045, single_direction=True, merge=True)
    print("顶部销轴创建完成")

    # --- 步骤 6: 倒角 (Chamfer C2) ---
    # 需要对所有立方体的棱边进行 C2 倒角。
    # 底部立方体棱边：
    # 12 条边。
    # 由于自动识别所有边比较困难，我们选取关键点来定位边。
    # 底部立方体角点示例：(0.03, 0.03, 0), (-0.03, 0.03, 0) 等。
    # 边上的点：
    bottom_edges_points = [
        (0.03, 0.03, 0.001), (0.03, -0.03, 0.001), (-0.03, 0.03, 0.001), (-0.03, -0.03, 0.001), # 底面四边附近
        (0.03, 0.03, 0.059), (0.03, -0.03, 0.059), (-0.03, 0.03, 0.059), (-0.03, -0.03, 0.059), # 顶面四边附近
        (0.03, 0.001, 0.03), (0.03, -0.001, 0.03), (-0.03, 0.001, 0.03), (-0.03, -0.001, 0.03), # 侧面竖直边附近
        (0.001, 0.03, 0.03), (-0.001, 0.03, 0.03), (0.001, -0.03, 0.03), (-0.001, -0.03, 0.03)  # 另外四个侧面竖直边
    ]
    
    # 顶部立方体棱边：
    # Z 范围 [z_top_cube_start, z_top_cube_start + cube_size]
    z_tc_min = z_top_cube_start
    z_tc_max = z_top_cube_start + cube_size
    top_edges_points = [
        (0.03, 0.03, z_tc_min + 0.001), (0.03, -0.03, z_tc_min + 0.001), (-0.03, 0.03, z_tc_min + 0.001), (-0.03, -0.03, z_tc_min + 0.001),
        (0.03, 0.03, z_tc_max - 0.001), (0.03, -0.03, z_tc_max - 0.001), (-0.03, 0.03, z_tc_max - 0.001), (-0.03, -0.03, z_tc_max - 0.001),
        (0.03, 0.001, z_tc_min + 0.03), (0.03, -0.001, z_tc_min + 0.03), (-0.03, 0.001, z_tc_min + 0.03), (-0.03, -0.001, z_tc_min + 0.03),
        (0.001, 0.03, z_tc_min + 0.03), (-0.001, 0.03, z_tc_min + 0.03), (0.001, -0.03, z_tc_min + 0.03), (-0.001, -0.03, z_tc_min + 0.03)
    ]
    
    all_chamfer_points = bottom_edges_points + top_edges_points
    
    try:
        sw_doc.chamfer_edges(on_line_points=all_chamfer_points, distance=chamfer_dist, angle=45.0)
        print("倒角处理完成")
    except Exception as e:
        print(f"倒角可能部分失败或跳过: {e}")

    # --- 步骤 7: 创建接口 (Interfaces) ---
    
    # 1. 面接口: bottom_side_face
    # 目的: 与 Arm 1 top_pin_face 配合。
    # 描述: 底部立方体的 -X 侧面。
    # 位置: X = -0.03, Y=0, Z=0.03 (中心)
    # 创建一个参考平面，平行于 YZ 平面，偏移 -0.03
    ref_plane_bottom_side = sw_doc.create_ref_plane("ZY", offset_val=-0.03, target_plane_name="bottom_side_face")
    
    # 2. 面接口: top_pin_face
    # 目的: 销轴起源面。
    # 描述: 顶部立方体的 +X 侧面。
    # 位置: X = 0.03
    ref_plane_top_pin_face = sw_doc.create_ref_plane("ZY", offset_val=0.03, target_plane_name="top_pin_face")
    
    # 3. 面接口: side_mate_face_top
    # 目的: 轴向约束。
    # 描述: 顶部立方体的 +X 侧面 (同 top_pin_face 或稍作区分，这里复用或创建同名)
    # 根据 spec，side_mate_face_top 也是 normal +X。我们可以复用上面的平面，或者创建一个稍微不同的命名。
    # 为了清晰，我们创建另一个引用同一几何位置的平面，或者直接使用上面的。
    # 这里创建一个新的命名平面指向同一位置，以便装配时明确引用。
    ref_plane_side_mate_top = sw_doc.create_ref_plane("ZY", offset_val=0.03, target_plane_name="side_mate_face_top")

    # 4. 轴接口: bottom_hole_axis
    # 目的: 与 Arm 1 pin_axis 同心。
    # 方向: 沿局部 X 轴。
    # 位置: 穿过底部立方体中心 (Y=0, Z=0.03)。
    # 点1: (-0.1, 0, 0.03), 点2: (0.1, 0, 0.03)
    axis_bottom_hole = sw_doc.create_axis(
        pt1=(-0.1, 0, 0.03), 
        pt2=(0.1, 0, 0.03), 
        axis_name="bottom_hole_axis"
    )
    
    # 5. 轴接口: pin_axis
    # 目的: 与 Arm 3 bottom_hole_axis 同心。
    # 方向: 沿局部 X 轴。
    # 位置: 穿过顶部立方体中心 (Y=0, Z=z_pin_center)。
    axis_pin = sw_doc.create_axis(
        pt1=(-0.1, 0, z_pin_center), 
        pt2=(0.1, 0, z_pin_center), 
        axis_name="pin_axis"
    )

    print("接口创建完成")

    # --- 步骤 8: 保存文件 ---
    model_path = r"D:\a_src\python\sw_agent\agent_output\4Axis_Robotic_Arm_Assembly-20260421_181004\parts\arm_segment_2\arm_segment_2.SLDPRT"
    success = sw_doc.save_as(model_path)
    
    if success:
        print(f"零件成功保存至: {model_path}")
    else:
        print("零件保存失败")

if __name__ == "__main__":
    model_arm_segment_2()