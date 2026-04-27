# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Cell_Holder"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 2. 定义参数 (单位: m)
    L = 0.135      # Length 135mm
    W = 0.070      # Width 70mm
    H = 0.065      # Height 65mm
    hole_dia = 0.0182 # Hole Diameter 18.2mm
    pitch_x = 0.032   # Pitch X 32mm
    pitch_y = 0.032   # Pitch Y 32mm
    
    # 计算孔位中心坐标 (相对于原点居中)
    # 4列 x 方向: -1.5*px, -0.5*px, 0.5*px, 1.5*px
    # 2行 y 方向: -0.5*py, 0.5*py
    px_half = pitch_x / 2.0
    py_half = pitch_y / 2.0
    
    col_offsets = [-1.5 * pitch_x, -0.5 * pitch_x, 0.5 * pitch_x, 1.5 * pitch_x]
    row_offsets = [-0.5 * pitch_y, 0.5 * pitch_y]
    
    # 3. 创建主体基座
    print("步骤 1: 创建主体基座")
    sketch_base = sw_doc.insert_sketch_on_plane("XY")
    # 绘制中心矩形，长L宽W
    sw_doc.create_centre_rectangle(
        center_x=0, 
        center_y=0, 
        width=L, 
        height=W, 
        sketch_ref="XY"
    )
    # 拉伸高度 H
    base_body = sw_doc.extrude(sketch_base, depth=H, single_direction=True, merge=True)
    print("主体基座创建完成")

    # 4. 创建电池孔切除
    print("步骤 2: 创建电池孔切除")
    # 在顶面 (Z=H) 创建草图用于切除
    # 为了准确定位，我们创建一个偏移平面或者直接利用现有几何。
    # 这里我们在 XY 平面画孔，然后向上切除贯穿，或者在 Z=H 平面画孔向下切除。
    # 选择在 Z=H 平面画孔，向下切除深度 H (或更多以确保贯穿)
    
    # 创建顶部参考平面用于草图
    top_plane = sw_doc.create_workplane_p_d("XY", offset_val=H)
    sketch_holes = sw_doc.insert_sketch_on_plane(top_plane)
    
    # 绘制8个圆
    for r_idx, y_off in enumerate(row_offsets):
        for c_idx, x_off in enumerate(col_offsets):
            sw_doc.create_circle(
                center_x=x_off,
                center_y=y_off,
                radius=hole_dia / 2.0,
                sketch_ref="XY" # 注意：虽然是在top_plane上，但坐标系映射通常沿用XY逻辑，除非API有特殊说明。根据KB，sketch_ref需与平面方向一致，top_plane平行于XY，故用XY
            )
            
    # 执行拉伸切除，向下切除深度 H + 小余量确保完全切穿
    cut_feature = sw_doc.extrude_cut(sketch_holes, depth=-(H + 0.001), single_direction=True)
    print("电池孔切除完成")

    # 5. 创建装配接口 (Faces & Axes)
    print("步骤 3: 创建装配接口")
    
    # --- Face Interfaces ---
    # face_bottom_support: 底面 (Z=0)，法向 -Z
    # 由于实体是从 Z=0 拉伸到 Z=H，底面即为 Z=0 处的面。
    # 我们可以通过创建参考平面来标记这个面，或者直接使用几何点选择。
    # 为了稳健性，创建命名参考平面作为接口代理或直接记录点位。
    # KB建议：优先通过创建命名参考面暴露接口。
    
    # 创建底部支撑面参考 (位于 Z=0)
    ref_plane_bottom = sw_doc.create_ref_plane("XY", offset_val=0.0, target_plane_name="face_bottom_support")
    
    # 创建顶部开口面参考 (位于 Z=H)
    ref_plane_top = sw_doc.create_ref_plane("XY", offset_val=H, target_plane_name="face_top_open")
    
    # --- Axis Interfaces ---
    # 需要为每个电池孔创建中心轴
    # axis_cell_1_1 到 axis_cell_2_4
    # 轴沿 Z 方向，穿过孔中心
    
    axis_names = [
        ["axis_cell_1_1", "axis_cell_1_2", "axis_cell_1_3", "axis_cell_1_4"], # Row 1 (y < 0)
        ["axis_cell_2_1", "axis_cell_2_2", "axis_cell_2_3", "axis_cell_2_4"]  # Row 2 (y > 0)
    ]
    
    for r_idx, y_off in enumerate(row_offsets):
        for c_idx, x_off in enumerate(col_offsets):
            pt1 = (x_off, y_off, 0.0)
            pt2 = (x_off, y_off, H)
            name = axis_names[r_idx][c_idx]
            sw_doc.create_axis(pt1, pt2, axis_name=name)
            
    print("所有装配接口创建完成")

    # 6. 保存文件
    output_path = r"D:\a_src\python\sw_agent\agent_output\Battery_Pack_2P4S_Assembly-20260423_155518\parts\cell_holder\cell_holder.SLDPRT"
    print(f"正在保存至: {output_path}")
    success = sw_doc.save_as(output_path)
    
    if success:
        print("零件建模与保存成功。")
    else:
        print("零件保存失败。")

if __name__ == "__main__":
    main()