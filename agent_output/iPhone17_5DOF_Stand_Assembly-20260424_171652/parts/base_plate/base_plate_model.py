# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Base Plate"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 2. 定义尺寸参数 (单位: m)
    base_diameter = 0.100      # 100 mm
    base_height = 0.020        # 20 mm
    boss_diameter = 0.030      # 30 mm
    boss_height = 0.010        # 10 mm
    
    # 计算半径
    base_radius = base_diameter / 2.0
    boss_radius = boss_diameter / 2.0

    # 3. 创建底座主体 (Base Body)
    # 在 XY 平面绘制圆，向上拉伸
    print("步骤 1: 创建底座主体")
    sketch_base = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=base_radius, sketch_ref="XY")
    extrude_base = sw_doc.extrude(sketch_base, depth=base_height, single_direction=True, merge=True)
    
    # 4. 创建顶部凸台 (Top Boss)
    # 需要在底座顶面创建草图。由于封装限制，我们通常通过偏移平面或直接在原基准面拉伸并合并来实现。
    # 这里采用更稳健的方式：创建一个偏移平面作为凸台的草图基准，或者如果API支持选择面，则选面。
    # 根据API描述，insert_sketch_on_plane 接受 plane 对象或名称。
    # 为了精确控制位置，我们创建一个位于 Z = base_height 的参考平面。
    print("步骤 2: 创建顶部凸台")
    top_plane = sw_doc.create_workplane_p_d(plane="XY", offset_val=base_height)
    
    sketch_boss = sw_doc.insert_sketch_on_plane(top_plane)
    sw_doc.create_circle(center_x=0, center_y=0, radius=boss_radius, sketch_ref="XY") # 注意：虽然平面是偏移的，但sketch_ref通常仍指代局部坐标系的投影方向，这里保持XY逻辑
    extrude_boss = sw_doc.extrude(sketch_boss, depth=boss_height, single_direction=True, merge=True)

    # 5. 创建装配接口 (Interfaces)
    
    # 5.1 面接口: bottom_face
    # 底面位于 Z=0，法向 -Z。我们可以通过创建一个重合于XY平面的参考面来标记它，或者直接依赖几何特征。
    # 为了明确接口，创建一个命名参考面。
    print("步骤 3: 创建接口参考几何")
    
    # bottom_face: 对应 Z=0 平面
    ref_bottom_face = sw_doc.create_ref_plane(plane="XY", offset_val=0.0, target_plane_name="bottom_face")
    
    # top_mount_face: 对应凸台顶面，位于 Z = base_height + boss_height
    top_mount_z = base_height + boss_height
    ref_top_mount_face = sw_doc.create_ref_plane(plane="XY", offset_val=top_mount_z, target_plane_name="top_mount_face")
    
    # 5.2 轴接口: central_axis_z
    # 穿过圆心 (0,0)，沿 Z 方向
    # 起点 (0,0,0), 终点 (0,0,1) 或任意长度
    ref_central_axis = sw_doc.create_axis(
        pt1=(0.0, 0.0, 0.0), 
        pt2=(0.0, 0.0, 0.1), 
        axis_name="central_axis_z"
    )

    # 6. 保存文件
    model_path = r"D:\a_src\python\sw_agent\agent_output\iPhone17_5DOF_Stand_Assembly-20260424_171652\parts\base_plate\base_plate.SLDPRT"
    print(f"保存模型至: {model_path}")
    success = sw_doc.save_as(model_path)
    
    if success:
        print("建模完成并保存成功。")
    else:
        print("保存失败，请检查路径权限或SolidWorks状态。")

if __name__ == "__main__":
    main()