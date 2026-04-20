# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化与零件创建
    app = SldWorksApp()
    part_id = "forearm"
    part_name = "小臂"
    model_file = r"D:\a_src\python\sw_agent\agent_output\4_Axis_Serial_Robot_Arm-20260416_175529\parts\forearm\forearm.SLDPRT"
    
    print(f"开始建模零件: {part_name} (ID: {part_id})")
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_id))

    # 2. 尺寸定义 (单位换算: mm -> m)
    length = 300 / 1000.0
    width = 40 / 1000.0
    hole_diam = 20 / 1000.0
    hole_radius = hole_diam / 2.0
    
    # 3. 建模主体：在YZ平面绘制40x40矩形拉伸300mm
    # 这里的 ZY 对应 SolidWorks 的右视基准面
    print(f"[{part_name}] 步骤 1: 创建主体矩形连杆结构...")
    sketch_main = sw_doc.insert_sketch_on_plane("ZY")
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=width, height=width, sketch_ref="ZY")
    # 向 X 正方向拉伸
    main_body = sw_doc.extrude(sketch_main, depth=length, single_direction=True)

    # 4. 创建后端横向轴孔 (axis_3_conn)
    # 位置：在后端 (X=20mm 处)，沿 Y 轴方向贯穿
    print(f"[{part_name}] 步骤 2: 创建后端横向轴孔 (axis_3_conn)...")
    # 在 XZ 平面（上视基准面）绘图，切除 Y 方向
    sketch_hole_back = sw_doc.insert_sketch_on_plane("XZ")
    # 轴孔中心位于 X=20mm (0.02m)
    sw_doc.create_circle(center_x=0.02, center_y=0, radius=hole_radius, sketch_ref="XZ")
    sw_doc.extrude_cut(sketch_hole_back, depth=width * 2, single_direction=False)

    # 5. 创建前端纵向轴孔 (axis_4_rot)
    # 位置：在前端 (X=300mm 处) 的端面中心，沿 X 轴方向切入
    print(f"[{part_name}] 步骤 3: 创建前端纵向轴孔 (axis_4_rot)...")
    # 创建位于 X=length 的偏移平面
    end_face_plane = sw_doc.create_workplane_p_d("ZY", length)
    sketch_hole_front = sw_doc.insert_sketch_on_plane(end_face_plane)
    sw_doc.create_circle(center_x=0, center_y=0, radius=hole_radius, sketch_ref="ZY")
    # 向内切除 30mm
    sw_doc.extrude_cut(sketch_hole_front, depth=-0.03, single_direction=True)

    # 6. 创建装配接口 (参考轴与参考面)
    print(f"[{part_name}] 步骤 4: 定义装配接口 (Axes & Planes)...")
    
    # 接口 axis_3_conn: 后端横向轴 (沿 Y 方向)
    sw_doc.create_axis((0.02, -width, 0), (0.02, width, 0), axis_name="axis_3_conn")
    
    # 接口 axis_4_rot: 前端纵向轴 (沿 X 方向)
    sw_doc.create_axis((length - 0.05, 0, 0), (length + 0.05, 0, 0), axis_name="axis_4_rot")
    
    # 接口 joint_face_3_conn: 与大臂连接的侧平面 (Normal -Y)
    # 矩形宽度40mm，中心在0，侧面在 Y = -20mm
    sw_doc.create_ref_plane("XZ", -width/2, target_plane_name="joint_face_3_conn")
    
    # 接口 end_face: 末端安装面 (Normal +X)
    sw_doc.create_ref_plane("ZY", length, target_plane_name="end_face")

    # 7. 保存零件
    print(f"[{part_name}] 步骤 5: 保存零件至 {model_file}")
    save_status = sw_doc.save_as(model_file)
    if save_status:
        print(f"[{part_name}] 建模并保存成功。")
    else:
        print(f"[{part_name}] 保存失败，请检查路径权限。")

if __name__ == "__main__":
    main()