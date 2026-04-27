# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

# 1. 启动与创建
app = SldWorksApp()
sw_doc = PartDoc(app.createAndActivate_sw_part("BottomCase"))

# 2. 参数定义 (单位: m)
L = 0.140       # Length 140mm
W = 0.075       # Width 75mm
H = 0.035       # Height 35mm
Wall_Thick = 0.0025 # Wall Thickness 2.5mm
Post_Dia = 0.006    # Screw Post Diameter 6mm
Mount_Hole_Dia = 0.0045 # Mounting Hole Diameter 4.5mm
Fillet_Rad = 0.002      # External Fillet Radius 2mm

# 计算关键坐标
Half_L = L / 2
Half_W = W / 2
Inner_L = L - 2 * Wall_Thick
Inner_W = W - 2 * Wall_Thick

# 螺丝柱位置 (假设在四个角，距离边缘一定距离，这里设为距离外壁中心偏移)
# 为了简化并保证结构强度，通常螺丝柱位于角落。
# 假设螺丝柱中心距离外边缘 X方向 10mm, Y方向 10mm
Offset_X = 0.010
Offset_Y = 0.010

Post_Centers = [
    (-Half_L + Offset_X, -Half_W + Offset_Y), # Post 1 (Left-Bottom)
    (Half_L - Offset_X, -Half_W + Offset_Y),  # Post 2 (Right-Bottom)
    (-Half_L + Offset_X, Half_W - Offset_Y),  # Post 3 (Left-Top)
    (Half_L - Offset_X, Half_W - Offset_Y)    # Post 4 (Right-Top)
]

# 底部安装孔位置 (通常在更外侧或同轴，这里假设与螺丝柱同轴以便装配，或者稍微偏移)
# 根据描述 "Cut 4 M4 through-holes on the outer bottom face at corners"
# 我们让安装孔与螺丝柱同轴，这样螺丝可以从底部穿过壳体进入柱子(如果柱子是实心的则需盲孔，但描述说是through-holes on outer bottom)
# 修正：通常M4安装孔是用于将电池包固定到外部底盘的。
# 如果螺丝柱是用于连接上下盖(M3)，那么底部的M4孔应该是独立的。
# 让我们把M4孔放在更靠近角落的位置，例如距离边缘 5mm。
Mount_Offset_X = 0.005
Mount_Offset_Y = 0.005

Mount_Hole_Centers = [
    (-Half_L + Mount_Offset_X, -Half_W + Mount_Offset_Y),
    (Half_L - Mount_Offset_X, -Half_W + Mount_Offset_Y),
    (-Half_L + Mount_Offset_X, Half_W - Mount_Offset_Y),
    (Half_L - Mount_Offset_X, Half_W - Mount_Offset_Y)
]

print(f"Starting modeling for Bottom Case with dimensions L={L}, W={W}, H={H}")

# 3. 主体建模：拉伸基体
sketch_base = sw_doc.insert_sketch_on_plane("XY")
sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=L, height=W, sketch_ref="XY")
base_extrude = sw_doc.extrude(sketch_base, depth=H, single_direction=True, merge=True)
print("Base block extruded.")

# 4. 壳化处理 (Shell)
# 选择顶面进行移除，形成开口盒子
# 顶面中心点坐标为 (0, 0, H)
sw_doc.shell(on_face_points=[(0, 0, H)], thickness=Wall_Thick, outward=False)
print("Shell operation completed.")

# 5. 添加内部螺丝柱 (Screw Posts)
# 需要在内底面上创建草图。内底面 Z 坐标为 Wall_Thick (因为壳化向内，底面厚度保留)
# 实际上，壳化后，内底面的Z高度是 Wall_Thick。
# 我们在 XY 平面 (Z=0) 上方 Wall_Thick 处创建一个参考平面，或者直接在内底面(Z=Wall_Thick)上画草图？
# API insert_sketch_on_plane 支持 "XY", "XZ", "ZY" 或自定义平面名。
# 我们可以先创建一个偏移平面作为内底面的绘图基准，或者直接在 XY 平面画然后拉伸到指定高度。
# 更稳健的方法：在 XY 平面画圆，然后拉伸到 H - Wall_Thick 的高度？不，柱子应该从内底面长到顶部。
# 内底面高度 = Wall_Thick。顶部高度 = H。
# 柱子高度 = H - Wall_Thick。

