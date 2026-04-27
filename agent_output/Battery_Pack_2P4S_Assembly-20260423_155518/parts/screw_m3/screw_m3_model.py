# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用并创建零件文档
    app = SldWorksApp()
    part_name = "screw_m3"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    print(f"开始建模零件: {part_name}")

    # 2. 定义参数 (单位转换为米)
    diameter_mm = 3.0
    length_mm = 6.0
    
    radius_m = diameter_mm / 2.0 / 1000.0
    length_m = length_mm / 1000.0

    # 3. 建模步骤
    # 3.1 在 XY 平面绘制草图
    sketch_plane = "XY"
    sketch = sw_doc.insert_sketch_on_plane(sketch_plane)
    
    # 绘制圆形截面，圆心在原点
    sw_doc.create_circle(center_x=0, center_y=0, radius=radius_m, sketch_ref=sketch_plane)
    
    # 退出草图并拉伸
    # 注意：SolidWorks API 通常需要在拉伸前结束草图编辑状态，但封装可能自动处理或需要显式调用。
    # 根据示例代码，直接调用 extrude 即可。
    extrude_feature = sw_doc.extrude(sketch, depth=length_m, single_direction=True, merge=True)
    print("主体拉伸完成")

    # 4. 创建装配接口
    # 4.1 创建轴接口: axis_shank
    # 轴沿 Z 方向，从底部 (0,0,0) 到顶部 (0,0,length_m)
    pt_bottom = (0.0, 0.0, 0.0)
    pt_top = (0.0, 0.0, length_m)
    sw_doc.create_axis(pt1=pt_bottom, pt2=pt_top, axis_name="axis_shank")
    print("创建参考轴: axis_shank")

    # 4.2 创建面接口: face_head_bottom
    # 该面是螺丝头部与 Top Case 接触的面。
    # 根据装配逻辑，螺丝穿过 Top Case 进入 Bottom Case。
    # 通常螺丝头在上方。如果我们将螺丝建模为从 Z=0 向上拉伸到 Z=length_m，
    # 那么 Z=length_m 处的面是“顶面”（可能是螺丝头底面，如果螺丝头被视为实体的一部分或者仅仅是杆的顶端）。
    # 但是，题目描述说 "Simplified cylinder representing screw shank" (简化圆柱代表螺杆)。
    # 且接口定义为 "face_head_bottom": "Contact face with Top Case", normal -Z.
    # 这意味着这个面的法向指向 -Z。
    # 在我们的模型中，Z=length_m 处的面法向是 +Z，Z=0 处的面法向是 -Z。
    # 如果螺丝是从下往上插入，或者我们定义局部坐标系使得螺丝头在 Z=max 处？
    # 让我们仔细看装配约束：
    # inst_screw_1.axis_shank concentric with inst_bottom_case.axis_screw_post_1
    # inst_screw_1.face_head_bottom distance 0 to inst_top_case.face_top_outer
    # inst_top_case.face_top_outer normal is +Z.
    # 如果 face_head_bottom 的法向是 -Z，且它与 face_top_outer (normal +Z) 距离为 0 (重合)，
    # 这意味着 face_head_bottom 位于 Top Case 的上表面。
    # 通常螺丝头压在 Top Case 上表面。
    # 如果我们的圆柱体是从 Z=0 到 Z=length_m。
    # 哪个面是 "head bottom"? 
    # 如果这是一个简化的螺杆，没有明显的头部几何特征，我们需要指定一个端面作为接口。
    # 假设螺丝安装后，其“头部”端位于 Z 轴正方向的最大值处（即 length_m），而尖端在 Z=0。
    # 那么 Z=length_m 处的面法向是 +Z。但这与接口定义的 normal -Z 矛盾吗？
    # 接口定义中的 "normal_direction_relation": "normal -Z" 是指该面在**零件局部坐标系**下的法向，还是指在**装配后**相对于全局的法向？
    # 通常零件接口的法向是指在零件自身坐标系下的属性。
    # 如果我们在零件中创建一个 Reference Plane 或者直接使用 Face，我们需要确保命名正确。
    # 然而，`create_ref_plane` 创建的是平面，不是实体面。装配约束通常引用实体面或基准面。
    # 对于简单的圆柱，我们可以创建两个基准面来辅助定位，或者直接依赖几何面。
    # 但为了稳健性，特别是当几何简单时，创建命名的基准面（Reference Plane）作为接口代理是更好的做法，或者确保我们能通过坐标选择到正确的面。
    # 这里的 `face_head_bottom` 是一个面接口。
    # 如果我们将螺丝建模为：原点在底部中心，向上拉伸。
    # 顶部面 (Z=length_m) 的法向是 +Z。
    # 底部面 (Z=0) 的法向是 -Z。
    # 如果接口要求 `face_head_bottom` 的法向是 -Z，那它应该是底部面？
    # 但这不符合物理直觉（螺丝头通常在上方）。
    # 让我们重新审视：也许螺丝是倒着放的？或者“Head Bottom”指的是螺丝头的下表面，而在局部坐标系中，如果我们把螺丝头放在 Z=0 处，杆向 -Z 延伸？
    # 不，标准做法通常是 Z 向上。
    # 另一种解释：接口定义中的 `normal_direction_relation` 是为了帮助装配代理理解方向，而不是强制零件内部的几何法向必须完全匹配字符串，只要装配时能对齐即可。
    # 但是，为了保险起见，我们创建一个名为 `face_head_bottom` 的**基准面 (Reference Plane)** 位于螺丝的顶部（假设那是头部位置），并将其命名为接口名。
    # 等等，`create_ref_plane` 返回的是平面对象。装配约束可以使用基准面。
    # 如果装配约束要求的是 "Face"，使用基准面可能不兼容，取决于底层实现。
    # 但在许多 CAD API 中，Mate 可以接受 Planar Face 或 Datum Plane。
    # 鉴于 `face_head_bottom` 被描述为 "Contact face"，它很可能指的是实体的那个面。
    # 由于我们无法直接重命名实体面（API 未提供 rename_face），我们通常依靠选择器或创建辅助基准面。
    # 这里有一个策略：创建一个与顶部面重合的基准面，命名为 `face_head_bottom`。
    # 这样装配代理可以通过名称找到这个基准面，并用它进行 Coincident/Distance 约束。
    
    # 修正思路：
    # 1. 螺丝杆长 6mm。
    # 2. 假设螺丝头在 Z=6mm 处（顶部）。
    # 3. 顶部面的几何法向是 +Z。
    # 4. 接口定义说 `face_head_bottom` normal is -Z。这可能意味着在装配语境下，该面朝向下方（即朝向 Top Case 的表面，如果 Top Case 在下面的话？不，Top Case 在上面）。
    # 让我们看装配：Top Case 盖在 Bottom Case 上。螺丝从上往下拧？还是从下往上？
    # 通常电池包螺丝从外壳外部拧入。
    # 如果 Top Case 是盖子，螺丝头在 Top Case 的外表面（Top Outer）。
    # 所以螺丝头在最高处。
    # 螺丝杆向下延伸进入 Post。
    # 如果我们将零件原点设在螺丝头顶面中心：
    #   - 顶部面在 Z=0。法向 +Z (向外) 或 -Z (向内/向下)? 
    #   - 如果原点在顶面，杆向 -Z 拉伸。
    #   - 顶面 (Z=0) 的法向如果是 +Z，则指向外部空间。
    #   - 接口 `face_head_bottom` 是接触面。螺丝头的下表面接触 Top Case 的上表面。
    #   - 如果螺丝头是一个独立的几何体，它的下表面法向是 -Z。
    #   - 但这里是简化圆柱。圆柱的顶面就是“头”。
    #   - 如果我们将圆柱建模为从 Z=0 (顶) 到 Z=-6mm (底)。
    #   - 顶面 (Z=0) 的法向是 +Z。
    #   - 这依然与 "normal -Z" 有冲突，除非 "normal -Z" 指的是该面在装配后的全局方向，或者指的是该面所代表的“功能方向”（即面向下方）。
    #   
    # 为了最稳妥地满足 "normal -Z" 的字面意思（如果在局部坐标系中）：
    # 我们可以将螺丝建模为：原点在底部，向 +Z 拉伸。
    # 此时顶部面法向 +Z。
    # 或者：原点在顶部，向 -Z 拉伸。
    # 此时顶部面 (Z=0) 法向 +Z。
    # 
    # 让我们忽略法向字符串的严格几何匹配，转而关注**位置**。
    # `face_head_bottom` 应该位于螺丝的一端，用于与 Top Case 配合。
    # 我们将创建一个基准面 `face_head_bottom` 位于螺丝的**顶部**（Z = length_m），因为这是螺丝头所在的位置。
    # 即使几何法向是 +Z，我们在装配时可以通过 "Anti-aligned" 或调整约束类型来处理。
    # 但是，如果必须严格遵守 `normal -Z`，我们可以创建一个基准面，其法向定义为 -Z？
    # `create_ref_plane` 基于现有平面偏移。XY 平面法向是 +Z。
    # 如果我们在 Z=length_m 处创建一个平行于 XY 的平面，它的法向也是 +Z。
    # 
    # 替代方案：也许 `face_head_bottom` 指的是螺丝的**底部**？
    # 不，"Head" 暗示头部。
    # 
    # 决定：
    # 1. 建模：原点在 (0,0,0)，向 +Z 拉伸 6mm。
    # 2. 顶部面在 Z=6mm。
    # 3. 创建基准面 `face_head_bottom` 在 Z=6mm 处。
    # 4. 创建基准轴 `axis_shank` 沿 Z 轴。
    # 
    # 关于法向的备注：如果装配代理严格检查法向，可能会遇到问题。但通常 "normal -Z" 在 JSON 中更多是提示装配时的对齐方向（例如，该面应朝向 -Z 方向的对象，或其法向应与目标面的法向相反）。
    # 在此模型中，顶部面法向 +Z。如果它与 Top Case 的 Top Outer (Normal +Z) 配合，且关系是 Distance 0，通常需要法向相反才能贴合（面对面）。
    # Top Case Top Outer Normal +Z (向上)。
    # Screw Head Bottom Normal ? 
    # 如果螺丝头压在 Top Case 上，螺丝头的下表面（接触面）法向应该是 -Z（向下）。
    # 啊！如果是简化圆柱，**顶面**的外法向是 +Z。但是作为“接触面”，我们关心的是它**朝向**哪里。
    # 实际上，SolidWorks 的面有内外之分。外表面法向向外。
    # 如果我们要模拟“螺丝头下表面”，在简化圆柱中，那就是顶面。
    # 顶面的外法向是 +Z。
    # 但是，如果我们把这个面当作“Head Bottom”，在物理上它朝下。
    # 这可能就是为什么 JSON 里写 `normal -Z` —— 它描述的是该面在功能上的朝向，或者期望在局部坐标系中该面的法向矢量指向 -Z。
    # 
    # 为了满足 `normal -Z`：
    # 我们可以将螺丝建模为：原点在顶部中心，向 **-Z** 方向拉伸。
    # 这样：
    # - 顶部面在 Z=0。
    # - 底部面在 Z=-6mm。
    # - 顶部面（Head）的外法向仍然是 +Z（指向外部空间，即上方）。
    # - 这还是没有改变外法向。
    # 
    # 除非... 我们创建一个**基准面**，并明确其方向？
    # `create_ref_plane` 创建的平面通常继承参考平面的法向。
    # 
    # 让我们尝试另一种解释：
    # 也许 `face_head_bottom` 并不是指几何顶面，而是指一个位于顶部的、法向向下的参考平面？
    # 不，平面没有“向下”的法向，只有正反两面。
    # 
    # 最终策略：
    # 按照常规习惯建模（原点底部，向上拉伸）。
    # 在顶部 (Z=length_m) 创建参考平面 `face_head_bottom`。
    # 在中心创建参考轴 `axis_shank`。
    # 并在日志中说明：该参考平面对应于螺丝头部端面。装配时请注意法向对齐。

    # 创建顶部参考平面 (对应螺丝头端面)
    # 基于 XY 平面 (Z=0) 偏移 length_m
    ref_plane_head = sw_doc.create_ref_plane(plane="XY", offset_val=length_m, target_plane_name="face_head_bottom")
    print("创建参考平面: face_head_bottom (位于顶部)")

    # 5. 保存文件
    output_path = r"D:\a_src\python\sw_agent\agent_output\Battery_Pack_2P4S_Assembly-20260423_155518\parts\screw_m3\screw_m3.SLDPRT"
    success = sw_doc.save_as(output_path)
    
    if success:
        print(f"零件成功保存至: {output_path}")
    else:
        print("零件保存失败")

if __name__ == "__main__":
    main()