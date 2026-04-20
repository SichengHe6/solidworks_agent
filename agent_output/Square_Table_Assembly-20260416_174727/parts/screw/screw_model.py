# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化与创建零件
    # 零件名称：简化沉头螺钉 (screw)
    # 尺寸说明：头部直径10mm(R5), 杆部直径8mm(R4), 总长60mm
    model_path = r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_174727\parts\screw\screw.SLDPRT"
    
    app = SldWorksApp()
    sw_doc = PartDoc(app.createAndActivate_sw_part("screw"))
    print("开始建模：简化沉头螺钉")

    # 2. 绘制旋转剖面
    # 建模指令：在XZ面绘制剖面并绕Z轴旋转
    # 坐标换算 (mm -> m):
    # (0, 0) -> (0, 0)
    # (4, 0) -> (0.004, 0)  # 杆部半径
    # (4, -50) -> (0.004, -0.050) # 杆部长度
    # (5, -50) -> (0.005, -0.050) # 头部半径起始
    # (5, -60) -> (0.005, -0.060) # 头部顶端
    # (0, -60) -> (0, -0.060) # 中心轴点
    
    sketch = sw_doc.insert_sketch_on_plane("XZ")
    
    # 绘制闭合轮廓
    points = [
        (0.0, 0.0),
        (0.004, 0.0),
        (0.004, -0.050),
        (0.005, -0.050),
        (0.005, -0.060),
        (0.0, -0.060),
        (0.0, 0.0)
    ]
    sw_doc.create_lines(points, "XZ")
    
    # 创建旋转中心轴 (构造线)
    sw_doc.create_construction_line(0.0, 0.0, 0.0, -0.060, "XZ")
    
    # 执行旋转特征
    revolve_feat = sw_doc.revolve(sketch, angle=360)
    print("旋转特征创建完成")

    # 3. 创建装配接口
    # 接口1: screw_axis (螺钉中心轴)
    # 沿 Z 轴方向
    sw_doc.create_axis((0, 0, 0), (0, 0, -0.060), axis_name="screw_axis")
    
    # 接口2: head_bottom_face (头下表面)
    # 位于 Z = -50mm 处，法向朝向 -Z
    sw_doc.create_ref_plane("XY", -0.050, target_plane_name="head_bottom_face")
    
    print("装配接口 (screw_axis, head_bottom_face) 创建完成")

    # 4. 保存零件
    save_success = sw_doc.save_as(model_path)
    if save_success:
        print(f"零件成功保存至: {model_path}")
    else:
        print("零件保存失败")

if __name__ == "__main__":
    main()