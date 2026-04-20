# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化与创建零件
    # 尺寸单位换算：1 mm = 0.001 m
    app = SldWorksApp()
    model_file = r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_174727\parts\tabletop\tabletop.SLDPRT"
    sw_doc = PartDoc(app.createAndActivate_sw_part("tabletop"))
    
    print("开始建模：正方形桌面 (tabletop)")

    # 2. 创建主体：800x800x30 mm 的长方体
    # 桌面顶面位于 Z=0，向负方向拉伸 30mm (0.03m)
    width = 0.8
    thickness = 0.03
    
    sketch_main = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=width, height=width, sketch_ref="XY")
    sw_doc.extrude(sketch_main, depth=-thickness, single_direction=True)
    print(f"主体拉伸完成：{width}x{width}x{thickness}m")

    # 3. 创建四个沉头孔
    # 孔位坐标 (mm): (+/-360, +/-360) -> (m): (+/-0.36, +/-0.36)
    # 沉头孔规格: 大头直径 10mm (深10mm), 小头直径 8mm (贯穿/深30mm)
    hole_positions = [
        (0.36, 0.36),
        (-0.36, 0.36),
        (-0.36, -0.36),
        (0.36, -0.36)
    ]
    
    d_large = 0.010
    d_small = 0.008
    h_large = 0.010
    
    for i, (px, py) in enumerate(hole_positions):
        # 3.1 切除大头孔 (沉头部分)
        sketch_large = sw_doc.insert_sketch_on_plane("XY")
        sw_doc.create_circle(center_x=px, center_y=py, radius=d_large/2, sketch_ref="XY")
        sw_doc.extrude_cut(sketch_large, depth=-h_large)
        
        # 3.2 切除小头孔 (通孔部分)
        sketch_small = sw_doc.insert_sketch_on_plane("XY")
        sw_doc.create_circle(center_x=px, center_y=py, radius=d_small/2, sketch_ref="XY")
        sw_doc.extrude_cut(sketch_small, depth=-thickness)
        
        # 3.3 创建轴接口 (用于装配)
        axis_name = f"hole_axis_{i+1}"
        sw_doc.create_axis(pt1=(px, py, 0), pt2=(px, py, -thickness), axis_name=axis_name)
        print(f"孔 {i+1} 及轴接口 {axis_name} 创建完成")

    # 4. 创建面接口
    # bottom_face: 桌面底面 (Z = -0.03)
    sw_doc.create_ref_plane("XY", offset_val=-thickness, target_plane_name="bottom_face")
    
    # hole_step_face_1: 螺钉1座面 (Z = -0.01)
    sw_doc.create_ref_plane("XY", offset_val=-h_large, target_plane_name="hole_step_face_1")
    
    print("接口面 bottom_face 和 hole_step_face_1 创建完成")

    # 5. 保存零件
    save_status = sw_doc.save_as(model_file)
    if save_status:
        print(f"零件成功保存至: {model_file}")
    else:
        print("零件保存失败")

if __name__ == "__main__":
    main()