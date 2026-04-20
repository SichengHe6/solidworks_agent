# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc
import os

def main():
    # 1. 初始化与路径设置
    model_file = r"D:\a_src\python\sw_agent\agent_output\4_Axis_Serial_Robot_Arm-20260416_175529\parts\base_station\base_station.SLDPRT"
    part_dir = os.path.dirname(model_file)
    if not os.path.exists(part_dir):
        os.makedirs(part_dir)

    # 尺寸参数转换 (mm -> m)
    base_diameter = 200 / 1000.0
    base_height = 50 / 1000.0
    hole_diameter = 20 / 1000.0

    app = SldWorksApp()
    # 创建并激活零件文档
    sw_doc = PartDoc(app.createAndActivate_sw_part("base_station"))
    print("开始建模零件：底座 (base_station)")

    # 2. 建模主体：圆柱底座
    # 在 XY 平面绘制直径 200mm 的圆
    sketch1 = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=base_diameter / 2.0, sketch_ref="XY")
    # 向上拉伸 50mm
    extrude1 = sw_doc.extrude(sketch1, depth=base_height, single_direction=True)
    print(f"主体拉伸完成，高度: {base_height}m")

    # 3. 建模特征：中心通孔
    # 在顶面（Z=0.05）或 XY 平面绘制直径 20mm 的圆
    sketch2 = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=hole_diameter / 2.0, sketch_ref="XY")
    # 向下拉伸切除通孔 (深度设为负值或覆盖整个高度)
    sw_doc.extrude_cut(sketch2, depth=base_height, single_direction=True)
    print(f"中心孔切除完成，孔径: {hole_diameter}m")

    # 4. 创建装配接口
    # 接口 1: base_bottom_face (底面)
    sw_doc.create_ref_plane("XY", 0, target_plane_name="base_bottom_face")
    
    # 接口 2: base_top_face (顶面)
    sw_doc.create_ref_plane("XY", base_height, target_plane_name="base_top_face")

    # 接口 3: axis_1_rot (第一轴旋转中心)
    # 轴从原点 (0,0,0) 指向 (0,0,0.05)
    sw_doc.create_axis((0, 0, 0), (0, 0, base_height), axis_name="axis_1_rot")
    print("装配接口 (参考面与参考轴) 创建完成")

    # 5. 保存零件
    success = sw_doc.save_as(model_file)
    if success:
        print(f"零件成功保存至: {model_file}")
    else:
        print("零件保存失败，请检查路径权限或 SolidWorks 状态。")

if __name__ == "__main__":
    main()