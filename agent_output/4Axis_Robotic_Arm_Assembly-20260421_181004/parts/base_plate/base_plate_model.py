# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Base Plate"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 2. 定义尺寸 (单位: m)
    block_w = 0.200  # 200 mm
    block_h = 0.200  # 200 mm
    block_d = 0.100  # 100 mm
    
    boss1_dia = 0.080  # 80 mm
    boss1_h = 0.020    # 20 mm
    
    boss2_dia = 0.040  # 40 mm
    boss2_h = 0.030    # 30 mm

    # 3. 创建底座主体 (Block)
    # 在 XY 平面绘制中心矩形
    sketch_base = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(
        center_x=0, 
        center_y=0, 
        width=block_w, 
        height=block_h, 
        sketch_ref="XY"
    )
    # 拉伸主体，沿 +Z 方向
    extrude_base = sw_doc.extrude(sketch_base, depth=block_d, single_direction=True)
    print("底座主体创建完成")

    # 4. 创建第一级凸台 (Boss Stage 1)
    # 需要在底座顶面 (Z = block_d) 上创建草图
    # 使用 create_workplane_p_d 创建一个偏移平面，或者直接在现有面上插入草图
    # 这里为了稳定性，先创建一个参考平面，或者直接利用 API 的 insert_sketch_on_plane 如果支持面选择
    # 根据 API 描述，insert_sketch_on_plane 接受 plane 对象或名称。
    # 我们可以先创建一个位于 Z=0.1 的平面，或者尝试直接引用。
    # 更稳健的方式：创建偏移平面
    plane_top_1 = sw_doc.create_workplane_p_d("XY", offset_val=block_d)
    
    sketch_boss1 = sw_doc.insert_sketch_on_plane(plane_top_1)
    sw_doc.create_circle(
        center_x=0, 
        center_y=0, 
        radius=boss1_dia / 2, 
        sketch_ref="XY" # 注意：虽然是在偏移平面上，但局部坐标系通常仍映射为 XY 逻辑，除非API有特殊规定。根据知识库，sketch_ref 需与当前草图平面方向一致。偏移自 XY 的平面，其局部坐标通常也是 XY。
    )
    # 拉伸第一级凸台
    extrude_boss1 = sw_doc.extrude(sketch_boss1, depth=boss1_h, single_direction=True)
    print("第一级凸台创建完成")

    # 5. 创建第二级凸台 (Boss Stage 2)
    # 在第一级凸台顶面 (Z = block_d + boss1_h) 上创建草图
    z_level_2 = block_d + boss1_h
    plane_top_2 = sw_doc.create_workplane_p_d("XY", offset_val=z_level_2)
    
    sketch_boss2 = sw_doc.insert_sketch_on_plane(plane_top_2)
    sw_doc.create_circle(
        center_x=0, 
        center_y=0, 
        radius=boss2_dia / 2, 
        sketch_ref="XY"
    )
    # 拉伸第二级凸台
    extrude_boss2 = sw_doc.extrude(sketch_boss2, depth=boss2_h, single_direction=True)
    print("第二级凸台创建完成")

    # 6. 创建装配接口 (Interfaces)
    
    # 6.1 面接口: mount_face_bottom (底面, Z=0)
    # 创建参考平面用于标识底面，虽然底面是基准面 XY，但为了命名清晰，可以重命名或创建重合平面
    # 这里我们创建一个与 XY 重合的平面并命名为 mount_face_bottom，方便后续装配引用
    ref_plane_bottom = sw_doc.create_ref_plane("XY", offset_val=0, target_plane_name="mount_face_bottom")
    
    # 6.2 面接口: boss_top_face (顶面, Z = block_d + boss1_h + boss2_h)
    z_top_total = block_d + boss1_h + boss2_h
    ref_plane_top = sw_doc.create_ref_plane("XY", offset_val=z_top_total, target_plane_name="boss_top_face")
    
    # 6.3 轴接口: main_axis_z (中心轴)
    # 创建从 (0,0,0) 到 (0,0,1) 的轴，代表 Z 轴方向
    axis_main = sw_doc.create_axis(
        pt1=(0, 0, 0), 
        pt2=(0, 0, 1), 
        axis_name="main_axis_z"
    )
    print("装配接口创建完成")

    # 7. 保存文件
    model_path = r"D:\a_src\python\sw_agent\agent_output\4Axis_Robotic_Arm_Assembly-20260421_181004\parts\base_plate\base_plate.SLDPRT"
    success = sw_doc.save_as(model_path)
    
    if success:
        print(f"模型已成功保存至: {model_path}")
    else:
        print("模型保存失败")

if __name__ == "__main__":
    main()