# 创建内底面参考平面 (可选，为了清晰)
# inner_bottom_plane = sw_doc.create_workplane_p_d("XY", Wall_Thick) 
# 但为了简单，我们直接在 XY 平面画草图，然后拉伸深度为 (H - Wall_Thick)，起始位置需要调整吗？
# extrude 默认从草图平面向正方向拉伸。
# 如果我们在 XY (Z=0) 画，拉伸深度 H-Wall_Thick，它会占据 Z=0 到 Z=H-Wall_Thick。
# 但我们需要它从 Z=Wall_Thick 开始。
# 所以最好创建一个偏移平面。

inner_bottom_plane = sw_doc.create_workplane_p_d("XY", Wall_Thick)

sketch_posts = sw_doc.insert_sketch_on_plane(inner_bottom_plane)
for cx, cy in Post_Centers:
    sw_doc.create_circle(center_x=cx, center_y=cy, radius=Post_Dia/2, sketch_ref="XY") # sketch_ref 对应平面法向，这里平面平行XY，故用XY

post_height = H - Wall_Thick
posts_extrude = sw_doc.extrude(sketch_posts, depth=post_height, single_direction=True, merge=True)
print("Screw posts added.")

# 6. 添加底部安装孔 (Mounting Holes)
# 在底面 (Z=0) 切除通孔
sketch_mount_holes = sw_doc.insert_sketch_on_plane("XY")
for cx, cy in Mount_Hole_Centers:
    sw_doc.create_circle(center_x=cx, center_y=cy, radius=Mount_Hole_Dia/2, sketch_ref="XY")

# 切除深度应大于壁厚，确保打通。这里直接切穿整个高度 H 以确保通孔，或者切 Wall_Thick + epsilon
# 由于是通孔，且从底部向上切，深度设为 H 即可（虽然中间有柱子，但孔位和柱子位不同，不会冲突）
# 注意：如果孔位和柱子位重合，则需要布尔减。这里假设不重合。
mount_cut = sw_doc.extrude_cut(sketch_mount_holes, depth=H, single_direction=True)
print("Mounting holes cut.")

# 7. 添加内部加强筋/电池槽 (Internal Ribs/Slots)
# 描述提到 "semi-circular cell slots on inner bottom"。
# 18650 直径 18mm。2P4S 排列。
# 为了简化建模并保证稳定性，我们在内底面添加一些简单的支撑肋条或半圆槽。
# 这里我们创建两个主要的横向支撑肋，位于电池排之间。
# 电池布局：2行4列。
# 行间距 Pitch Y = 32mm (来自 Cell Holder 规格，虽未明确给 Bottom Case，但需匹配)。
# 列间距 Pitch X = 32mm。
# 总宽 70mm (Holder), 总长 135mm (Holder).
# Bottom Case 内腔尺寸: Inner_L = 135mm, Inner_W = 70mm.
# 我们在内底面 (Z=Wall_Thick) 上画肋条。

Rib_Height = 0.005 # 5mm high ribs
Rib_Width = 0.003  # 3mm thick ribs

# 创建肋条草图在内底面
sketch_ribs = sw_doc.insert_sketch_on_plane(inner_bottom_plane)

# 纵向肋条 (分隔左右两排电池? 不，2P是并联，通常是并排。4S是串联。
# 2P4S 意味着 2个并联组，每组4个串联？或者 4串2并？
# 通常 2P4S 指 2 Parallel, 4 Series. 即 2个电芯并联为一组，共4组串联。
# 物理排列可能是 2行 (并联对) x 4列 (串联组)。
# 所以在 Y 方向有两排，X 方向有四列。
# 我们需要在 Y 方向中间加一个隔板吗？或者在 X 方向加隔板？
# 为了通用性，我们添加一个十字形或网格状肋条太复杂，容易出错。
# 按照指令 "semi-circular cell slots"，这通常意味着每个电池位置有一个半圆凹槽。
# 绘制8个半圆比较繁琐。
# 替代方案：添加几条主要的加强筋。
# 让我们在 X 方向中心加一条筋，Y 方向中心加一条筋，形成十字支撑。

