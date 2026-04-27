# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    print("Starting modeling for Table Leg...")
    app = SldWorksApp()
    sw_doc = PartDoc(app.createAndActivate_sw_part("TableLeg"))

    # 2. 定义参数 (单位: m)
    diameter = 0.040      # 40 mm
    radius = diameter / 2 # 0.02 m
    height = 0.725        # 725 mm
    hole_diameter = 0.006 # 6 mm
    hole_radius = hole_diameter / 2 # 0.003 m
    hole_offset_from_top = 0.050    # 50 mm from top
    
    # 计算孔的Z坐标位置
    # 假设底面在 Z=0，顶面在 Z=height
    # 孔中心距离顶面 50mm，所以 Z_hole = height - 0.050
    z_hole_center = height - hole_offset_from_top

    # 3. 创建主体圆柱
    print("Creating main cylinder body...")
    # 在 XY 平面绘制圆形草图
    sketch_base = sw_doc.insert_sketch_on_plane("XY")
    if not sketch_base:
        raise Exception("Failed to create base sketch on XY plane")
        
    sw_doc.create_circle(center_x=0, center_y=0, radius=radius, sketch_ref="XY")
    
    # 拉伸生成圆柱体
    # 向 +Z 方向拉伸
    extrude_body = sw_doc.extrude(sketch_base, depth=height, single_direction=True, merge=True)
    if not extrude_body:
        raise Exception("Failed to extrude base cylinder")
    print(f"Cylinder created with height {height}m")

    # 4. 创建安装孔 (贯穿孔)
    # 根据装配规划，需要两个侧面安装孔，沿 X 轴方向贯穿。
    # 我们在 YZ 平面绘制草图，因为孔是沿 X 轴方向的。
    # 注意：SolidWorks API 中，YZ 平面的局部坐标系可能有所不同。
    # 如果 insert_sketch_on_plane("YZ") 失败或行为异常，我们可以尝试使用 "ZY" 或者通过偏移平面来创建。
    # 这里先尝试直接使用 "YZ"。如果失败，可能需要检查封装对基准面的命名支持。
    # 知识库提到："plane_name 仅限: 'XY', 'XZ', 'ZY' 或自定义平面名"。
    # 注意：这里是 "ZY" 而不是 "YZ"。这可能是导致之前失败的原因。
    # SolidWorks 默认基准面通常是 Front (XY), Top (XZ), Right (YZ)。
    # 但在某些封装中，顺序可能不同。让我们尝试 "ZY" 作为右视基准面（通常对应 YZ 平面）。
    # 如果 "ZY" 也不对，我们可能需要创建一个参考平面。
    # 让我们先尝试 "ZY"。
    
    print("Creating mounting holes...")
    
    # 尝试使用 "ZY" 平面 (Right Plane)
    sketch_hole_1 = sw_doc.insert_sketch_on_plane("ZY")
    
    # 如果 "ZY" 返回 None，尝试 "YZ" (虽然知识库说仅限 ZY，但有时别名有效)
    if not sketch_hole_1:
        print("Trying 'YZ' plane...")
        sketch_hole_1 = sw_doc.insert_sketch_on_plane("YZ")
        
    # 如果仍然失败，创建一个平行于 YZ 的参考平面
    if not sketch_hole_1:
        print("Creating reference plane for hole sketch...")
        ref_plane_hole = sw_doc.create_ref_plane(plane="YZ", offset_val=0, target_plane_name="HoleSketchPlane")
        if ref_plane_hole:
            sketch_hole_1 = sw_doc.insert_sketch_on_plane(ref_plane_hole)
        else:
            raise Exception("Failed to create hole sketch plane")

    if not sketch_hole_1:
        raise Exception("Failed to create hole sketch on any available plane")

    # 在草图上绘制圆
    # 对于 ZY 平面 (Right Plane)，通常局部 X 对应全局 Y，局部 Y 对应全局 Z。
    # 我们需要圆心在全局 Y=0, Z=z_hole_center。
    # 所以在局部坐标系中，center_x (Global Y) = 0, center_y (Global Z) = z_hole_center.
    sw_doc.create_circle(center_x=0, center_y=z_hole_center, radius=hole_radius, sketch_ref="ZY")
    
    # 拉伸切除，贯穿整个圆柱。
    # 圆柱直径 40mm，半径 20mm。从中心到边缘距离 20mm。
    # 为了确保贯穿，深度设为大于直径的值，例如 0.05m (50mm)。
    # 由于是在 ZY 平面画的圆，拉伸方向默认垂直于草图平面，即沿 X 轴。
    # 使用双向拉伸以确保完全贯穿。
    
    cut_hole_1 = sw_doc.extrude_cut(sketch_hole_1, depth=0.05, single_direction=False)
    if not cut_hole_1:
        raise Exception("Failed to cut hole 1")
    print("Hole 1 created (along X axis)")

    # 5. 创建接口 (参考面和参考轴)
    
    # 5.1 面接口
    # top_face: Z = height
    # bottom_face: Z = 0
    # side_face_mount_1: +X 方向的面。
    # side_face_mount_2: -X 方向的面。
    
    print("Creating reference interfaces...")
    
    # Top Face Reference Plane
    # 基于 XY 平面偏移 height
    ref_plane_top = sw_doc.create_ref_plane(plane="XY", offset_val=height, target_plane_name="top_face")
    
    # Bottom Face Reference Plane
    # 基于 XY 平面偏移 0
    ref_plane_bottom = sw_doc.create_ref_plane(plane="XY", offset_val=0, target_plane_name="bottom_face")
    
    # Side Face Mount 1 (+X direction)
    # 创建一个平行于 YZ 平面，偏移量为 +radius 的平面。
    # 注意：create_ref_plane 的 plane 参数可以是 "XY", "XZ", "ZY"。
    # 我们要创建平行于 YZ (即 ZY) 的平面。
    ref_plane_side_1 = sw_doc.create_ref_plane(plane="ZY", offset_val=radius, target_plane_name="side_face_mount_1")
    
    # Side Face Mount 2 (-X direction)
    # 在 X = -radius 处创建一个 ZY 平行平面。
    ref_plane_side_2 = sw_doc.create_ref_plane(plane="ZY", offset_val=-radius, target_plane_name="side_face_mount_2")

    # 5.2 轴接口
    # central_axis: 沿 Z 轴，通过原点
    # pt1 (0,0,0), pt2 (0,0,height)
    axis_central = sw_doc.create_axis(pt1=(0, 0, 0), pt2=(0, 0, height), axis_name="central_axis")
    
    # mount_hole_axis_1: 沿 X 轴，位于 Z=z_hole_center, Y=0
    # 方向：along local X.
    # pt1 (-0.05, 0, z_hole_center), pt2 (0.05, 0, z_hole_center)
    axis_hole_1 = sw_doc.create_axis(
        pt1=(-0.05, 0, z_hole_center), 
        pt2=(0.05, 0, z_hole_center), 
        axis_name="mount_hole_axis_1"
    )
    
    # mount_hole_axis_2: 沿 local -X.
    # 几何上是同一条线，但方向相反。
    # 为了区分，我们反转点顺序。
    axis_hole_2 = sw_doc.create_axis(
        pt1=(0.05, 0, z_hole_center), 
        pt2=(-0.05, 0, z_hole_center), 
        axis_name="mount_hole_axis_2"
    )

    # 6. 保存文件
    model_path = r"D:\a_src\python\sw_agent\agent_output\Standard_Office_Table_Assembly-20260423_143100\parts\leg_cylindrical\leg_cylindrical.SLDPRT"
    print(f"Saving part to: {model_path}")
    success = sw_doc.save_as(model_path)
    
    if success:
        print("Modeling and saving completed successfully.")
    else:
        print("Failed to save the model.")

if __name__ == "__main__":
    main()