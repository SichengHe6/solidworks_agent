# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Link_2"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 定义尺寸 (单位: m)
    cyl_dia = 0.060      # φ60mm
    cyl_len = 0.250      # 250mm
    block_size = 0.080   # 80x80mm
    block_thick = 0.025  # 25mm
    bottom_hole_dia = 0.032 # φ32mm
    top_pin_dia = 0.030     # φ30mm
    top_pin_len = 0.020     # 20mm
    chamfer_dist = 0.005    # C5
    
    # --- 步骤 1: 创建主体圆柱 ---
    # 在 XY 平面绘制中心圆，沿 Z 轴拉伸
    sketch_cyl = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=cyl_dia/2, sketch_ref="XY")
    extrude_cyl = sw_doc.extrude(sketch_cyl, depth=cyl_len, single_direction=True, merge=True)
    print("主体圆柱创建完成")

    # --- 步骤 2: 底部方块 (Z=0 处，向下拉伸) ---
    # 在 XY 平面绘制正方形，向 -Z 方向拉伸
    sketch_bot_block = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=block_size, height=block_size, sketch_ref="XY")
    # 注意：extrude depth 为负值表示向法向量反方向（即 -Z）
    extrude_bot_block = sw_doc.extrude(sketch_bot_block, depth=-block_thick, single_direction=True, merge=True)
    print("底部方块创建完成")

    # --- 步骤 3: 底部侧面孔 (φ32mm, 沿 X 轴) ---
    # 需要在底部方块的 -X 侧面上创建草图。
    # 底部方块范围: X[-40, 40], Y[-40, 40], Z[-25, 0]
    # -X 侧面位于 X = -40mm (-0.04m)。
    # 为了在该面上画草图，我们需要一个平行于 YZ 平面的基准面，或者直接在面上插入草图。
    # 由于 API 限制，我们创建一个偏移基准面来辅助，或者直接利用 create_workplane_p_d 创建参考面。
    # 这里使用 create_workplane_p_d 基于 "ZY" 平面偏移？不，ZY 是 X=0。
    # 我们需要 X = -0.04 的平面。
    # 实际上，SolidWorks 中可以在面上直接插入草图。但封装接口 insert_sketch_on_plane 接受 plane 对象或名称。
    # 让我们先创建一个参考平面用于定位，或者尝试直接使用坐标点选择面？
    # 根据知识库，insert_sketch_on_plane 接受 "XY", "XZ", "ZY" 或自定义平面名。
    # 我们可以创建一个名为 "BotBlock_Face_XNeg" 的参考平面。
    
    # 创建参考平面：基于 ZY 平面 (X=0)，偏移 -0.04m
    ref_plane_bot_xneg = sw_doc.create_ref_plane(plane="ZY", offset_val=-block_size/2, target_plane_name="BotBlock_Face_XNeg")
    
    # 在该参考平面上插入草图
    sketch_bot_hole = sw_doc.insert_sketch_on_plane(ref_plane_bot_xneg)
    # 在 YZ 视图下 (因为平面是 ZY 偏移)，坐标系通常是 Y 水平, Z 垂直? 
    # 对于 ZY 平面，sketch_ref 应该是 "ZY"。
    # 圆心位置：Y=0, Z = -block_thick/2 (方块厚度的一半，即中心)
    # 注意：在 ZY 平面上，create_circle 的 x,y 对应全局的 Y,Z ? 
    # 根据知识库："ZY 可能对 x 做反号处理... 只需要按封装要求给 sketch_ref"。
    # 通常 SolidWorks 草图坐标系：
    # XY: X->Right, Y->Up
    # XZ: X->Right, Z->Up (Y is normal)
    # ZY: Z->Right?, Y->Up? 或者 Y->Right, Z->Up?
    # 标准 SW 行为：
    # Front Plane (XY): X right, Y up.
    # Top Plane (XZ): X right, Z up.
    # Right Plane (YZ/ZY): Y right, Z up. (Normal is X)
    # 如果我们在 X = -0.04 的平面上，法线指向 +X 还是 -X？
    # create_ref_plane 基于 ZY (Normal +X?) 偏移。
    # 假设草图坐标系：U (Horizontal), V (Vertical).
    # 对于 ZY 平面，通常 U=Y, V=Z.
    # 所以 center_x 参数对应 Y 坐标，center_y 参数对应 Z 坐标。
    # 我们要画的孔中心在全局坐标 (X=-0.04, Y=0, Z=-0.0125).
    # 所以在草图中：center_x (Y) = 0, center_y (Z) = -0.0125.
    
    bot_hole_center_z = -block_thick / 2.0
    sw_doc.create_circle(center_x=0, center_y=bot_hole_center_z, radius=bottom_hole_dia/2, sketch_ref="ZY")
    
    # 切除孔。需要贯穿整个方块宽度 (80mm)。
    # 方块在 X 方向从 -0.04 到 +0.04。
    # 当前草图在 X = -0.04。
    # 如果向 +X 方向切除 (法线方向)，深度应为 0.08。
    # 如果向 -X 方向切除，深度应为 -0.08 (但这会切出实体外)。
    # 通常 extrude_cut 默认沿草图法线正方向。
    # 参考平面 "BotBlock_Face_XNeg" 是基于 ZY 偏移得到的。ZY 的法线通常是 +X。
    # 所以切除方向应该是 +X，深度 0.08。
    cut_bot_hole = sw_doc.extrude_cut(sketch_bot_hole, depth=block_size, single_direction=True)
    print("底部侧面孔创建完成")

    # --- 步骤 4: 底部方块倒角 C5 ---
    # 需要对底部方块的边缘进行倒角。
    # 底部方块有 12 条边。
    # 为了简化，我们可以选择几个关键点来定位边。
    # 底部方块顶点示例: (-0.04, -0.04, -0.025), (-0.04, 0.04, -0.025) 等。
    # 倒角所有竖直边和水平边可能比较繁琐，且容易出错。
    # 题目要求 "Chamfer C5 on block edges"。
    # 我们可以尝试对特定的边进行倒角。
    # 选取底部方块顶面 (Z=0) 的四条边，和底面 (Z=-0.025) 的四条边，以及四条竖边。
    # 为了稳定性，我们先处理竖边。
    # 竖边上的点: (-0.04, -0.04, -0.0125), (-0.04, 0.04, -0.0125), (0.04, -0.04, -0.0125), (0.04, 0.04, -0.0125)
    # 注意：chamfer_edges 需要边上任意点。
    
    try:
        # 底部方块竖边
        pts_bot_vert = [
            (-block_size/2, -block_size/2, -block_thick/2),
            (-block_size/2, block_size/2, -block_thick/2),
            (block_size/2, -block_size/2, -block_thick/2),
            (block_size/2, block_size/2, -block_thick/2)
        ]
        sw_doc.chamfer_edges(on_line_points=pts_bot_vert, distance=chamfer_dist, angle=45.0)
        
        # 底部方块顶面边 (Z=0)
        pts_bot_top = [
            (-block_size/2, -block_size/2, 0),
            (-block_size/2, block_size/2, 0),
            (block_size/2, -block_size/2, 0),
            (block_size/2, block_size/2, 0)
        ]
        sw_doc.chamfer_edges(on_line_points=pts_bot_top, distance=chamfer_dist, angle=45.0)
        
        # 底部方块底面边 (Z=-0.025)
        pts_bot_bottom = [
            (-block_size/2, -block_size/2, -block_thick),
            (-block_size/2, block_size/2, -block_thick),
            (block_size/2, -block_size/2, -block_thick),
            (block_size/2, block_size/2, -block_thick)
        ]
        sw_doc.chamfer_edges(on_line_points=pts_bot_bottom, distance=chamfer_dist, angle=45.0)
        
        print("底部方块倒角完成")
    except Exception as e:
        print(f"底部倒角失败: {e}")

    # --- 步骤 5: 顶部方块 (Z=250 处，向上拉伸) ---
    # 在 XY 平面绘制正方形，向 +Z 方向拉伸
    # 顶部方块起始于 Z = cyl_len = 0.25
    sketch_top_block = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=block_size, height=block_size, sketch_ref="XY")
    # 拉伸起点是当前草图平面 (Z=0)? 不，草图是在 XY (Z=0) 上画的吗？
    # 之前的操作都在 Z=0 附近。现在要在 Z=0.25 处建块。
    # 我们需要先在 Z=0.25 处创建一个基准面，或者在现有面上画草图。
    # 更简单的方法：在 XY 平面画草图，然后拉伸时指定起始条件？API 不支持。
    # 正确做法：创建一个偏移平面 Z = 0.25。
    ref_plane_top_base = sw_doc.create_ref_plane(plane="XY", offset_val=cyl_len, target_plane_name="TopBlock_Base_Plane")
    
    sketch_top_block_real = sw_doc.insert_sketch_on_plane(ref_plane_top_base)
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=block_size, height=block_size, sketch_ref="XY")
    # 向 +Z 方向拉伸
    extrude_top_block = sw_doc.extrude(sketch_top_block_real, depth=block_thick, single_direction=True, merge=True)
    print("顶部方块创建完成")

    # --- 步骤 6: 顶部侧面销轴 (φ30mm, 沿 +X 轴) ---
    # 顶部方块范围: X[-40, 40], Y[-40, 40], Z[250, 275]
    # +X 侧面位于 X = 40mm (0.04m)。
    # 创建参考平面 X = 0.04
    ref_plane_top_xpos = sw_doc.create_ref_plane(plane="ZY", offset_val=block_size/2, target_plane_name="TopBlock_Face_XPos")
    
    sketch_top_pin = sw_doc.insert_sketch_on_plane(ref_plane_top_xpos)
    # 销轴中心：Y=0, Z = cyl_len + block_thick/2 = 0.25 + 0.0125 = 0.2625
    top_pin_center_z = cyl_len + block_thick / 2.0
    sw_doc.create_circle(center_x=0, center_y=top_pin_center_z, radius=top_pin_dia/2, sketch_ref="ZY")
    
    # 拉伸销轴。沿 +X 方向 (法线方向)，长度 20mm。
    extrude_top_pin = sw_doc.extrude(sketch_top_pin, depth=top_pin_len, single_direction=True, merge=True)
    print("顶部销轴创建完成")

    # --- 步骤 7: 顶部方块倒角 C5 ---
    try:
        # 顶部方块竖边
        pts_top_vert = [
            (-block_size/2, -block_size/2, cyl_len + block_thick/2),
            (-block_size/2, block_size/2, cyl_len + block_thick/2),
            (block_size/2, -block_size/2, cyl_len + block_thick/2),
            (block_size/2, block_size/2, cyl_len + block_thick/2)
        ]
        sw_doc.chamfer_edges(on_line_points=pts_top_vert, distance=chamfer_dist, angle=45.0)
        
        # 顶部方块顶面边 (Z=0.275)
        pts_top_top = [
            (-block_size/2, -block_size/2, cyl_len + block_thick),
            (-block_size/2, block_size/2, cyl_len + block_thick),
            (block_size/2, -block_size/2, cyl_len + block_thick),
            (block_size/2, block_size/2, cyl_len + block_thick)
        ]
        sw_doc.chamfer_edges(on_line_points=pts_top_top, distance=chamfer_dist, angle=45.0)
        
        # 顶部方块底面边 (Z=0.25) - 注意这里可能与圆柱连接处有干涉，但通常倒角只作用于方块外露边
        # 实际上，方块底面与圆柱顶面重合，这部分边可能不需要倒角或者无法倒角。
        # 我们只对暴露在外的边进行倒角。
        # 暴露的边包括：顶面4条，竖边4条。底面4条被圆柱遮挡或合并。
        # 为了安全，只倒角顶面和竖边。
        
        print("顶部方块倒角完成")
    except Exception as e:
        print(f"顶部倒角失败: {e}")

    # --- 步骤 8: 创建装配接口 (参考面与参考轴) ---
    
    # 1. link2_bottom_side_face_hole (Normal -X)
    # 这是底部方块 -X 侧的面。我们已经创建了 ref_plane_bot_xneg (X=-0.04)。
    # 但是该平面是用于画草图的，它本身就是一个参考面。
    # 我们可以重命名它或者创建一个新的同名参考面以确保语义清晰。
    # 既然 ref_plane_bot_xneg 已经存在且位置正确，我们可以直接使用它，或者创建一个偏移量为0的新面并命名。
    # 为了符合接口名称，我们创建一个明确命名的面。
    iface_bot_face = sw_doc.create_ref_plane(plane=ref_plane_bot_xneg, offset_val=0, target_plane_name="link2_bottom_side_face_hole")
    
    # 2. link2_top_side_face_pin_base (Normal +X)
    # 这是顶部方块 +X 侧的面 (X=0.04)。
    iface_top_face = sw_doc.create_ref_plane(plane=ref_plane_top_xpos, offset_val=0, target_plane_name="link2_top_side_face_pin_base")
    
    # 3. link2_bottom_side_hole_axis (Along local X)
    # 孔中心线：通过 (-0.04, 0, -0.0125) 沿 X 方向。
    # 起点: (-0.04, 0, -0.0125), 终点: (0.04, 0, -0.0125)
    pt1_bot_axis = (-block_size/2, 0, -block_thick/2)
    pt2_bot_axis = (block_size/2, 0, -block_thick/2)
    iface_bot_axis = sw_doc.create_axis(pt1=pt1_bot_axis, pt2=pt2_bot_axis, axis_name="link2_bottom_side_hole_axis")
    
    # 4. link2_top_pin_axis (Along local X)
    # 销轴中心线：通过 (0.04, 0, 0.2625) 沿 X 方向。
    # 起点: (0.04, 0, 0.2625), 终点: (0.06, 0, 0.2625) (稍微延伸一点以明确方向)
    pt1_top_axis = (block_size/2, 0, top_pin_center_z)
    pt2_top_axis = (block_size/2 + top_pin_len, 0, top_pin_center_z)
    iface_top_axis = sw_doc.create_axis(pt1=pt1_top_axis, pt2=pt2_top_axis, axis_name="link2_top_pin_axis")

    print("装配接口创建完成")

    # --- 步骤 9: 保存文件 ---
    model_path = r"D:\a_src\python\sw_agent\agent_output\4Axis_RobotArm_Assembly-20260421_180034\parts\link_2\link_2.SLDPRT"
    success = sw_doc.save_as(model_path)
    
    if success:
        print(f"零件已成功保存至: {model_path}")
    else:
        print("零件保存失败")

if __name__ == "__main__":
    main()