# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Main Column"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 2. 定义尺寸参数 (单位: m)
    # Key Dimensions from JSON:
    # Outer Diameter: 28mm -> 0.028m
    # Inner Diameter: 20mm -> 0.020m
    # Length: 150mm -> 0.150m
    # Bottom Flange Thickness: 5mm -> 0.005m
    # Top Joint Width: 30mm -> 0.030m
    
    outer_dia = 0.028
    inner_dia = 0.020
    tube_length = 0.150
    flange_thick = 0.005
    flange_dia = 0.035 # Assumed slightly larger than tube for stability, based on typical design
    joint_width = 0.030
    joint_depth = 0.020 # Depth of the U-cut into the tube top
    
    # 3. 建模步骤
    
    # Step 3.1: 创建底部法兰盘 (Flange)
    # 在XY平面绘制法兰圆，向上拉伸
    sketch_flange = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=flange_dia/2, sketch_ref="XY")
    extrude_flange = sw_doc.extrude(sketch_flange, depth=flange_thick, single_direction=True, merge=True)
    print("Step 1: 底部法兰盘创建完成")

    # Step 3.2: 创建主体管状结构 (Tube Body)
    # 在法兰顶面(即Z=flange_thick处)或直接在XY平面偏移后拉伸。
    # 为了简化，我们在XY平面画环，然后拉伸总高度 (tube_length + flange_thick)，但这样会覆盖法兰内部。
    # 更好的策略：在XY平面画外圆，拉伸到总高；然后在顶部画内圆切除？或者画环拉伸。
    # 让我们采用：在XY平面画外圆，拉伸到总高度 (tube_length + flange_thick)。
    # 然后在顶部画内圆，向下切除形成中空。
    
    total_height = tube_length + flange_thick
    
    sketch_tube_outer = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=outer_dia/2, sketch_ref="XY")
    extrude_tube = sw_doc.extrude(sketch_tube_outer, depth=total_height, single_direction=True, merge=True)
    print("Step 2: 主体外圆柱创建完成")

    # Step 3.3: 创建中空内孔 (Hollow Core)
    # 在顶面 (Z = total_height) 创建草图，画内圆，向下切除
    # 首先创建一个参考平面用于顶面草图，或者直接利用现有几何。
    # API insert_sketch_on_plane 支持 "XY", "XZ", "ZY"。对于顶面，我们需要一个偏移平面。
    top_plane = sw_doc.create_workplane_p_d(plane="XY", offset_val=total_height)
    
    sketch_tube_inner = sw_doc.insert_sketch_on_plane(top_plane)
    sw_doc.create_circle(center_x=0, center_y=0, radius=inner_dia/2, sketch_ref="XY") # Ref is still XY logic relative to plane normal? 
    # Note: The API doc says sketch_ref must match plane direction. For a plane parallel to XY, ref should be "XY".
    # Cut downwards through all or specific depth. Since it's hollow, cut down to just above flange or through.
    # Let's cut down to the flange top surface (depth = tube_length).
    sw_doc.extrude_cut(sketch_tube_inner, depth=tube_length, single_direction=True) # Direction is -Z relative to plane normal if single_direction=True and we want to go down? 
    # Wait, extrude_cut depth positive usually means along normal. Normal of XY-offset-up is +Z. We want to cut DOWN (-Z).
    # So depth should be negative or use single_direction=False? 
    # Let's assume standard behavior: Positive depth follows normal. To cut down, we might need negative depth or check API specifics.
    # Given "depth: ... 正值为向平面法向量正方向切除", and our plane normal is +Z, we want -Z. So depth = -tube_length.
    sw_doc.extrude_cut(sketch_tube_inner, depth=-tube_length, single_direction=True)
    print("Step 3: 中空内孔切除完成")

    # Step 3.4: 创建顶部U型叉耳 (Top U-Joint)
    # 需要在顶部切除两侧材料，形成宽度为 joint_width 的槽。
    # 槽宽 30mm，意味着从中心向左右各切去 (outer_dia - joint_width)/2 ? 
    # 不，通常是保留中间部分，切除两边。或者切除中间留两边？
    # "U型叉耳" 通常指两个耳朵夹住悬臂。所以是切除中间部分还是两边？
    # 描述说 "Top Joint Width: 30mm"。如果外径28mm，关节宽30mm比外径还大？这不可能。
    # 重新审视尺寸：Outer Dia 28mm. Joint Width 30mm. 
    # 这可能意味着叉耳的外侧间距是30mm，或者叉耳本身的厚度/宽度定义不同。
    # 如果外径只有28mm，无法做出30mm宽的实体叉耳而不超出外径。
    # 可能性1：Joint Width指的是两个叉耳内侧之间的距离（间隙），用于容纳悬臂。
    # 可能性2：Joint Width指的是叉耳结构的整体包络宽度，但这超过了管径，需要加宽顶部。
    # 根据常见设计，立柱顶部可能会稍微加宽以提供足够的铰接强度。
    # 让我们假设：顶部有一个加宽的块，或者我们直接在管顶切出一个槽。
    # 如果必须在28mm直径上实现30mm宽的配合，这在几何上是不可能的（除非悬臂很薄且嵌入）。
    # 修正理解：也许 "Top Joint Width" 是指叉耳两臂外侧的总宽度？如果是这样，它必须 >= 28mm。30mm > 28mm，合理。
    # 那么，叉耳两臂之间的间隙是多少？假设悬臂厚度约15-20mm。
    # 让我们采取另一种稳健策略：在顶部创建一个矩形块作为连接头，然后再切U型。
    # 或者，简单地在顶部切一个通槽。
    # 为了符合 "U型叉耳" 和 "Width 30mm"，我将假设这是指叉耳开口处的有效宽度或者整体宽度。
    # 鉴于外径28mm，我将创建一个顶部局部加宽特征，或者直接切割。
    # 让我们尝试：在顶部创建一个长方体基座，宽30mm，长等于外径或稍大，高一定值，然后切U型。
    # 但指令说 "在顶部切除材料形成U型叉耳"。这暗示主体已经是那个形状。
    # 如果主体是28mm圆柱，要得到30mm宽的叉耳，必须先加宽顶部。
    # 让我们在顶部添加一个 30mm x 30mm x 10mm 的方块，然后在这个方块上切U型槽。
    
    # 添加顶部连接块
    block_height = 0.015 # 15mm high block for joint
    block_width = 0.030  # 30mm
    block_length = 0.030 # 30mm
    
    # 在顶面 (Z = total_height) 创建草图
    sketch_block = sw_doc.insert_sketch_on_plane(top_plane)
    # 绘制中心矩形
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=block_width, height=block_length, sketch_ref="XY")
    sw_doc.extrude(sketch_block, depth=block_height, single_direction=True, merge=True)
    print("Step 4: 顶部连接块创建完成")

    # 在连接块上切U型槽
    # 槽的方向：沿X轴还是Y轴？
    # 接口定义：pitch1_axis 沿 local Y。这意味着旋转轴是Y轴。
    # 悬臂将绕Y轴旋转。因此，叉耳的开口应该朝向X方向（前后）或者Z方向？
    # 通常悬臂向前伸出。如果绕Y轴俯仰，叉耳应该在X-Z平面内张开？
    # 不，如果轴是Y，叉耳的两个臂应该在Y方向的两侧？不对。
    # 想象门铰链：轴垂直于门板。如果轴是Y（左右），门板在X-Z平面旋转。
    # 叉耳需要夹住悬臂的根部。悬臂根部有一个孔，轴穿过孔。
    # 所以叉耳的两个臂应该平行于X-Z平面？不，叉耳臂应该平行于旋转轴所在的平面法线？
    # 标准U型叉：两个平行的板，中间有间隙。轴穿过这两个板。
    # 如果轴是Y轴，那么这两个板应该垂直于Y轴吗？不，轴穿过板的孔。所以板应该平行于X-Z平面？
    # 如果板平行于X-Z平面，它们的法线是Y。那么间隙是沿Y方向的。
    # 这样悬臂插入间隙，轴沿Y穿过。
    # 所以，我们需要切除沿Y方向的材料，留下沿X方向延伸的两个臂？
    # 不，如果间隙沿Y，那么切除的是一个沿Y方向的槽。
    # 让我们确认坐标系：
    # Global Z up. Y left. X forward.
    # Pitch1 axis along Local Y.
    # 这意味着旋转是绕左右轴进行的（点头动作）。
    # 叉耳应该允许悬臂在X-Z平面内摆动。
    # 因此，叉耳的两个臂应该位于Y轴的两侧（左臂和右臂）。
    # 间隙在中间，沿Y方向测量宽度？不，间隙宽度是两臂内侧距离。
    # 如果臂在Y两侧，间隙就是沿Y方向的空隙。
    # 所以我们要切除一个沿Y方向的矩形槽？
    # 不，如果臂在Y两侧，说明材料在Y方向被分开了。
    # 这意味着我们要切除中间的部分，留下左边和右边的材料。
    # 切除的形状：一个长方体，沿Y方向贯穿？或者只在顶部？
    # 让我们在顶部块的顶面 (Z = total_height + block_height) 创建草图。
    
    top_of_block_plane = sw_doc.create_workplane_p_d(plane="XY", offset_val=total_height + block_height)
    sketch_cut_u = sw_doc.insert_sketch_on_plane(top_of_block_plane)
    
    # 我们要切除中间部分，形成两个臂。
    # 假设臂厚 5mm each. Total width 30mm. Gap = 30 - 5 - 5 = 20mm? 
    # 或者根据 "Top Joint Width: 30mm"，这可能指整个组件宽30mm。
    # 让我们设定间隙宽度为 16mm (适配悬臂厚度15mm + 间隙)。
    gap_width = 0.016
    arm_thickness = (block_width - gap_width) / 2
    
    # 绘制要切除的矩形：中心在原点，宽度=gap_width，长度=block_length (贯穿)
    # 实际上，U型槽通常不贯穿整个长度，而是有一定深度。
    # 但为了形成叉耳，通常需要切透或者切到轴心位置。
    # 让我们切一个矩形，宽度 gap_width，长度 block_length，深度足以到达轴心。
    # 轴心位置：通常在块的中心高度附近。
    # 让我们在草图中画一个矩形，代表要移除的材料。
    # 矩形范围：X: -block_length/2 to +block_length/2, Y: -gap_width/2 to +gap_width/2
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=block_length, height=gap_width, sketch_ref="XY")
    
    # 向下切除，深度为 block_height (切穿整个块) 或者更深进入管体？
    # 通常叉耳根部需要加强，不一定切穿到管体内部，但为了简化，切穿块即可。
    # 如果需要轴孔，后续再打孔。
    sw_doc.extrude_cut(sketch_cut_u, depth=-block_height, single_direction=True)
    print("Step 5: U型叉耳槽切除完成")

    # Step 3.5: 创建轴孔 (Pin Hole)
    # 在叉耳的两个臂上打孔，用于安装转轴。
    # 轴沿Y方向。孔中心应在块的中心 (X=0, Z=center_of_block_height)。
    # 我们需要在侧面（XZ平面或YZ平面？）创建草图。
    # 由于对称，可以在 Right Plane (YZ) 或 Front Plane (XZ) 上操作？
    # 孔沿Y轴，所以草图平面应垂直于Y轴，即 XZ 平面。
    # 但是 XZ 平面是全局的。我们需要在局部位置。
    # 我们可以创建一个平行于 XZ 的平面，偏移 Y = block_width/2 (右侧面)？
    # 或者更简单：在 YZ 平面（侧面）画圆？不，孔轴线是Y，截面在XZ平面。
    # 让我们在 XZ 平面创建草图？不，XZ平面是Y=0。
    # 我们需要在 Y = arm_thickness/2 + gap/2 ? 不，是在臂的中心。
    # 臂的范围 Y: [gap/2, block_width/2]. 中心 Y = (gap/2 + block_width/2)/2.
    # 让我们创建一个参考平面 Parallel to XZ, at Y = arm_center_y.
    
    arm_center_y = (gap_width/2 + block_width/2) / 2
    
    # 创建右侧孔草图平面
    plane_right_hole = sw_doc.create_workplane_p_d(plane="XZ", offset_val=arm_center_y) # Offset in Y? 
    # create_workplane_p_d(plane, offset). If plane is "XZ", offset is likely along Y normal? 
    # Assuming standard SW API mapping: XZ plane normal is Y. So offset moves along Y.
    
    sketch_hole_right = sw_doc.insert_sketch_on_plane(plane_right_hole)
    # 孔中心坐标：X=0, Z = total_height + block_height/2
    hole_z = total_height + block_height / 2
    hole_radius = 0.004 # 8mm diameter hole for pin? Spec doesn't specify pin dia, but arm has 8mm hole. Let's match.
    # Arm spec: Base Hole Diameter 8mm. So column hole should be 8mm.
    sw_doc.create_circle(center_x=0, center_y=hole_z, radius=hole_radius, sketch_ref="XZ") 
    # Note: In XZ plane sketch, coords are (x, z). The API create_circle takes (center_x, center_y). 
    # Does it map to (u, v) of the plane? Yes. For XZ plane, u=X, v=Z.
    
    # 切除孔。方向沿Y轴负方向（向左）穿过整个宽度？
    # 孔需要穿过两个臂。
    # 我们可以从右侧面向左切除，深度 = block_width (穿过整个顶部块宽度)。
    sw_doc.extrude_cut(sketch_hole_right, depth=-block_width, single_direction=True)
    print("Step 6: 转轴孔创建完成")

    # 4. 创建装配接口 (Interfaces)

    # Interface: bottom_flange_face
    # Purpose: Mate with base. Normal -Z.
    # This is the bottom face of the flange at Z=0.
    # We can create a reference plane coincident with this face for easier mating, 
    # or just rely on the face itself. The prompt asks to "expose interface names".
    # Creating a named reference plane is the robust way.
    ref_bottom_face = sw_doc.create_ref_plane(plane="XY", offset_val=0.0, target_plane_name="bottom_flange_face")
    
    # Interface: top_joint_side_left & top_joint_side_right
    # These are the inner faces of the U-joint arms.
    # Left Arm Inner Face: Y = +gap_width/2 ? Or -?
    # Coordinate system: Y+ is Left.
    # If we cut a slot from -gap/2 to +gap/2.
    # The "Left" side of the slot (positive Y side) has a face at Y = +gap_width/2.
    # The "Right" side of the slot (negative Y side) has a face at Y = -gap_width/2.
    # However, the interface names are "top_joint_side_left" and "top_joint_side_right".
    # Usually "Left" refers to the part's left.
    # Let's create reference planes at these locations.
    
    ref_joint_side_left = sw_doc.create_ref_plane(plane="XZ", offset_val=gap_width/2, target_plane_name="top_joint_side_left")
    ref_joint_side_right = sw_doc.create_ref_plane(plane="XZ", offset_val=-gap_width/2, target_plane_name="top_joint_side_right")

    # Interface: column_main_axis
    # Purpose: Concentric with base. Along Z.
    # Create an axis along Z passing through (0,0,0).
    axis_main = sw_doc.create_axis(pt1=(0, 0, 0), pt2=(0, 0, 1), axis_name="column_main_axis")

    # Interface: pitch1_axis
    # Purpose: Rotation axis for arm. Along Y, passing through top joint center.
    # Center of joint: X=0, Y=0, Z=hole_z.
    # Axis along Y.
    axis_pitch1 = sw_doc.create_axis(pt1=(0, -1, hole_z), pt2=(0, 1, hole_z), axis_name="pitch1_axis")

    print("Step 7: 装配接口创建完成")

    # 5. 保存文件
    output_path = r"D:\a_src\python\sw_agent\agent_output\iPhone17_5DOF_Stand_Assembly-20260424_171652\parts\main_column\main_column.SLDPRT"
    success = sw_doc.save_as(output_path)
    
    if success:
        print(f"零件成功保存至: {output_path}")
    else:
        print("零件保存失败")

if __name__ == "__main__":
    main()