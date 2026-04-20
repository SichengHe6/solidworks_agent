# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化与创建零件
    # 尺寸单位换算：1 mm = 0.001 m
    model_path = r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_173236\parts\m8_screw\m8_screw.SLDPRT"
    
    app = SldWorksApp()
    sw_doc = PartDoc(app.createAndActivate_sw_part("m8_screw"))
    print("开始建模零件：M8螺钉")

    # 定义尺寸 (m)
    head_diameter = 0.013
    head_thickness = 0.008
    shank_diameter = 0.008
    shank_length = 0.040

    # 2. 建模螺钉头部
    # 在 XY 平面绘制直径 13mm 的圆，并拉伸 8mm
    print(f"正在创建螺钉头部: 直径 {head_diameter}m, 厚度 {head_thickness}m")
    sketch_head = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=head_diameter/2, sketch_ref="XY")
    # 向 Z 正方向拉伸
    sw_doc.extrude(sketch_head, depth=head_thickness, single_direction=True)

    # 3. 建模螺钉螺杆
    # 在头部底面（即 XY 平面，因为头部是向 Z+ 拉伸的）绘制直径 8mm 的圆
    # 或者直接在 XY 平面向 Z- 方向拉伸螺杆
    print(f"正在创建螺钉螺杆: 直径 {shank_diameter}m, 长度 {shank_length}m")
    sketch_shank = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=shank_diameter/2, sketch_ref="XY")
    # 向 Z 负方向拉伸，以保证头部底面在 Z=0 处，方便后续装配贴合
    sw_doc.extrude(sketch_shank, depth=-shank_length, single_direction=True, merge=True)

    # 4. 创建装配接口
    print("正在创建装配接口...")
    
    # 接口1: head_bottom_face (螺钉头下表面)
    # 螺钉头在 Z=0 到 Z=0.008 之间，螺杆在 Z=0 到 Z=-0.04 之间
    # 因此 Z=0 的平面即为 head_bottom_face
    sw_doc.create_ref_plane("XY", 0, target_plane_name="head_bottom_face")

    # 接口2: screw_axis (螺钉中心轴线)
    # 轴线从头部顶端 (0,0,0.008) 延伸到螺杆末端 (0,0,-0.04)
    sw_doc.create_axis(pt1=(0, 0, head_thickness), pt2=(0, 0, -shank_length), axis_name="screw_axis")

    # 5. 保存零件
    success = sw_doc.save_as(model_path)
    if success:
        print(f"零件建模完成并成功保存至: {model_path}")
    else:
        print("零件保存失败，请检查路径权限。")

if __name__ == "__main__":
    main()