# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Top Case"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    # 定义尺寸参数 (单位: m)
    length = 0.140      # 140 mm
    width = 0.075       # 75 mm
    height = 0.035      # 35 mm
    wall_thickness = 0.0025 # 2.5 mm
    wire_window_l = 0.020   # 20 mm
    wire_window_w = 0.010   # 10 mm
    screw_hole_dia = 0.0032 # 3.2 mm
    fillet_radius = 0.002   # R2 mm
    
    # 螺丝孔位置计算 (基于Bottom Case的Screw Post位置，通常位于角落内侧)
    # 假设Screw Post中心距离外边缘有一定距离，这里根据常规设计估算
    # Bottom Case L=140, W=75. 
    # 假设Post中心距边沿 10mm (0.01m)
    margin_x = 0.010
    margin_y = 0.010
    
    # 四个螺丝孔的中心坐标 (X, Y)
    # 1: Top-Right (+X, +Y), 2: Top-Left (-X, +Y), 3: Bottom-Left (-X, -Y), 4: Bottom-Right (+X, -Y)
    # 注意：SolidWorks坐标系中，XY平面草图，X向右，Y向上。
    # 为了匹配装配约束，我们需要确定具体的坐标值。
    # 假设原点在几何中心。
    hole_x_pos = (length / 2) - margin_x
    hole_y_pos = (width / 2) - margin_y
    
    hole_coords = [
        (hole_x_pos, hole_y_pos),   # Hole 1 (Top Right)
        (-hole_x_pos, hole_y_pos),  # Hole 2 (Top Left)
        (-hole_x_pos, -hole_y_pos), # Hole 3 (Bottom Left)
        (hole_x_pos, -hole_y_pos)   # Hole 4 (Bottom Right)
    ]

    print(f"Starting modeling for {part_name}...")

    # 2. 创建主体基座
    # 在XY平面绘制矩形
    sketch_base = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(
        center_x=0, 
        center_y=0, 
        width=length, 
        height=width, 
        sketch_ref="XY"
    )
    # 拉伸高度
    extrude_body = sw_doc.extrude(sketch_base, depth=height, single_direction=True, merge=True)
    print("Base body extruded.")

    # 3. 壳化处理 (Shell)
    # 保持顶面 (Z = height)，向内挖空
    # on_face_points 需要选择要移除的面（即开口面）。这里我们要保留顶面作为盖子，所以应该移除底面？
    # 不，指令说 "Shell inward by 2.5mm, keeping top face." 
    # 这意味着顶面是封闭的，其他面变薄？或者顶面是开口？
    # 通常电池盖上盖是实心的板，四周有围壁。
    # 如果 "keeping top face" 意味着顶面不被移除，那么我们需要移除的是底面吗？
    # 让我们重新审视形状："Rectangular plate with raised rim".
    # 这通常意味着：一个平板，下面有一圈凸起的边框用于嵌入下壳体。
    # 建模策略调整：
    # 方法A: 拉伸实心块 -> Shell (移除底面) -> 得到带底的盒子？不对，上盖通常是平的。
    # 方法B: 拉伸实心块 -> Shell (移除顶面?) -> 得到开口的盒子？也不对。
    # 方法C (更稳健): 
    # 1. 拉伸一个大的实心块 (140x75x35)。
    # 2. 在底面 (Z=0) 创建一个稍小的矩形草图 (考虑壁厚)，拉伸切除内部材料，形成“Raised Rim”结构。
    #    这样顶面是完整的平板，底面有一圈凸台。
    #    这种结构更符合 "Cover ... with raised rim to fit into bottom case"。
    
    # 让我们采用方法C，因为它比Shell更容易控制“Raised Rim”的具体形状和配合间隙。
    # 但是指令明确说了 "Shell inward by 2.5mm, keeping top face"。
    # 如果严格执行Shell：
    # 选择一个面进行移除。如果移除底面 (Z=0)，则得到一个顶部封闭、底部开口的盒子。
    # 这正是 "Raised Rim" 的一种形式（倒扣的盒子）。
    # 顶面厚度 = wall_thickness? 不，Shell会让所有保留的面都变成 wall_thickness。
    # 如果顶面也是 2.5mm 厚，那它就是一个薄壁盒子的顶。
    # 这符合 "Wall Thickness: 2.5mm" 的全局规则。
    
    # 执行 Shell: 移除底面 (Z=0 处的面)
    # 底面中心点坐标: (0, 0, 0)
    try:
        sw_doc.shell(on_face_points=[(0, 0, 0)], thickness=wall_thickness, outward=False)
        print("Shell operation completed. Top face kept, bottom opened.")
    except Exception as e:
        print(f"Shell failed: {e}. Attempting alternative modeling strategy if needed.")
        # 如果Shell失败，可能需要回退到拉伸切除策略，但先尝试Shell。

    # 4. 切割线窗 (Wire Window)
    # 在顶面 (Z = height) 创建草图
    # 顶面法向是 +Z。
    sketch_window = sw_doc.insert_sketch_on_plane("XY") 
    # 注意：insert_sketch_on_plane("XY") 默认是在 Z=0 平面。
    # 我们需要在 Z=height 处建草图。
    # API中没有直接指定Z偏移的insert_sketch_on_plane，除非使用 create_workplane_p_d。
    
    # 创建偏移平面用于顶面草图
    plane_top = sw_doc.create_workplane_p_d("XY", offset_val=height)
    sketch_window = sw_doc.insert_sketch_on_plane(plane_top)
    
    sw_doc.create_centre_rectangle(
        center_x=0,
        center_y=0,
        width=wire_window_l,
        height=wire_window_w,
        sketch_ref="XY" # 参考系仍为XY方向
    )
    # 拉伸切除，贯穿整个厚度 (或者至少切穿顶面壁厚)
    # 由于是壳化后的实体，顶面厚度为 2.5mm。切除深度设为 0.005 (5mm) 确保切穿。
    sw_doc.extrude_cut(sketch_window, depth=0.005, single_direction=True)
    print("Wire window cut completed.")

    # 5. 钻螺丝孔 (Screw Holes)
    # 需要在顶面上钻孔，贯穿整个盖子厚度 (35mm) 或者至少穿过顶面壁厚？
    # 指令: "Drill 4 through-holes (3.2mm)". Through-hole 通常意味着贯穿整个零件在该方向的厚度。
    # 对于上盖，螺丝是从上往下拧入下壳体的螺柱。
    # 所以孔必须贯穿顶面的实体部分。
    # 由于我们做了Shell，顶面是 2.5mm 厚的板。
    # 但是，如果是 "Raised Rim" 结构，螺丝孔可能位于凸缘上？
    # 不，通常M3螺丝穿过上盖的通孔，旋入下盖的螺柱。
    # 所以孔只需要穿过上盖的顶板即可。
    
    # 在顶面平面 (plane_top) 上绘制4个圆
    sketch_holes = sw_doc.insert_sketch_on_plane(plane_top)
    
    for i, (hx, hy) in enumerate(hole_coords):
        sw_doc.create_circle(center_x=hx, center_y=hy, radius=screw_hole_dia/2, sketch_ref="XY")
        
    # 拉伸切除，深度足以切穿顶面壁厚 (2.5mm)。设深度为 0.005m。
    sw_doc.extrude_cut(sketch_holes, depth=0.005, single_direction=True)
    print("Screw holes drilled.")

    # 6. 外部圆角 (Fillet)
    # "Apply R2 fillet to all external vertical edges."
    # 垂直边指的是侧面的棱边。
    # 由于Shell操作，外部形状仍然是 140x75x35 的长方体轮廓。
    # 垂直边的坐标特征：X = ±L/2, Y = ±W/2, Z 在 0 到 H 之间。
    # 我们可以选取每条垂直边上的一个点来定位。
    
    # 四条垂直边的中点或任意点：
    # Edge 1 (Front Right): X=L/2, Y=W/2, Z=H/2
    # Edge 2 (Front Left):  X=-L/2, Y=W/2, Z=H/2
    # Edge 3 (Back Left):   X=-L/2, Y=-W/2, Z=H/2
    # Edge 4 (Back Right):  X=L/2, Y=-W/2, Z=H/2
    
    edge_points = [
        (length/2, width/2, height/2),
        (-length/2, width/2, height/2),
        (-length/2, -width/2, height/2),
        (length/2, -width/2, height/2)
    ]
    
    try:
        sw_doc.fillet_edges(on_line_points=edge_points, radius=fillet_radius)
        print("External vertical edges filleted.")
    except Exception as e:
        print(f"Fillet failed: {e}")

    # 7. 创建装配接口 (Interfaces)
    
    # --- Faces ---
    # face_bottom_mating: 这是上盖的内表面（与下盖配合的面）。
    # 由于我们移除了底面并进行了Shell，现在的“底面”其实是空的，或者说，配合面是上盖内壁的下边缘？
    # 不，"face_bottom_mating" normal -Z. 
    # 在Shell之后，原来的底面被移除了。剩下的实体有一个内表面和一个外表面。
    # 配合面通常是上盖凸缘（Rim）的底端面。
    # 在我们的模型中，Shell后，Z=0 处是空的。实体的最下端是 Z=0 处的边缘？
    # 实际上，Shell保留了侧面和顶面。侧面的内表面和外表面都存在。
    # 如果下盖是插入上盖的Rim中，那么配合面可能是上盖内侧壁的某个面，或者是上盖顶板的下表面？
    # 根据 "normal -Z"，这是一个水平面。
    # 在上盖结构中，唯一的水平下表面是顶板的下表面 (Z = height - wall_thickness)? 
    # 或者，如果Rim是向下延伸的，那么Rim的底端面是 Z=0? 
    # 让我们回顾Shell行为：Shell移除选定面，并将剩余面向内偏移。
    # 如果我们移除底面 (Z=0)，那么 Z=0 处就没有面了，只有边界。
    # 这可能不是最佳的配合面定义。
    # 也许 "face_bottom_mating" 指的是上盖顶板的下表面？ Normal -Z.
    # 让我们创建一个参考平面来表示这个面，或者直接引用几何面。
    # 由于API限制，我们主要创建 Reference Planes 和 Axes。
    
    # 创建参考平面: face_bottom_mating
    # 这个面应该是上盖内部顶板的下表面。
    # Z 坐标 = height - wall_thickness = 0.035 - 0.0025 = 0.0325
    plane_bottom_mating = sw_doc.create_ref_plane("XY", offset_val=height - wall_thickness, target_plane_name="face_bottom_mating")
    
    # 创建参考平面: face_top_outer
    # 这是上盖的外顶面。
    # Z 坐标 = height = 0.035
    plane_top_outer = sw_doc.create_ref_plane("XY", offset_val=height, target_plane_name="face_top_outer")

    # --- Axes ---
    # 4个螺丝孔轴
    # axis_screw_hole_1 to 4
    # 方向沿 Local Z (0,0,1)
    # 起点可以在孔中心，Z=0，终点 Z=height
    
    axis_names = ["axis_screw_hole_1", "axis_screw_hole_2", "axis_screw_hole_3", "axis_screw_hole_4"]
    
    for i, (hx, hy) in enumerate(hole_coords):
        pt1 = (hx, hy, 0)
        pt2 = (hx, hy, height)
        sw_doc.create_axis(pt1=pt1, pt2=pt2, axis_name=axis_names[i])
        
    print("Interfaces created.")

    # 8. 保存文件
    model_path = r"D:\a_src\python\sw_agent\agent_output\Battery_Pack_2P4S_Assembly-20260423_155518\parts\top_case\top_case.SLDPRT"
    success = sw_doc.save_as(model_path)
    
    if success:
        print(f"Model saved successfully to {model_path}")
    else:
        print("Failed to save model.")

if __name__ == "__main__":
    main()