# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def model_table_top():
    # 1. 初始化应用和零件
    # 尺寸单位换算：1 mm = 0.001 m
    app = SldWorksApp()
    model_file = r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_173236\parts\table_top\table_top.SLDPRT"
    sw_doc = PartDoc(app.createAndActivate_sw_part("table_top"))
    
    print("开始建模：桌面 (table_top)")

    # 2. 创建主体：800mm x 800mm x 25mm
    width = 0.800
    length = 0.800
    thickness = 0.025
    
    sketch1 = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=width, height=length, sketch_ref="XY")
    # 向 Z 正方向拉伸 25mm
    sw_doc.extrude(sketch1, depth=thickness, single_direction=True)
    print(f"主体拉伸完成: {width}x{length}x{thickness} m")

    # 3. 创建四个角部的通孔：直径 8.5mm
    # 孔位中心距离边缘 25mm。由于是中心矩形，边缘坐标为 +/- 400mm
    # 孔中心坐标计算：400 - 25 = 375mm -> 0.375m
    hole_radius = 0.0085 / 2
    hole_pos = 0.375
    
    # 在顶面 (Z=0.025) 绘制草图进行切除
    # 注意：insert_sketch_on_plane 传入 "XY" 会在默认 XY 平面，
    # 也可以通过偏移平面或直接在顶面操作。这里使用偏移平面确保在顶面切除。
    top_plane = sw_doc.create_workplane_p_d("XY", thickness)
    sketch_holes = sw_doc.insert_sketch_on_plane(top_plane)
    
    # 绘制四个圆
    hole_coords = [
        (hole_pos, hole_pos),   # 右上
        (-hole_pos, hole_pos),  # 左上
        (-hole_pos, -hole_pos), # 左下
        (hole_pos, -hole_pos)   # 右下
    ]
    
    for x, y in hole_coords:
        sw_doc.create_circle(center_x=x, center_y=y, radius=hole_radius, sketch_ref="XY")
    
    # 向下切除（深度为负或指向实体内部）
    sw_doc.extrude_cut(sketch_holes, depth=-thickness, single_direction=True)
    print("四个安装通孔切除完成")

    # 4. 创建装配接口
    # 4.1 面接口
    # top_face: Z = 0.025
    sw_doc.create_ref_plane("XY", thickness, target_plane_name="top_face")
    # bottom_face: Z = 0
    sw_doc.create_ref_plane("XY", 0, target_plane_name="bottom_face")
    
    # 4.2 轴接口 (hole_axis_1 到 4)
    # 轴 1: 左上 (-0.375, 0.375)
    sw_doc.create_axis((-hole_pos, hole_pos, 0), (-hole_pos, hole_pos, thickness), axis_name="hole_axis_1")
    # 轴 2: 右上 (0.375, 0.375)
    sw_doc.create_axis((hole_pos, hole_pos, 0), (hole_pos, hole_pos, thickness), axis_name="hole_axis_2")
    # 轴 3: 左下 (-0.375, -0.375)
    sw_doc.create_axis((-hole_pos, -hole_pos, 0), (-hole_pos, -hole_pos, thickness), axis_name="hole_axis_3")
    # 轴 4: 右下 (0.375, -0.375)
    sw_doc.create_axis((hole_pos, -hole_pos, 0), (hole_pos, -hole_pos, thickness), axis_name="hole_axis_4")
    
    print("装配接口（参考面与参考轴）创建完成")

    # 5. 保存零件
    sw_doc.save_as(model_file)
    print(f"零件建模成功并保存至: {model_file}")

if __name__ == "__main__":
    model_table_top()