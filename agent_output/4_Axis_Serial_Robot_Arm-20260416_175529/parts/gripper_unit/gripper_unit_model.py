# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    """
    零件建模：夹爪组件 (gripper_unit)
    功能：执行抓取动作，提供与小臂末端连接的旋转轴接口。
    """
    # 1. 路径与参数定义
    model_file = r"D:\a_src\python\sw_agent\agent_output\4_Axis_Serial_Robot_Arm-20260416_175529\parts\gripper_unit\gripper_unit.SLDPRT"
    part_id = "gripper_unit"
    
    # 尺寸换算 (mm -> m)
    body_width = 0.05   # 50mm
    body_height = 0.05  # 50mm
    body_length = 0.1   # 100mm
    conn_radius = 0.01  # 直径20mm -> 半径10mm
    conn_length = 0.02  # 凸起轴长度设为20mm

    print(f"开始零件建模任务: {part_id}")
    app = SldWorksApp()
    
    # 2. 创建并激活零件文档
    sw_part_obj = app.createAndActivate_sw_part(part_id)
    if not sw_part_obj:
        print(f"错误: 无法创建零件文档 {part_id}")
        return
    sw_doc = PartDoc(sw_part_obj)

    # 3. 建模主体：在 YZ 平面绘制 50x50mm 矩形，向 X 正方向拉伸 100mm
    print(f"[{part_id}] 正在创建主体特征...")
    sketch_main = sw_doc.insert_sketch_on_plane("YZ")
    if sketch_main:
        sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=body_width, height=body_height, sketch_ref="YZ")
        # 显式退出草图编辑模式
        sw_doc.partDoc.SketchManager.InsertSketch(True)
        sw_doc.extrude(sketch_main, depth=body_length, single_direction=True)
    else:
        print(f"[{part_id}] 错误: 无法在 YZ 平面创建主体草图")
        return

    # 4. 建模后端凸起轴：在 YZ 平面（X=0）绘制直径 20mm 圆，向 X 负方向拉伸
    print(f"[{part_id}] 正在创建后端连接轴特征...")
    sketch_conn = sw_doc.insert_sketch_on_plane("YZ")
    if sketch_conn:
        sw_doc.create_circle(center_x=0, center_y=0, radius=conn_radius, sketch_ref="YZ")
        sw_doc.partDoc.SketchManager.InsertSketch(True)
        # 向 X 负方向拉伸，depth 取负值
        sw_doc.extrude(sketch_conn, depth=-conn_length, single_direction=True)
    else:
        print(f"[{part_id}] 错误: 无法在 YZ 平面创建连接轴草图")

    # 5. 创建装配接口 (Interfaces)
    print(f"[{part_id}] 正在配置装配接口...")
    
    # 5.1 轴接口 axis_4_conn: 沿 X 轴方向，用于与小臂末端同心配合
    # 起点为凸起轴末端，终点为主体末端
    sw_doc.create_axis(pt1=(-conn_length, 0, 0), pt2=(body_length, 0, 0), axis_name="axis_4_conn")
    
    # 5.2 面接口 mount_face: 与小臂末端贴合的面 (X=0 平面)
    # 基于 YZ 基准面偏移 0m
    sw_doc.create_ref_plane(plane="YZ", offset_val=0, target_plane_name="mount_face")

    # 6. 保存零件
    print(f"[{part_id}] 正在保存模型至: {model_file}")
    success = sw_doc.save_as(model_file)
    if success:
        print(f"[{part_id}] 建模与保存成功。")
    else:
        print(f"[{part_id}] 错误: 保存失败。")

if __name__ == "__main__":
    main()