# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, AssemDoc
import os

def main():
    # 1. 初始化应用和路径配置
    sw_app = SldWorksApp()
    
    # 工作区根目录
    root_dir = r"D:\a_src\python\sw_agent\agent_output\Standard_Rectangular_Desk-20260423_164351"
    parts_dir = os.path.join(root_dir, "parts")
    assembly_dir = os.path.join(root_dir, "assembly")
    
    # 确保装配输出目录存在
    if not os.path.exists(assembly_dir):
        os.makedirs(assembly_dir)

    # 零件文件路径映射 (part_id -> model_file)
    part_files = {
        "desktop_panel": os.path.join(parts_dir, "desktop_panel", "desktop_panel.SLDPRT"),
        "cylindrical_leg": os.path.join(parts_dir, "cylindrical_leg", "cylindrical_leg.SLDPRT")
    }

    # 装配体名称
    assem_name = "Standard_Rectangular_Desk"
    
    print(f"[LOG] Starting assembly: {assem_name}")

    # 2. 创建并激活装配文档
    try:
        sw_assem_doc = sw_app.createAndActivate_sw_assembly(assem_name)
        sw_assem = AssemDoc(sw_assem_doc)
        print(f"[LOG] Assembly document created and activated.")
    except Exception as e:
        print(f"[ERROR] Failed to create assembly: {e}")
        return

    # 3. 插入组件实例
    # 记录 instance_id -> comp_name 的映射
    instance_map = {}

    # --- 插入基准件: Desktop Panel ---
    desktop_path = part_files["desktop_panel"]
    if os.path.exists(desktop_path):
        # 桌面作为基准，放置在原点附近。根据规划，底面在Z=-12.5mm (即-0.0125m)，中心在(0,0,0)。
        # add_component 通常将零件原点放在指定坐标。假设零件原点在几何中心。
        # 为了配合方便，我们先将其插入到 (0, 0, 0)。后续通过约束固定位置或依赖初始位置。
        # 注意：SolidWorks API中，第一个插入的组件通常是固定的(Fixed)。
        comp_desktop = sw_assem.add_component(desktop_path, 0, 0, 0)
        if comp_desktop:
            instance_map["inst_desktop_main"] = comp_desktop
            print(f"[LOG] Inserted desktop panel: {comp_desktop}")
        else:
            print("[ERROR] Failed to insert desktop panel.")
            return
    else:
        print(f"[ERROR] Desktop part file not found: {desktop_path}")
        return

    # --- 插入桌腿实例 (复用同一个文件) ---
    leg_path = part_files["cylindrical_leg"]
    if not os.path.exists(leg_path):
        print(f"[ERROR] Leg part file not found: {leg_path}")
        return

    # 定义桌腿的目标位置 (单位: 米)
    # 规划说明：桌腿位于桌面四角内侧50mm处。
    # 桌面尺寸: 1200x600. 半长=600, 半宽=300.
    # 偏移: 50mm = 0.05m.
    # X coords: -600+50 = -550mm (-0.55m), 600-50 = 550mm (0.55m)
    # Y coords: 300-50 = 250mm (0.25m), -300+50 = -250mm (-0.25m)
    # Z coord: 桌面底面在 Z=-12.5mm (-0.0125m). 桌腿高725mm. 
    # 如果桌腿原点在底部中心，则顶部在 Z=725mm. 
    # 为了让桌腿顶面(face_top)与桌面底面(face_bottom)重合，我们需要计算插入时的近似Z位置。
    # 假设桌腿模型原点在底面中心：
    #   顶面高度 = 0.725m.
    #   目标顶面高度 = -0.0125m.
    #   所以桌腿底面应该在 -0.0125 - 0.725 = -0.7375m.
    #   插入点设为 (x, y, -0.7375).
    # 假设桌腿模型原点在几何中心 (高度一半处):
    #   顶面相对于原点 +0.3625m.
    #   目标顶面高度 -0.0125m.
    #   所以原点应该在 -0.0125 - 0.3625 = -0.375m.
    #   插入点设为 (x, y, -0.375).
    # 由于不确定具体建模原点，我们采用一个通用的策略：先插入到大致位置，然后依靠 mate_faces 来精确对齐Z轴。
    # 这里假设原点在底面中心（常见做法），或者我们直接插入到 (x, y, 0) 然后靠配合拉过去？
    # 为了稳定性，我们尝试插入到接近最终位置的地方。
    # 让我们假设原点在底面中心。
    
    leg_positions = {
        "inst_leg_fl": (-0.55, 0.25, -0.7375), # Front Left: X-, Y+
        "inst_leg_fr": (0.55, 0.25, -0.7375),  # Front Right: X+, Y+
        "inst_leg_bl": (-0.55, -0.25, -0.7375), # Back Left: X-, Y-
        "inst_leg_br": (0.55, -0.25, -0.7375)  # Back Right: X+, Y-
    }

    for inst_id, pos in leg_positions.items():
        x, y, z = pos
        comp_leg = sw_assem.add_component(leg_path, x, y, z)
        if comp_leg:
            instance_map[inst_id] = comp_leg
            print(f"[LOG] Inserted leg {inst_id}: {comp_leg} at ({x}, {y}, {z})")
        else:
            print(f"[ERROR] Failed to insert leg {inst_id}.")
            return

    # 4. 执行配合 (Constraints)
    
    desktop_comp = instance_map.get("inst_desktop_main")
    
    # 辅助函数：安全执行配合
    def apply_mate(mate_func, *args, **kwargs):
        try:
            result = mate_func(*args, **kwargs)
            if result:
                print(f"[LOG] Mate applied successfully: {args[2]} & {args[3]}")
            else:
                print(f"[WARN] Mate might have failed or returned None: {args[2]} & {args[3]}")
        except Exception as e:
            print(f"[ERROR] Exception during mating {args[2]} & {args[3]}: {e}")

    # --- 约束 1: 固定桌面 (Implicitly fixed by being first component, but let's ensure logic) ---
    # 规划中提到 "fix" 关系。在SW中，第一个组件通常自动固定。如果需要显式固定，API可能不同。
    # 这里假设第一个组件已固定。

    # --- 约束 2-9: 桌腿与桌面的配合 ---
    # 每个桌腿需要两个主要配合：
    # 1. Face Coincident: leg.face_top <-> desktop.face_bottom
    # 2. Positioning: 由于API限制，没有直接的 point-to-axis distance mate。
    #    但是，我们在插入时已经设置了近似的 X, Y 坐标。
    #    如果 face_coincident 成功，Z轴就确定了。
    #    X, Y 的位置依赖于插入时的坐标。如果插入坐标准确，且没有旋转自由度干扰，通常可以接受。
    #    然而，圆柱体绕自身轴旋转是自由的，但这不影响外观和功能。
    #    关键是 X, Y 平移自由度。
    #    规划中的 "distance" 约束针对的是 axis_center 到 point_ref。
    #    由于当前 API `mate_axes` 和 `mate_faces` 不支持距离偏移或点到轴的距离，
    #    我们依赖 `add_component` 时的初始位置精度。
    #    为了确保万无一失，如果系统支持，我们可以尝试添加额外的参考平面配合，但这里仅使用给定的接口。
    
    legs_to_constrain = [
        ("inst_leg_fl", "Front Left"),
        ("inst_leg_fr", "Front Right"),
        ("inst_leg_bl", "Back Left"),
        ("inst_leg_br", "Back Right")
    ]

    for inst_id, name in legs_to_constrain:
        leg_comp = instance_map.get(inst_id)
        if not leg_comp or not desktop_comp:
            continue
            
        print(f"[LOG] Constraining {name} ({inst_id})...")
        
        # 面配合: 桌腿顶面 与 桌面底面 重合
        # aligned=False 表示反向平行（Opposed），即法线方向相反，面对面贴合。
        # 规划中 alignment: "opposed".
        apply_mate(
            sw_assem.mate_faces,
            assem_name,
            leg_comp,       # comp1
            desktop_comp,   # comp2
            "face_top",     # plane_name1 (Leg)
            "face_bottom",  # plane_name2 (Desktop)
            aligned=False   # Opposed normals
        )

        # 注意：关于 X/Y 定位
        # 规划要求轴线距离边缘50mm。
        # 我们在 add_component 时已经设置了 X, Y。
        # 如果没有额外的约束锁定 X/Y，零件可能会在面上滑动。
        # 但在简单的静态装配展示中，初始位置通常被保留，除非有冲突。
        # 如果有 `mate_axes` 可用，且桌面有对应的垂直轴或参考线，我们可以使用。
        # 但桌面接口只定义了 faces 和 points。points 不能直接用于 mate_axes。
        # 因此，我们依赖初始放置位置的准确性。
        
    # 5. 保存装配体
    output_path = os.path.join(assembly_dir, f"{assem_name}.SLDASM")
    try:
        sw_assem.save_as(output_path)
        print(f"[LOG] Assembly saved to: {output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to save assembly: {e}")

    print("[LOG] Assembly process completed.")

if __name__ == "__main__":
    main()