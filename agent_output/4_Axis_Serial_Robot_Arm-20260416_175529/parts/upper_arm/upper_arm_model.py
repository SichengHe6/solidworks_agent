# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化与创建零件
    # 尺寸定义 (单位换算: mm -> m)
    length = 0.400  # 400mm
    width = 0.060   # 60mm
    hole_diam = 0.020 # 20mm
    model_path = r"D:\a_src\python\sw_agent\agent_output\4_Axis_Serial_Robot_Arm-20260416_175529\parts\upper_arm\upper_arm.SLDPRT"
    
    app = SldWorksApp()
    sw_doc = PartDoc(app.createAndActivate_sw_part("upper_arm"))
    print("开始建模零件: upper_arm (大臂)")

    # 2. 创建主体结构 (60x60x400mm 矩形柱)
    # 在 XY 平面绘制中心矩形并向上拉伸
    sketch1 = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=width, height=width, sketch_ref="XY")
    sw_doc.extrude(sketch1, depth=length, single_direction=True)
    print(f"主体拉伸完成: 高度 {length}m")

    # 3. 创建底部中心轴孔 (axis_1_conn 接口)
    # 在底面 (XY平面) 切除深度为 50mm 的孔或通孔，此处按指令创建轴孔
    sketch2 = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=hole_diam/2, sketch_ref="XY")
    sw_doc.extrude_cut(sketch2, depth=0.05, single_direction=True) # 深度50mm
    print("底部轴孔切除完成")

    # 4. 创建底部横向贯穿轴孔 (axis_2_rot 肩部俯仰轴)
    # 在距离底部一定高度（例如 30mm）的 XZ 平面切除
    sketch3 = sw_doc.insert_sketch_on_plane("XZ")
    # 坐标说明：XZ平面中，水平为X，垂直为Z。我们在 Z=0.03 处画圆
    sw_doc.create_circle(center_x=0, center_y=0.03, radius=hole_diam/2, sketch_ref="XZ")
    sw_doc.extrude_cut(sketch3, depth=width, single_direction=False) # 双向切除贯穿宽度
    print("底部横向轴孔 (axis_2_rot) 完成")

    # 5. 创建顶部横向贯穿轴孔 (axis_3_rot 肘部俯仰轴)
    # 在距离顶部一定距离（例如 370mm 处，即 length - 0.03）的 XZ 平面切除
    sketch4 = sw_doc.insert_sketch_on_plane("XZ")
    sw_doc.create_circle(center_x=0, center_y=length - 0.03, radius=hole_diam/2, sketch_ref="XZ")
    sw_doc.extrude_cut(sketch4, depth=width, single_direction=False)
    print("顶部横向轴孔 (axis_3_rot) 完成")

    # 6. 创建装配接口 (Reference Interfaces)
    
    # 轴接口 1: axis_1_conn (连接底座，沿 Z 轴)
    sw_doc.create_axis((0, 0, 0), (0, 0, 0.05), axis_name="axis_1_conn")
    
    # 轴接口 2: axis_2_rot (肩部俯仰，沿 Y 轴)
    sw_doc.create_axis((0, -width/2, 0.03), (0, width/2, 0.03), axis_name="axis_2_rot")
    
    # 轴接口 3: axis_3_rot (肘部俯仰，沿 Y 轴)
    sw_doc.create_axis((0, -width/2, length - 0.03), (0, width/2, length - 0.03), axis_name="axis_3_rot")

    # 面接口 1: arm_bottom_face (底面，法线 -Z)
    # 直接使用 XY 基准面作为参考
    sw_doc.create_ref_plane("XY", 0, target_plane_name="arm_bottom_face")
    
    # 面接口 2: joint_face_3 (侧平面，用于连接小臂，法线 +Y)
    # 偏移 XZ 平面 width/2
    sw_doc.create_ref_plane("XZ", width/2, target_plane_name="joint_face_3")

    # 7. 保存零件
    save_success = sw_doc.save_as(model_path)
    if save_success:
        print(f"零件成功保存至: {model_path}")
    else:
        print("零件保存失败")

if __name__ == "__main__":
    main()