# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用并创建零件文档
    app = SldWorksApp()
    part_name = "简约矩形桌"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 2. 定义参数 (单位转换为米)
    # 桌面尺寸
    table_length = 1.200  # 1200 mm
    table_width = 0.600   # 600 mm
    table_thickness = 0.025 # 25 mm
    
    # 桌腿尺寸
    leg_diameter = 0.040  # 40 mm
    leg_radius = leg_diameter / 2
    leg_height = 0.750    # 750 mm
    
    # 位置关系
    edge_offset = 0.050   # 50 mm (桌腿中心距边缘距离)
    
    # 圆角半径
    fillet_radius = 0.002 # 2 mm

    # 3. 创建桌面 (长方体)
    # 在 XY 平面绘制中心矩形
    sketch_table = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(
        center_x=0, 
        center_y=0, 
        width=table_length, 
        height=table_width, 
        sketch_ref="XY"
    )
    
    # 拉伸桌面，向上拉伸厚度
    # 注意：通常桌子底面作为基准，或者顶面。这里假设桌面主体从 Z=0 到 Z=thickness
    extrude_table = sw_doc.extrude(sketch_table, depth=table_thickness, single_direction=True, merge=True)
    print("桌面主体创建完成")

    # 4. 创建桌腿 (4根圆柱)
    # 计算桌腿中心坐标
    # X方向半长减去偏移量
    x_pos = (table_length / 2) - edge_offset
    # Y方向半宽减去偏移量
    y_pos = (table_width / 2) - edge_offset
    
    leg_centers = [
        (x_pos, y_pos),      # 第一象限
        (-x_pos, y_pos),     # 第二象限
        (-x_pos, -y_pos),    # 第三象限
        (x_pos, -y_pos)      # 第四象限
    ]
    
    for i, (cx, cy) in enumerate(leg_centers):
        # 在桌面底部平面 (Z=0) 或顶部平面 (Z=thickness) 建草图？
        # 题目说“位于桌面底部”，通常意味着桌腿连接在桌面下表面。
        # 为了建模方便，我们在 Z=0 平面（即桌面底面）绘制草图，然后向下拉伸。
        
        # 由于 SolidWorks 默认基准面是全局的，我们需要在 Z=0 处操作。
        # 之前的拉伸是从 Z=0 到 Z=0.025。所以 Z=0 是底面。
        
        sketch_leg = sw_doc.insert_sketch_on_plane("XY")
        sw_doc.create_circle(center_x=cx, center_y=cy, radius=leg_radius, sketch_ref="XY")
        
        # 向下拉伸桌腿 (负方向)
        # 深度为 leg_height
        sw_doc.extrude(sketch_leg, depth=-leg_height, single_direction=True, merge=True)
        print(f"第 {i+1} 根桌腿创建完成 at ({cx}, {cy})")

    # 5. 添加圆角 (Fillet)
    # 要求：所有外露锐边添加 R2mm 圆角
    # 这是一个复杂的几何选择问题。对于简单的长方体和圆柱组合，
    # 我们可以尝试对特定的边进行圆角。
    
    # 策略：
    # 1. 桌面顶面的4条边
    # 2. 桌面侧面的4条垂直边 (如果存在且未被桌腿遮挡，但通常桌腿在内侧，侧面边是外露的)
    # 3. 桌腿底部的4个圆周边
    # 4. 桌腿与桌面连接处的边 (通常是内凹或相切，可能不需要圆角或需要特殊处理，题目说"外露锐边")
    
    # 为了稳健性，我们选取一些关键点来定位边。
    # 桌面顶面边 (Z = table_thickness)
    top_z = table_thickness
    half_l = table_length / 2
    half_w = table_width / 2
    
    # 桌面顶面四条边的中点附近点，用于选择边
    # 边1: x from -half_l to half_l, y = half_w, z = top_z
    # 边2: x from -half_l to half_l, y = -half_w, z = top_z
    # 边3: y from -half_w to half_w, x = half_l, z = top_z
    # 边4: y from -half_w to half_w, x = -half_l, z = top_z
    
    points_top_edges = [
        (0, half_w, top_z),       # Top edge Y+
        (0, -half_w, top_z),      # Top edge Y-
        (half_l, 0, top_z),       # Top edge X+
        (-half_l, 0, top_z)       # Top edge X-
    ]
    
    try:
        sw_doc.fillet_edges(on_line_points=points_top_edges, radius=fillet_radius)
        print("桌面顶面边缘圆角完成")
    except Exception as e:
        print(f"桌面顶面边缘圆角失败: {e}")

    # 桌面侧面垂直边 (Z from 0 to top_z)
    # 这些边在角落: (±half_l, ±half_w, z)
    # 选取中间高度点
    mid_z = top_z / 2
    points_vertical_edges = [
        (half_l, half_w, mid_z),
        (-half_l, half_w, mid_z),
        (-half_l, -half_w, mid_z),
        (half_l, -half_w, mid_z)
    ]
    
    try:
        sw_doc.fillet_edges(on_line_points=points_vertical_edges, radius=fillet_radius)
        print("桌面侧面垂直边缘圆角完成")
    except Exception as e:
        print(f"桌面侧面垂直边缘圆角失败: {e}")

    # 桌腿底部边缘 (Z = -leg_height)
    bottom_z = -leg_height
    points_leg_bottom_edges = []
    for cx, cy in leg_centers:
        # 圆周上的点，例如右侧点
        points_leg_bottom_edges.append((cx + leg_radius, cy, bottom_z))
        
    try:
        sw_doc.fillet_edges(on_line_points=points_leg_bottom_edges, radius=fillet_radius)
        print("桌腿底部边缘圆角完成")
    except Exception as e:
        print(f"桌腿底部边缘圆角失败: {e}")

    # 注意：桌腿与桌面连接的根部边缘通常也是锐边，但如果桌腿是合并实体，
    # 这里的几何拓扑可能比较复杂。如果上述圆角已经覆盖了主要外露边，
    # 且没有报错，则继续。如果有特定需求需处理根部，可能需要更精确的点选。
    # 鉴于“所有外露锐边”，根部内侧如果是直角，也算外露。
    # 让我们尝试添加根部边缘的圆角。
    # 根部边缘位于 Z=0 (桌面底面) 和 桌腿侧面交界处。
    # 点选桌腿侧面靠近底部的点? 不，那是面。
    # 边是圆形的。
    # 选取桌腿侧面与桌面底面交界圆上的点。
    # 例如: (cx + leg_radius, cy, 0)
    
    points_leg_root_edges = []
    for cx, cy in leg_centers:
        points_leg_root_edges.append((cx + leg_radius, cy, 0))
        
    try:
        sw_doc.fillet_edges(on_line_points=points_leg_root_edges, radius=fillet_radius)
        print("桌腿根部边缘圆角完成")
    except Exception as e:
        print(f"桌腿根部边缘圆角失败: {e}")

    # 6. 保存文件
    model_path = r"D:\a_src\python\sw_agent\agent_output\简约矩形桌-20260423_163327\part\简约矩形桌.SLDPRT"
    success = sw_doc.save_as(model_path)
    
    if success:
        print(f"模型已成功保存至: {model_path}")
    else:
        print("模型保存失败")

if __name__ == "__main__":
    main()