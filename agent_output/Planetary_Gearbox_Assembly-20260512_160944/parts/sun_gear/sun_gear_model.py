import math
from pysw import SldWorksApp, PartDoc

def main():
    # 1. 初始化与创建零件
    # 尺寸单位说明：输入为mm，代码内部需转换为m
    app = SldWorksApp()
    part_name = "sun_gear"
    model_path = r"D:\a_src\python\sw_agent\agent_output\Planetary_Gearbox_Assembly-20260512_160944\parts\sun_gear\sun_gear.SLDPRT"
    
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    print(f"开始建模零件: {part_name}")

    # 2. 参数定义 (单位换算为 m)
    m = 2.0 / 1000.0      # 模数
    z = 18                # 齿数
    width = 20.0 / 1000.0 # 齿宽
    hole_dia = 10.0 / 1000.0 # 中心孔径
    
    d = m * z             # 分度圆直径 (36mm)
    da = d + 2 * m        # 齿顶圆直径 (40mm)
    df = d - 2.5 * m      # 齿根圆直径 (31mm)
    
    # 3. 绘制齿轮主体 (简化为分度圆柱，符合建模指令要求)
    # 指令要求：在XY平面绘制分度圆36mm的齿轮廓形，拉伸20mm
    sketch_main = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(0, 0, d / 2.0, "XY")
    extrude_feature = sw_doc.extrude(sketch_main, depth=width, single_direction=True)
    print(f"主体拉伸完成，直径: {d*1000}mm, 深度: {width*1000}mm")

    # 4. 切除中心通孔
    # 在顶面或XY面切除
    sketch_hole = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(0, 0, hole_dia / 2.0, "XY")
    sw_doc.extrude_cut(sketch_hole, depth=width, single_direction=True)
    print(f"中心孔切除完成，直径: {hole_dia*1000}mm")

    # 5. 创建装配接口
    # 接口1: bottom_face (装配基准面，法线 -Z)
    # 零件在XY平面创建，向+Z拉伸，故XY平面即为 bottom_face
    sw_doc.create_ref_plane("XY", 0, target_plane_name="bottom_face")
    
    # 接口2: center_axis (旋转中心轴，沿 local Z)
    sw_doc.create_axis((0, 0, 0), (0, 0, width), axis_name="center_axis")
    print("装配接口 (bottom_face, center_axis) 创建完成")

    # 6. 保存零件
    save_success = sw_doc.save_as(model_path)
    if save_success:
        print(f"零件成功保存至: {model_path}")
    else:
        print("零件保存失败")

if __name__ == "__main__":
    main()