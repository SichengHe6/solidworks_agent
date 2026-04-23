# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Link_1"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 2. 定义尺寸参数 (单位: m)
    cyl_diam = 0.060      # φ60mm
    cyl_len = 0.300       # 300mm
    
    block_size = 0.080    # 80x80mm
    block_thick = 0.025   # 25mm
    
    bottom_hole_diam = 0.042 # φ42mm
    
    top_pin_diam = 0.030     # φ30mm
    top_pin_len = 0.020      # 20mm
    
    chamfer_dist = 0.005     # C5mm

    # 3. 主体圆柱建模 (沿Z轴)
    # 在XY平面绘制中心圆
    sketch_cyl = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=cyl_diam/2, sketch_ref="XY")
    sw_doc.extrude(sketch_cyl, depth=cyl_len, single_direction=True, merge=True)
    print("主体圆柱创建完成")

    # 4. 底部方块 (Z=0处，向下拉伸)
    # 在XY平面绘制中心矩形
    sketch_bot_block = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=block_size, height=block_size, sketch_ref="XY")
    # 向负Z方向拉伸
    sw_doc.extrude(sketch_bot_block, depth=-block_thick, single_direction=True, merge=True)
    print("底部方块创建完成")

    # 5. 底部通孔 (φ42mm, 沿Z轴)
    # 在XY平面绘制圆
    sketch_bot_hole = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=bottom_hole_diam/2, sketch_ref="XY")
    # 切除，深度需贯穿底部方块。由于方块厚25mm，且从Z=0开始向下，切除深度设为 -0.03m 确保贯通
    sw_doc.extrude_cut(sketch_bot_hole, depth=-0.03, single_direction=True)
    print("底部通孔创建完成")

    # 6. 顶部方块 (Z=300mm处，向上拉伸)
    # 需要在Z=0.3的平面上绘图。先创建偏移基准面或直接使用Top Face? 
    # API中 insert_sketch_on_plane 支持 "XY", "XZ", "ZY" 或自定义平面名。
    # 为了稳定，我们创建一个位于 Z=0.3 的参考平面用于顶部方块草图，或者直接在现有实体顶面操作？
    # 封装通常允许在已有实体的面上插入草图，但这里为了明确坐标，我们先创建一个工作平面。
    # 注意：create_workplane_p_d 基于基准面偏移。
    plane_top = sw_doc.create_workplane_p_d(plane="XY", offset_val=cyl_len)
    
    sketch_top_block = sw_doc.insert_sketch_on_plane(plane_top)
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=block_size, height=block_size, sketch_ref="XY")
    # 向正Z方向拉伸
    sw_doc.extrude(sketch_top_block, depth=block_thick, single_direction=True, merge=True)
    print("顶部方块创建完成")

    # 7. 顶部销轴 (φ30mm, 沿+X方向伸出)
    # 销轴位于顶部方块的 +X 侧面。
    # 顶部方块范围 X: [-0.04, 0.04], Y: [-0.04, 0.04], Z: [0.3, 0.325]
    # 销轴中心应在 Y=0, Z=0.3 + 0.025/2 = 0.3125
    # 销轴起始面是 X=0.04 的面。
    # 我们需要在 X=0.04 的平面上画圆。
    # 创建参考平面 X=0.04 (基于YZ平面偏移? 不，API只有XY/XZ/ZY偏移。
    # 我们可以利用 create_workplane_p_d 基于 "ZY" 平面偏移 X 值吗？
    # 查看 API: create_workplane_p_d(plane, offset_val). plane可以是 "XY"/"XZ"/"ZY".
    # 如果 plane="ZY", offset_val 应该是沿 X 轴的偏移。
    plane_pin_base = sw_doc.create_workplane_p_d(plane="ZY", offset_val=block_size/2) # X = 0.04
    
    sketch_pin = sw_doc.insert_sketch_on_plane(plane_pin_base)
    # 在 ZY 平面上，坐标系通常是 (Y, Z)。
    # 圆心位置：Y=0, Z=0.3125
    # sketch_ref 应为 "ZY"
    sw_doc.create_circle(center_x=0, center_y=0.3125, radius=top_pin_diam/2, sketch_ref="ZY")
    # 向 +X 方向拉伸 (对于 ZY 平面，法向量通常是 +X)
    sw_doc.extrude(sketch_pin, depth=top_pin_len, single_direction=True, merge=True)
    print("顶部销轴创建完成")

    # 8. 倒角处理 (C5)
    # 需要对底部方块和顶部方块的边缘进行倒角。
    # 底部方块边缘：Z=-0.025 处的四个垂直边，以及 Z=0 处的四个水平边（与圆柱连接处可能不需要，主要指外轮廓）。
    # 通常 C5 指的是外棱角。
    # 底部方块顶点示例：(0.04, 0.04, -0.025), (-0.04, 0.04, -0.025) 等。
    # 顶部方块顶点示例：(0.04, 0.04, 0.325), (-0.04, 0.04, 0.325) 等。
    
    # 底部方块上表面边缘 (Z=0, X/Y=±0.04) - 这些边与圆柱相交，可能不需要倒角，或者需要？
    # 指令说 "Chamfer C5 on block edges"。通常指外露的锐边。
    # 让我们选择底部方块的下表面边缘和侧棱。
    
    # 底部方块下表面边缘点 (Z = -0.025)
    bot_edges_pts = [
        (0.04, 0.04, -0.025),
        (-0.04, 0.04, -0.025),
        (-0.04, -0.04, -0.025),
        (0.04, -0.04, -0.025)
    ]
    # 底部方块侧棱 (连接 Z=0 和 Z=-0.025)
    # 选取侧棱上的点，例如中点
    bot_side_edges_pts = [
        (0.04, 0.04, -0.0125),
        (-0.04, 0.04, -0.0125),
        (-0.04, -0.04, -0.0125),
        (0.04, -0.04, -0.0125)
    ]
    
    # 顶部方块上表面边缘 (Z = 0.325)
    top_edges_pts = [
        (0.04, 0.04, 0.325),
        (-0.04, 0.04, 0.325),
        (-0.04, -0.04, 0.325),
        (0.04, -0.04, 0.325)
    ]
    # 顶部方块侧棱
    top_side_edges_pts = [
        (0.04, 0.04, 0.3125),
        (-0.04, 0.04, 0.3125),
        (-0.04, -0.04, 0.3125),
        (0.04, -0.04, 0.3125)
    ]
    
    # 执行倒角
    # 注意：chamfer_edges 需要准确的边定位点。
    try:
        sw_doc.chamfer_edges(on_line_points=bot_edges_pts, distance=chamfer_dist, angle=45.0)
        sw_doc.chamfer_edges(on_line_points=bot_side_edges_pts, distance=chamfer_dist, angle=45.0)
        sw_doc.chamfer_edges(on_line_points=top_edges_pts, distance=chamfer_dist, angle=45.0)
        sw_doc.chamfer_edges(on_line_points=top_side_edges_pts, distance=chamfer_dist, angle=45.0)
        print("倒角处理完成")
    except Exception as e:
        print(f"倒角处理可能失败或部分失败: {e}")

    # 9. 创建装配接口 (参考面与参考轴)
    
    # 接口 1: link1_bottom_face (Z=0 平面，法向 -Z)
    # 这是一个现有的几何面，但为了装配引用，最好创建一个命名的参考平面重合于它，或者直接引用几何面？
    # 任务要求“体现接口名称”。通常通过 create_ref_plane 创建命名平面。
    # 底部面位于 Z=0。
    ref_plane_bottom = sw_doc.create_ref_plane(plane="XY", offset_val=0.0, target_plane_name="link1_bottom_face")
    
    # 接口 2: link1_bottom_hole_axis (Z轴)
    # 沿 Z 轴，穿过原点。
    axis_bottom_hole = sw_doc.create_axis(pt1=(0, 0, -0.1), pt2=(0, 0, 0.1), axis_name="link1_bottom_hole_axis")
    
    # 接口 3: link1_top_side_face_pin_base (X=0.04 平面，法向 +X)
    # 这是销轴的基座面。
    ref_plane_pin_base = sw_doc.create_ref_plane(plane="ZY", offset_val=block_size/2, target_plane_name="link1_top_side_face_pin_base")
    
    # 接口 4: link1_top_pin_axis (沿 X 轴，穿过 Y=0, Z=0.3125)
    # 销轴中心线。
    axis_top_pin = sw_doc.create_axis(
        pt1=(0.04, 0, 0.3125), 
        pt2=(0.04 + top_pin_len, 0, 0.3125), 
        axis_name="link1_top_pin_axis"
    )

    print("接口创建完成")

    # 10. 保存文件
    model_path = r"D:\a_src\python\sw_agent\agent_output\4Axis_RobotArm_Assembly-20260421_180034\parts\link_1\link_1.SLDPRT"
    success = sw_doc.save_as(model_path)
    
    if success:
        print(f"零件已成功保存至: {model_path}")
    else:
        print("零件保存失败")

if __name__ == "__main__":
    main()