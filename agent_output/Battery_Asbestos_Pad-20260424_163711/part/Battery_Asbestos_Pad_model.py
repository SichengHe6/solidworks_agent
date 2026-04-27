# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    print("正在启动 SolidWorks 应用...")
    app = SldWorksApp()
    
    part_name = "Battery_Asbestos_Pad"
    print(f"创建并激活零件: {part_name}")
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    # 2. 定义参数 (单位转换为米)
    radius_mm = 50.0
    thickness_mm = 10.0
    
    radius_m = radius_mm / 1000.0  # 0.05 m
    thickness_m = thickness_mm / 1000.0  # 0.01 m
    
    print(f"建模参数: 半径={radius_m}m, 厚度={thickness_m}m")
    
    # 3. 建模步骤
    
    # 3.1 在 XY 平面绘制草图
    print("在 XY 平面插入草图...")
    sketch_plane = "XY"
    sketch = sw_doc.insert_sketch_on_plane(sketch_plane)
    
    # 3.2 绘制圆形轮廓 (中心在原点)
    print("绘制圆形轮廓...")
    center_x = 0.0
    center_y = 0.0
    sw_doc.create_circle(center_x=center_x, center_y=center_y, radius=radius_m, sketch_ref=sketch_plane)
    
    # 3.3 拉伸生成圆柱体
    print("执行拉伸特征...")
    # 沿 Z 轴正向拉伸，单向，合并实体
    extrude_feature = sw_doc.extrude(
        sketch=sketch, 
        depth=thickness_m, 
        single_direction=True, 
        merge=True
    )
    
    # 4. 接口处理
    # 根据 spec，该零件暂无特定命名接口要求 (faces/axes/points 为空)。
    # 但为了装配通用性，通常保留默认基准面即可。
    # 如果需要暴露顶面或底面作为装配参考，可以在后续装配阶段通过坐标选择，
    # 或者在此处创建命名参考面。鉴于 spec 中 interfaces 为空，此处不额外创建命名参考几何，
    # 保持模型简洁。若后续需要，可基于 Z=0 和 Z=thickness_m 创建参考面。
    
    # 5. 保存文件
    model_file_path = r"D:\a_src\python\sw_agent\agent_output\Battery_Asbestos_Pad-20260424_163711\part\Battery_Asbestos_Pad.SLDPRT"
    print(f"尝试保存零件至: {model_file_path}")
    
    success = sw_doc.save_as(model_file_path)
    
    if success:
        print("零件建模与保存成功。")
    else:
        print("零件保存失败，请检查路径权限或 SolidWorks 状态。")

if __name__ == "__main__":
    main()