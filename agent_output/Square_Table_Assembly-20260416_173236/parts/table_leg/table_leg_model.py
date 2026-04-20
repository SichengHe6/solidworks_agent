# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化与创建零件
    # 尺寸定义 (单位换算: mm -> m)
    leg_width = 0.050  # 50mm
    leg_height = 0.375 # 375mm
    hole_diameter = 0.0085 # 8.5mm
    hole_depth = 0.020 # 20mm
    
    model_path = r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_173236\parts\table_leg\table_leg.SLDPRT"
    
    app = SldWorksApp()
    sw_doc = PartDoc(app.createAndActivate_sw_part("table_leg"))
    print("开始建模零件: table_leg (桌腿)")

    # 2. 创建主体：50x50 中心矩形，拉伸 375mm
    # 在 XY 平面绘制
    sketch1 = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=leg_width, height=leg_width, sketch_ref="XY")
    # 向 Z 正方向拉伸 375mm
    sw_doc.extrude(sketch1, depth=leg_height, single_direction=True)
    print(f"主体拉伸完成: 高度 {leg_height}m")

    # 3. 创建顶面中心盲孔
    # 顶面位于 Z = 0.375 的平面上。
    # 我们可以在 XY 平面上创建一个偏移平面，或者直接在顶面上绘图。
    # 这里使用 create_workplane_p_d 创建一个位于顶部的参考面
    top_plane = sw_doc.create_workplane_p_d("XY", leg_height)
    sketch2 = sw_doc.insert_sketch_on_plane(top_plane)
    sw_doc.create_circle(center_x=0, center_y=0, radius=hole_diameter/2, sketch_ref="XY")
    
    # 向下切除 (深度为正，因为法向朝外，具体取决于封装内部对切除方向的定义，通常正值向内切)
    # 根据 instructions: 向下切除深度 20mm
    sw_doc.extrude_cut(sketch2, depth=hole_depth, single_direction=True)
    print(f"盲孔切除完成: 直径 {hole_diameter}m, 深度 {hole_depth}m")

    # 4. 创建装配接口
    # 接口 1: top_end_face (顶面)
    sw_doc.create_ref_plane(top_plane, 0, target_plane_name="top_end_face")
    
    # 接口 2: side_face_x (X方向侧面，位于 x = 25mm 处)
    side_plane_x = sw_doc.create_workplane_p_d("ZY", leg_width/2)
    sw_doc.create_ref_plane(side_plane_x, 0, target_plane_name="side_face_x")
    
    # 接口 3: side_face_y (Y方向侧面，位于 y = 25mm 处)
    side_plane_y = sw_doc.create_workplane_p_d("XZ", leg_width/2)
    sw_doc.create_ref_plane(side_plane_y, 0, target_plane_name="side_face_y")

    # 接口 4: leg_hole_axis (中心孔轴线)
    # 轴线从顶面中心 (0,0,0.375) 向下延伸
    sw_doc.create_axis((0, 0, leg_height), (0, 0, leg_height - hole_depth), axis_name="leg_hole_axis")
    print("装配接口 (top_end_face, side_face_x, side_face_y, leg_hole_axis) 创建完成")

    # 5. 保存零件
    success = sw_doc.save_as(model_path)
    if success:
        print(f"零件建模成功并保存至: {model_path}")
    else:
        print("零件保存失败，请检查路径权限。")

if __name__ == "__main__":
    main()