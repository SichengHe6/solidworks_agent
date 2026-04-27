# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    print("启动 SolidWorks 应用...")
    app = SldWorksApp()
    
    part_name = "Cylindrical Leg"
    print(f"创建并激活零件: {part_name}")
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    # 2. 定义参数 (单位: 米)
    # 直径 40mm -> 半径 20mm = 0.02m
    radius = 0.02 
    # 高度 725mm = 0.725m
    height = 0.725
    
    # 3. 建模步骤
    print("开始在 XY 平面绘制草图...")
    sketch = sw_doc.insert_sketch_on_plane("XY")
    
    # 绘制中心圆，圆心在 (0,0)，半径 0.02m
    print(f"绘制圆形: 中心(0,0), 半径{radius}m")
    sw_doc.create_circle(center_x=0, center_y=0, radius=radius, sketch_ref="XY")
    
    # 拉伸生成圆柱体
    print(f"向 +Z 方向拉伸，深度: {height}m")
    extrude_feat = sw_doc.extrude(sketch, depth=height, single_direction=True, merge=True)
    
    # 4. 创建装配接口 (参考面与参考轴)
    print("创建装配接口...")
    
    # 接口: face_top (顶面)
    # 顶面位于 Z = height 处。创建一个偏移平面作为参考，命名为 face_top
    # 注意：SolidWorks 中通常通过选择面来配合，但为了代码化引用，我们创建命名参考平面
    # 这里创建两个参考平面分别对应 Top 和 Bottom 的几何位置，方便后续装配约束引用
    try:
        ref_plane_top = sw_doc.create_ref_plane(plane="XY", offset_val=height, target_plane_name="face_top")
        print("已创建参考平面: face_top")
    except Exception as e:
        print(f"创建 face_top 参考平面失败: {e}")

    # 接口: face_bottom (底面)
    # 底面位于 Z = 0 处 (即 XY 平面本身)。我们可以直接重命名或创建偏移为0的平面
    # 为了统一接口风格，创建一个偏移为0的平面并命名
    try:
        ref_plane_bottom = sw_doc.create_ref_plane(plane="XY", offset_val=0, target_plane_name="face_bottom")
        print("已创建参考平面: face_bottom")
    except Exception as e:
        print(f"创建 face_bottom 参考平面失败: {e}")

    # 接口: axis_center (中心轴)
    # 沿局部 Z 轴，从 (0,0,0) 到 (0,0,height)
    try:
        axis_center = sw_doc.create_axis(pt1=(0, 0, 0), pt2=(0, 0, height), axis_name="axis_center")
        print("已创建参考轴: axis_center")
    except Exception as e:
        print(f"创建 axis_center 参考轴失败: {e}")

    # 5. 保存零件
    model_path = r"D:\a_src\python\sw_agent\agent_output\Standard_Rectangular_Desk-20260423_164351\parts\cylindrical_leg\cylindrical_leg.SLDPRT"
    print(f"保存零件至: {model_path}")
    success = sw_doc.save_as(model_path)
    
    if success:
        print("零件建模与保存成功。")
    else:
        print("零件保存失败。")

if __name__ == "__main__":
    main()