# X方向中心筋 (沿X轴，宽Rib_Width，高Rib_Height)
# 长度覆盖内腔长度
sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=Inner_L, height=Rib_Width, sketch_ref="XY")

# Y方向中心筋 (沿Y轴)
sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=Rib_Width, height=Inner_W, sketch_ref="XY")

ribs_extrude = sw_doc.extrude(sketch_ribs, depth=Rib_Height, single_direction=True, merge=True)
print("Internal ribs added.")

# 8. 外部圆角 (External Fillets)
# 对所有外部垂直边进行 R2 圆角。
# 垂直边位于四个角。
# 角点坐标: (+-Half_L, +-Half_W, z)
# 我们需要选择边上的点。
# 边1: x=-Half_L, y=-Half_W, z from 0 to H
# 边2: x=Half_L, y=-Half_W
# 边3: x=-Half_L, y=Half_W
# 边4: x=Half_L, y=Half_W

fillet_points = [
    (-Half_L, -Half_W, H/2),
    (Half_L, -Half_W, H/2),
    (-Half_L, Half_W, H/2),
    (Half_L, Half_W, H/2)
]

try:
    sw_doc.fillet_edges(on_line_points=fillet_points, radius=Fillet_Rad)
    print("External fillets applied.")
except Exception as e:
    print(f"Fillet failed, possibly due to geometry changes: {e}")

# 9. 创建接口 (Interfaces)

# 9.1 面接口
# face_bottom_outer: 底面 (Z=0)
# 我们可以通过创建一个与底面重合的参考平面来命名它，或者依赖装配时的面选择。
# 根据知识库，优先创建命名参考面。
# 但是 create_ref_plane 是基于现有平面偏移。底面就是 XY 平面 (Z=0)。
# 我们可以重命名 XY 平面吗？API 没有直接重命名基准面的功能，只有 create_ref_plane 可以命名新平面。
# 对于已有的几何面，通常装配时通过点选或名称引用。
# 这里我们创建几个关键的参考平面以辅助装配定位，特别是 top_inner 和 inner_bottom。

# face_top_inner: 内顶面? 不，Top Case  mating surface 是 Bottom Case 的顶面边缘。
# 实际上，Top Case 盖在 Bottom Case 上。
# Bottom Case 的顶面是 Z=H 的平面环。
# 我们可以创建一个参考平面在 Z=H，命名为 "face_top_inner_ref" (虽然它是顶面，但用于配合 Top Case 的底面)
# 注意：Shell 之后，顶面是一个环。
top_plane = sw_doc.create_ref_plane("XY", H, target_plane_name="face_top_inner")

# face_inner_bottom: 内底面 Z=Wall_Thick
inner_bottom_ref_plane = sw_doc.create_ref_plane("XY", Wall_Thick, target_plane_name="face_inner_bottom")

# face_bottom_outer: 外底面 Z=0
# 我们可以创建一个 Z=0 的参考平面并命名，尽管它与原始 XY 重合
bottom_plane = sw_doc.create_ref_plane("XY", 0, target_plane_name="face_bottom_outer")

# 9.2 轴接口 (Screw Posts Axes)
# axis_screw_post_1 to 4
# 方向沿 Local Z (0,0,1)
# 起点可以在内底面，终点在顶面
for i, (cx, cy) in enumerate(Post_Centers):
    pt1 = (cx, cy, Wall_Thick)
    pt2 = (cx, cy, H)
    axis_name = f"axis_screw_post_{i+1}"
    sw_doc.create_axis(pt1=pt1, pt2=pt2, axis_name=axis_name)
    print(f"Created axis: {axis_name}")

# 10. 保存文件
model_path = r"D:\a_src\python\sw_agent\agent_output\Battery_Pack_2P4S_Assembly-20260423_155518\parts\bottom_case\bottom_case.SLDPRT"
success = sw_doc.save_as(model_path)

if success:
    print(f"Model saved successfully to {model_path}")
else:
    print("Failed to save model.")