# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "石棉垫_圆形带槽孔"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模: {part_name}")

    # 2. 定义参数 (单位转换为米)
    # 主体尺寸
    body_diameter_m = 0.050  # 50 mm
    body_radius_m = body_diameter_m / 2
    body_thickness_m = 0.002 # 2 mm
    
    # 矩形槽尺寸
    slot_length_y_m = 0.020  # 20 mm (Y向长边)
    slot_width_x_m = 0.010   # 10 mm (X向宽边)
    
    # 圆孔尺寸
    hole_diameter_m = 0.006  # 6 mm
    hole_radius_m = hole_diameter_m / 2
    hole_offset_x_m = 0.018  # 18 mm (距离圆心)

    # 3. 创建主体圆柱体
    print("步骤 1: 创建主体圆柱体")
    sketch_body = sw_doc.insert_sketch_on_plane("XY")
    # 在XY平面，中心(0,0)，半径body_radius_m
    sw_doc.create_circle(center_x=0, center_y=0, radius=body_radius_m, sketch_ref="XY")
    # 拉伸厚度 2mm
    extrude_body = sw_doc.extrude(sketch_body, depth=body_thickness_m, single_direction=True, merge=True)
    print("主体圆柱体创建完成")

    # 4. 创建矩形通槽切除
    print("步骤 2: 创建矩形通槽")
    # 为了切除贯穿，我们需要在顶面或底面建草图。这里选择在顶面(Z=thickness)对应的平面或直接使用XY平面投影切除。
    # 由于extrude_cut是基于当前草图平面的法向切除，如果我们在XY平面画草图并切除，它会沿Z轴方向切除。
    # 因为主体是从Z=0到Z=0.002，如果在XY平面(Z=0)做切除，深度设为负值或正值需小心。
    # 更稳妥的方式：在顶面(Z=0.002)创建一个参考平面，或者直接在XY平面画草图，然后向下切除(负深度)或向上切除(正深度)。
    # 这里我们直接在XY平面画草图，然后向Z轴正方向切除(穿过实体)。
    # 注意：SolidWorks中，如果草图在实体表面下方，切除方向需要指向实体内部。
    # 让我们创建一个位于顶部的参考平面来确保草图位置正确，或者直接使用XY平面并指定足够的切除深度。
    # 简单策略：在XY平面画草图，切除深度设为 -0.005 (向下切穿，假设实体在Z>0区域? 不，默认拉伸是单向，通常从草图面向上)。
    # 修正：sw_doc.extrude 默认 single_direction=True 通常是沿法线正向。对于XY平面，法线是+Z。
    # 所以实体占据 Z=[0, 0.002]。
    # 如果我们在 XY 平面 (Z=0) 画切除草图，并向 +Z 方向切除 (depth > 0)，它将切穿实体。
    
    sketch_slot = sw_doc.insert_sketch_on_plane("XY")
    # 矩形中心(0,0)，宽(X)=0.010, 高(Y)=0.020
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=slot_width_x_m, height=slot_length_y_m, sketch_ref="XY")
    # 切除，深度大于厚度即可，例如 0.005m
    cut_slot = sw_doc.extrude_cut(sketch_slot, depth=0.005, single_direction=True)
    print("矩形通槽创建完成")

    # 5. 创建两个圆通孔切除
    print("步骤 3: 创建两个圆通孔")
    sketch_holes = sw_doc.insert_sketch_on_plane("XY")
    
    # 左孔 (-18mm, 0) -> (-0.018, 0)
    sw_doc.create_circle(center_x=-hole_offset_x_m, center_y=0, radius=hole_radius_m, sketch_ref="XY")
    
    # 右孔 (18mm, 0) -> (0.018, 0)
    sw_doc.create_circle(center_x=hole_offset_x_m, center_y=0, radius=hole_radius_m, sketch_ref="XY")
    
    # 切除，深度大于厚度
    cut_holes = sw_doc.extrude_cut(sketch_holes, depth=0.005, single_direction=True)
    print("圆通孔创建完成")

    # 6. 保存文件
    model_path = r"D:\a_src\python\sw_agent\agent_output\石棉垫_圆形带槽孔-20260424_164709\part\石棉垫_圆形带槽孔.SLDPRT"
    print(f"保存模型至: {model_path}")
    success = sw_doc.save_as(model_path)
    
    if success:
        print("建模与保存成功。")
    else:
        print("保存失败。")

if __name__ == "__main__":
    main()