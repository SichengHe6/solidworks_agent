# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    print("正在启动 SolidWorks 应用...")
    app = SldWorksApp()
    
    part_name = "Standard_Asbestos_Gasket"
    print(f"创建并激活零件: {part_name}")
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    # 2. 定义尺寸参数 (转换为米)
    outer_diameter_mm = 100.0
    inner_diameter_mm = 50.0
    thickness_mm = 2.0
    
    outer_radius_m = (outer_diameter_mm / 2.0) / 1000.0  # 0.05 m
    inner_radius_m = (inner_diameter_mm / 2.0) / 1000.0  # 0.025 m
    thickness_m = thickness_mm / 1000.0                   # 0.002 m
    
    print(f"外径: {outer_diameter_mm} mm -> {outer_radius_m*2} m")
    print(f"内径: {inner_diameter_mm} mm -> {inner_radius_m*2} m")
    print(f"厚度: {thickness_mm} mm -> {thickness_m} m")

    # 3. 建模步骤
    
    # 3.1 在 XY 平面创建草图
    print("在 XY 平面插入草图...")
    sketch_plane = "XY"
    sketch = sw_doc.insert_sketch_on_plane(sketch_plane)
    
    # 3.2 绘制外圆
    print("绘制外圆...")
    sw_doc.create_circle(center_x=0, center_y=0, radius=outer_radius_m, sketch_ref=sketch_plane)
    
    # 3.3 绘制内圆
    print("绘制内圆...")
    sw_doc.create_circle(center_x=0, center_y=0, radius=inner_radius_m, sketch_ref=sketch_plane)
    
    # 注意：SolidWorks 拉伸时，如果草图中有两个同心圆，默认会生成环形实体（外轮廓减去内轮廓），
    # 只要它们都是封闭轮廓且没有额外的构造线干扰。这里直接拉伸即可得到垫片形状。
    
    # 3.4 拉伸形成实体
    print("执行拉伸特征...")
    extrude_feature = sw_doc.extrude(
        sketch=sketch, 
        depth=thickness_m, 
        single_direction=True, 
        merge=True
    )
    
    if extrude_feature is None:
        print("错误: 拉伸特征创建失败")
        return

    # 4. 接口处理
    # 根据 spec，该零件暂无特定命名接口要求 (faces/axes/points 为空)。
    # 但为了装配通用性，通常垫片的中心轴和上下表面是潜在接口。
    # 由于 spec 明确 interfaces 为空，此处不强制创建命名参考几何，
    # 但保留基础基准面供后续可能的装配使用。
    
    # 5. 保存文件
    model_path = r"D:\a_src\python\sw_agent\agent_output\Standard_Asbestos_Gasket-20260424_165125\part\Standard_Asbestos_Gasket.SLDPRT"
    print(f"尝试保存零件到: {model_path}")
    
    success = sw_doc.save_as(model_path)
    
    if success:
        print("零件建模完成并保存成功。")
    else:
        print("零件保存失败，请检查路径权限或 SolidWorks 状态。")

if __name__ == "__main__":
    main()