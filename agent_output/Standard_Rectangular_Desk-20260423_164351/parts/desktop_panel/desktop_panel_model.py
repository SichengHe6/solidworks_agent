# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与创建零件文档
    print("正在启动 SolidWorks 应用...")
    app = SldWorksApp()
    
    part_name = "Desktop Panel"
    print(f"正在创建零件: {part_name}")
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    # 2. 定义尺寸参数 (单位: m)
    # 原始尺寸: Length=1200mm, Width=600mm, Thickness=25mm
    length_m = 1.200
    width_m = 0.600
    thickness_m = 0.025
    
    # 3. 建模步骤
    print("开始在 XY 平面绘制草图...")
    sketch1 = sw_doc.insert_sketch_on_plane("XY")
    
    # 绘制中心矩形，长1.2m，宽0.6m
    # create_centre_rectangle(center_x, center_y, width, height, sketch_ref)
    sw_doc.create_centre_rectangle(
        center_x=0.0, 
        center_y=0.0, 
        width=length_m, 
        height=width_m, 
        sketch_ref="XY"
    )
    
    print("执行双向拉伸特征，确保几何中心位于原点...")
    # 向 +Z 和 -Z 方向各拉伸一半厚度，使底面位于 Z = -thickness/2
    # single_direction=False 表示双向拉伸
    extrude_feat = sw_doc.extrude(sketch1, depth=thickness_m, single_direction=False, merge=True)
    
    # 4. 创建装配接口 (参考面/轴)
    print("创建装配参考接口...")
    
    # 接口 1: face_bottom (底面)
    # 底面位于 Z = -0.0125
    ref_plane_bottom = sw_doc.create_ref_plane(
        plane="XY", 
        offset_val=-thickness_m / 2, 
        target_plane_name="face_bottom"
    )
    
    # 接口 2: face_top (顶面)
    # 顶面位于 Z = 0.0125
    ref_plane_top = sw_doc.create_ref_plane(
        plane="XY", 
        offset_val=thickness_m / 2, 
        target_plane_name="face_top"
    )
    
    # 接口 3: 角点参考 (Points)
    # 规划中要求的点名称: corner_fl_xp_yp, corner_fl_xp_ym, corner_fl_xm_yp, corner_fl_xm_ym
    # 由于 API 没有直接的“命名点”，我们使用短的参考轴来标记这些位置，并赋予指定的名称。
    # 桌腿安装位置距离边缘 50mm (0.05m)。
    # X 坐标: +/- (length/2 - 0.05) = +/- (0.6 - 0.05) = +/- 0.55 m
    # Y 坐标: +/- (width/2 - 0.05) = +/- (0.3 - 0.05) = +/- 0.25 m
    # Z 坐标: 底面高度 -0.0125 m
    
    leg_offset_x = 0.55
    leg_offset_y = 0.25
    z_ref = -thickness_m / 2
    
    # 右前角 (X+, Y+) -> corner_fl_xp_yp
    sw_doc.create_axis(
        pt1=(leg_offset_x, leg_offset_y, z_ref),
        pt2=(leg_offset_x, leg_offset_y, z_ref + 0.001), # 微小延伸以形成轴
        axis_name="corner_fl_xp_yp"
    )
    
    # 右后角 (X+, Y-) -> corner_fl_xp_ym
    sw_doc.create_axis(
        pt1=(leg_offset_x, -leg_offset_y, z_ref),
        pt2=(leg_offset_x, -leg_offset_y, z_ref + 0.001),
        axis_name="corner_fl_xp_ym"
    )
    
    # 左前角 (X-, Y+) -> corner_fl_xm_yp
    sw_doc.create_axis(
        pt1=(-leg_offset_x, leg_offset_y, z_ref),
        pt2=(-leg_offset_x, leg_offset_y, z_ref + 0.001),
        axis_name="corner_fl_xm_yp"
    )
    
    # 左后角 (X-, Y-) -> corner_fl_xm_ym
    sw_doc.create_axis(
        pt1=(-leg_offset_x, -leg_offset_y, z_ref),
        pt2=(-leg_offset_x, -leg_offset_y, z_ref + 0.001),
        axis_name="corner_fl_xm_ym"
    )

    # 5. 保存文件
    output_path = r"D:\a_src\python\sw_agent\agent_output\Standard_Rectangular_Desk-20260423_164351\parts\desktop_panel\desktop_panel.SLDPRT"
    print(f"正在保存零件到: {output_path}")
    success = sw_doc.save_as(output_path)
    
    if success:
        print("零件建模完成并保存成功。")
    else:
        print("零件保存失败。")

if __name__ == "__main__":
    main()