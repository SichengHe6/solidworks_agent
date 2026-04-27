# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Desktop Panel"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 2. 定义参数 (单位: m)
    length = 1.200      # 1200 mm
    width = 0.600       # 600 mm
    thickness = 0.025   # 25 mm
    corner_radius = 0.005 # 5 mm
    hole_diameter = 0.006 # 6 mm
    
    # 孔位坐标 (相对于中心原点)
    # X = ±580mm -> ±0.58m
    # Y = ±280mm -> ±0.28m
    x_pos = 0.580
    x_neg = -0.580
    y_pos = 0.280
    y_neg = -0.280
    
    hole_centers = [
        (x_pos, y_pos),
        (x_pos, y_neg),
        (x_neg, y_pos),
        (x_neg, y_neg)
    ]

    # 3. 创建主体轮廓草图 (XY平面)
    print("步骤 1: 绘制桌面主体轮廓")
    sketch_base = sw_doc.insert_sketch_on_plane("XY")
    
    # 绘制中心矩形
    sw_doc.create_centre_rectangle(
        center_x=0, 
        center_y=0, 
        width=length, 
        height=width, 
        sketch_ref="XY"
    )
    
    # 对四个角进行圆角处理
    # 注意：create_sketch_fillet 需要指定角点。对于中心矩形，角点坐标为 (±L/2, ±W/2)
    half_l = length / 2
    half_w = width / 2
    
    corners = [
        (half_l, half_w),
        (half_l, -half_w),
        (-half_l, half_w),
        (-half_l, -half_w)
    ]
    
    for corner in corners:
        sw_doc.create_sketch_fillet(
            sketch_points=[corner], 
            radius=corner_radius, 
            sketch_ref="XY"
        )
        
    # 拉伸生成实体
    # 向 -Z 方向拉伸厚度
    print("步骤 2: 拉伸生成桌面实体")
    extrude_feature = sw_doc.extrude(
        sketch=sketch_base, 
        depth=-thickness, 
        single_direction=True, 
        merge=True
    )

    # 4. 创建安装孔
    print("步骤 3: 创建安装孔")
    # 在底面 (Z = -thickness) 上创建草图
    # 由于底面是平面，我们可以直接在 XY 平面上偏移 Z 值来定位，或者更简单地，
    # 在 XY 平面画孔，然后切除贯穿或指定深度。
    # 为了精确控制位置，我们在 XY 平面绘制孔的圆心，然后向下切除。
    
    sketch_holes = sw_doc.insert_sketch_on_plane("XY")
    
    for cx, cy in hole_centers:
        sw_doc.create_circle(
            center_x=cx, 
            center_y=cy, 
            radius=hole_diameter / 2, 
            sketch_ref="XY"
        )
        
    # 执行拉伸切除，贯穿整个厚度
    # 深度设为负值，表示沿法向量反方向（即-Z）切除
    # 为了确保切穿，深度可以略大于厚度，或者使用单向切除并设置足够深度
    cut_feature = sw_doc.extrude_cut(
        sketch=sketch_holes, 
        depth=-thickness * 1.1, # 稍微多切一点确保通孔
        single_direction=True
    )

    # 5. 创建装配接口 (参考面和参考轴)
    print("步骤 4: 创建装配接口")
    
    # 5.1 面接口
    # bottom_face: Z = -thickness 处的平面
    # top_face: Z = 0 处的平面 (XY基准面本身，但为了明确接口，可以创建一个重合的参考面或直接引用)
    # 这里我们创建命名的参考面以便装配引用
    
    # 创建底面参考面 (Offset from XY by -thickness)
    ref_bottom = sw_doc.create_ref_plane(
        plane="XY", 
        offset_val=-thickness, 
        target_plane_name="bottom_face"
    )
    
    # 创建顶面参考面 (Offset from XY by 0, essentially XY but named)
    # 如果 API 允许 offset 0 并重命名，则这样做；否则可能需要其他方式。
    # 假设 create_ref_plane 支持 offset 0
    ref_top = sw_doc.create_ref_plane(
        plane="XY", 
        offset_val=0.0, 
        target_plane_name="top_face"
    )

    # 5.2 轴接口 (安装孔轴线)
    # 轴线沿 Z 方向，穿过孔中心
    # pt1: (x, y, 0) - 顶面附近
    # pt2: (x, y, -thickness) - 底面附近
    
    axis_definitions = [
        ("mount_hole_axis_fl_xp_yp", x_pos, y_pos),
        ("mount_hole_axis_fl_xp_ym", x_pos, y_neg),
        ("mount_hole_axis_bl_xm_yp", x_neg, y_pos),
        ("mount_hole_axis_bl_xm_ym", x_neg, y_neg)
    ]
    
    for axis_name, ax, ay in axis_definitions:
        sw_doc.create_axis(
            pt1=(ax, ay, 0.0),
            pt2=(ax, ay, -thickness),
            axis_name=axis_name
        )
        print(f"  创建轴: {axis_name} at ({ax}, {ay})")

    # 6. 保存文件
    output_path = r"D:\a_src\python\sw_agent\agent_output\Standard_Office_Table_Assembly-20260423_143100\parts\desktop_main\desktop_main.SLDPRT"
    print(f"步骤 5: 保存文件至 {output_path}")
    success = sw_doc.save_as(output_path)
    
    if success:
        print("建模完成并保存成功。")
    else:
        print("保存失败，请检查路径权限或 SolidWorks 状态。")

if __name__ == "__main__":
    main()