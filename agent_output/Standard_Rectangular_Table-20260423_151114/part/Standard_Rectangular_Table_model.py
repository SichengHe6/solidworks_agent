# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Standard_Rectangular_Table"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 2. 定义参数 (单位: mm -> m)
    table_length_mm = 1200.0
    table_width_mm = 600.0
    table_thickness_mm = 25.0
    
    leg_diameter_mm = 30.0
    leg_height_mm = 725.0
    
    leg_offset_edge_mm = 50.0
    
    chamfer_dist_mm = 2.0

    # 转换为米
    L = table_length_mm / 1000.0
    W = table_width_mm / 1000.0
    H_table = table_thickness_mm / 1000.0
    
    D_leg = leg_diameter_mm / 1000.0
    R_leg = D_leg / 2.0
    H_leg = leg_height_mm / 1000.0
    
    offset = leg_offset_edge_mm / 1000.0
    chamfer_dist = chamfer_dist_mm / 1000.0

    # 3. 创建桌面主体 (XY平面)
    print("步骤 1: 创建桌面主体")
    sketch_top = sw_doc.insert_sketch_on_plane("XY")
    # 中心矩形，长L，宽W
    sw_doc.create_centre_rectangle(
        center_x=0, 
        center_y=0, 
        width=L, 
        height=W, 
        sketch_ref="XY"
    )
    # 拉伸桌面，厚度H_table，单向向上(Z+)
    extrude_top = sw_doc.extrude(sketch_top, depth=H_table, single_direction=True, merge=True)
    print("桌面主体创建完成")

    # 4. 创建桌腿 (在桌面底面 Z=0 处绘制草图，向下拉伸)
    print("步骤 2: 创建桌腿")
    
    # 计算桌腿中心坐标
    # 桌面范围: X [-L/2, L/2], Y [-W/2, W/2]
    # 桌腿中心距边缘 offset
    x_pos = L/2 - offset
    y_pos = W/2 - offset
    
    leg_centers = [
        (x_pos, y_pos),   # 第一象限
        (-x_pos, y_pos),  # 第二象限
        (-x_pos, -y_pos), # 第三象限
        (x_pos, -y_pos)   # 第四象限
    ]
    
    # 在 XY 平面 (Z=0) 上绘制四个圆
    sketch_legs = sw_doc.insert_sketch_on_plane("XY")
    for cx, cy in leg_centers:
        sw_doc.create_circle(center_x=cx, center_y=cy, radius=R_leg, sketch_ref="XY")
        
    # 拉伸切除? 不，是添加材料。但是桌腿是在桌面下方。
    # 桌面占据 Z [0, H_table]。
    # 桌腿应该从 Z=0 向下延伸到 Z=-H_leg。
    # 使用 extrude，depth 为负值表示向法向量反方向（即-Z方向）。
    # 注意：SolidWorks 中如果草图在面上，默认拉伸方向可能取决于面的法向或用户选择。
    # 这里我们在 XY 平面画圆，XY 平面法向通常是 +Z。
    # 我们要向 -Z 方向拉伸。所以 depth 设为 -H_leg。
    # merge=True 确保与桌面合并。
    extrude_legs = sw_doc.extrude(sketch_legs, depth=-H_leg, single_direction=True, merge=True)
    print("桌腿创建完成")

    # 5. 桌面边缘倒角 C2
    print("步骤 3: 桌面顶面边缘倒角")
    # 桌面顶面位于 Z = H_table
    # 我们需要选择顶面的四条边进行倒角。
    # 为了定位边，我们可以提供边上的一些点。
    # 顶面矩形的四个角点坐标 (X, Y, Z=H_table):
    # (L/2, W/2, H_table), (-L/2, W/2, H_table), etc.
    # 边的中点或者角点附近的点都可以用来定位边。
    # 这里使用角点来定位相邻的两条边可能不够精确，最好用边上的中间点。
    
    # 边1: X = L/2, Y from -W/2 to W/2, Z = H_table. Point: (L/2, 0, H_table)
    # 边2: X = -L/2, Y from -W/2 to W/2, Z = H_table. Point: (-L/2, 0, H_table)
    # 边3: Y = W/2, X from -L/2 to L/2, Z = H_table. Point: (0, W/2, H_table)
    # 边4: Y = -W/2, X from -L/2 to L/2, Z = H_table. Point: (0, -W/2, H_table)
    
    edge_points = [
        (L/2, 0, H_table),
        (-L/2, 0, H_table),
        (0, W/2, H_table),
        (0, -W/2, H_table)
    ]
    
    # C2 倒角: distance=2mm, angle=45deg
    try:
        sw_doc.chamfer_edges(on_line_points=edge_points, distance=chamfer_dist, angle=45.0)
        print("桌面边缘倒角完成")
    except Exception as e:
        print(f"倒角操作失败: {e}")
        # 如果自动识别边失败，可能需要更复杂的逻辑，但通常中点足够唯一标识直边

    # 6. 保存文件
    output_path = r"D:\a_src\python\sw_agent\agent_output\Standard_Rectangular_Table-20260423_151114\part\Standard_Rectangular_Table.SLDPRT"
    print(f"保存零件至: {output_path}")
    success = sw_doc.save_as(output_path)
    
    if success:
        print("建模与保存成功。")
    else:
        print("保存失败。")

if __name__ == "__main__":
    main()