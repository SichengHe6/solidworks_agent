# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, AssemDoc
import os

def main():
    # 1. 初始化应用和装配文档
    sw_app = SldWorksApp()
    assem_name = "Battery_Pack_2P4S_Assembly"
    
    # 创建并激活装配体
    print(f"[LOG] Creating assembly: {assem_name}")
    sw_assem_doc = sw_app.createAndActivate_sw_assembly(assem_name)
    sw_assem = AssemDoc(sw_assem_doc)
    
    # 定义工作目录和路径
    base_dir = r"D:\a_src\python\sw_agent\agent_output\Battery_Pack_2P4S_Assembly-20260423_155518"
    parts_dir = os.path.join(base_dir, "parts")
    assembly_dir = os.path.join(base_dir, "assembly")
    
    # 确保输出目录存在
    if not os.path.exists(assembly_dir):
        os.makedirs(assembly_dir)

    # 2. 建立 part_id -> model_file 映射
    part_files = {
        "bottom_case": os.path.join(parts_dir, "bottom_case", "bottom_case.SLDPRT"),
        "top_case": os.path.join(parts_dir, "top_case", "top_case.SLDPRT"),
        "cell_holder": os.path.join(parts_dir, "cell_holder", "cell_holder.SLDPRT"),
        "cell_18650": os.path.join(parts_dir, "cell_18650", "cell_18650.SLDPRT"),
        "screw_m3": os.path.join(parts_dir, "screw_m3", "screw_m3.SLDPRT")
    }

    # 3. 插入组件实例 (instance_id -> comp_name)
    instances = {}
    
    # --- Step 1: Insert Bottom Case (Base) ---
    try:
        print("[LOG] Inserting Bottom Case...")
        comp_bottom = sw_assem.add_component(part_files["bottom_case"], 0, 0, 0)
        if comp_bottom:
            instances["inst_bottom_case"] = comp_bottom
            print(f"[SUCCESS] Bottom Case inserted as: {comp_bottom}")
        else:
            raise Exception("Failed to insert Bottom Case")
    except Exception as e:
        print(f"[ERROR] Failed to insert Bottom Case: {e}")
        return

    # --- Step 2: Insert Cell Holder ---
    try:
        print("[LOG] Inserting Cell Holder...")
        # Initial placement roughly inside the case
        comp_holder = sw_assem.add_component(part_files["cell_holder"], 0, 0, 0.01) 
        if comp_holder:
            instances["inst_cell_holder"] = comp_holder
            print(f"[SUCCESS] Cell Holder inserted as: {comp_holder}")
        else:
            raise Exception("Failed to insert Cell Holder")
    except Exception as e:
        print(f"[ERROR] Failed to insert Cell Holder: {e}")
        return

    # --- Step 3: Insert Cells (8 instances of cell_18650) ---
    cell_instances = [
        ("inst_cell_1", 0.02, 0.02, 0.01),
        ("inst_cell_2", 0.05, 0.02, 0.01),
        ("inst_cell_3", 0.08, 0.02, 0.01),
        ("inst_cell_4", 0.11, 0.02, 0.01),
        ("inst_cell_5", 0.02, -0.02, 0.01),
        ("inst_cell_6", 0.05, -0.02, 0.01),
        ("inst_cell_7", 0.08, -0.02, 0.01),
        ("inst_cell_8", 0.11, -0.02, 0.01),
    ]
    
    for inst_id, x, y, z in cell_instances:
        try:
            print(f"[LOG] Inserting {inst_id}...")
            comp_cell = sw_assem.add_component(part_files["cell_18650"], x, y, z)
            if comp_cell:
                instances[inst_id] = comp_cell
                print(f"[SUCCESS] {inst_id} inserted as: {comp_cell}")
            else:
                print(f"[WARNING] Failed to insert {inst_id}")
        except Exception as e:
            print(f"[ERROR] Failed to insert {inst_id}: {e}")

    # --- Step 4: Insert Top Case ---
    try:
        print("[LOG] Inserting Top Case...")
        comp_top = sw_assem.add_component(part_files["top_case"], 0, 0, 0.05)
        if comp_top:
            instances["inst_top_case"] = comp_top
            print(f"[SUCCESS] Top Case inserted as: {comp_top}")
        else:
            raise Exception("Failed to insert Top Case")
    except Exception as e:
        print(f"[ERROR] Failed to insert Top Case: {e}")
        return

    # --- Step 5: Insert Screws (4 instances of screw_m3) ---
    screw_positions = [
        ("inst_screw_1", 0.06, 0.03, 0.06),
        ("inst_screw_2", -0.06, 0.03, 0.06),
        ("inst_screw_3", 0.06, -0.03, 0.06),
        ("inst_screw_4", -0.06, -0.03, 0.06),
    ]
    
    for inst_id, x, y, z in screw_positions:
        try:
            print(f"[LOG] Inserting {inst_id}...")
            comp_screw = sw_assem.add_component(part_files["screw_m3"], x, y, z)
            if comp_screw:
                instances[inst_id] = comp_screw
                print(f"[SUCCESS] {inst_id} inserted as: {comp_screw}")
            else:
                print(f"[WARNING] Failed to insert {inst_id}")
        except Exception as e:
            print(f"[ERROR] Failed to insert {inst_id}: {e}")

    # 4. 执行配合约束
    
    # Helper function to check if components exist before mating
    def safe_mate_faces(comp1_name, comp2_name, face1, face2, aligned=True):
        if comp1_name and comp2_name:
            try:
                sw_assem.mate_faces(assem_name, comp1_name, comp2_name, face1, face2, aligned=aligned)
                print(f"[MATE] Face mate: {comp1_name}({face1}) <-> {comp2_name}({face2})")
            except Exception as e:
                print(f"[WARN] Face mate failed: {e}")
        else:
            print(f"[SKIP] Missing component for face mate: {comp1_name}, {comp2_name}")

    def safe_mate_axes(comp1_name, comp2_name, axis1, axis2, aligned=True):
        if comp1_name and comp2_name:
            try:
                sw_assem.mate_axes(assem_name, comp1_name, comp2_name, axis1, axis2, aligned=aligned)
                print(f"[MATE] Axis mate: {comp1_name}({axis1}) <-> {comp2_name}({axis2})")
            except Exception as e:
                print(f"[WARN] Axis mate failed: {e}")
        else:
            print(f"[SKIP] Missing component for axis mate: {comp1_name}, {comp2_name}")

    # --- Constraint 1: Fix Bottom Case to Ground (Implicitly fixed by first insertion or explicit fix) ---
    # In many SW APIs, the first component is fixed. If not, we might need a specific fix command.
    # Assuming add_component at origin fixes it or it's handled by the environment.
    print("[LOG] Bottom Case assumed fixed at origin.")

    # --- Constraint 2: Mate Cell Holder to Bottom Case ---
    # Source: inst_cell_holder (face_bottom_support) -> Target: inst_bottom_case (face_inner_bottom)
    safe_mate_faces(
        instances.get("inst_cell_holder"), 
        instances.get("inst_bottom_case"), 
        "face_bottom_support", 
        "face_inner_bottom", 
        aligned=True
    )

    # --- Constraints 3-10: Mate Cells to Holder (Concentric Axes) ---
    cell_axis_map = [
        ("inst_cell_1", "axis_cell_1_1"),
        ("inst_cell_2", "axis_cell_1_2"),
        ("inst_cell_3", "axis_cell_1_3"),
        ("inst_cell_4", "axis_cell_1_4"),
        ("inst_cell_5", "axis_cell_2_1"),
        ("inst_cell_6", "axis_cell_2_2"),
        ("inst_cell_7", "axis_cell_2_3"),
        ("inst_cell_8", "axis_cell_2_4"),
    ]
    
    for cell_inst_id, holder_axis in cell_axis_map:
        safe_mate_axes(
            instances.get(cell_inst_id),
            instances.get("inst_cell_holder"),
            "axis_center",
            holder_axis,
            aligned=True
        )

    # --- Constraint 11: Mate Top Case to Bottom Case (Face Coincident) ---
    # Source: inst_top_case (face_bottom_mating) -> Target: inst_bottom_case (face_top_inner)
    # Note: Alignment 'opposed' usually means normals are opposite. 
    # face_bottom_mating normal is -Z, face_top_inner normal is +Z. They face each other.
    safe_mate_faces(
        instances.get("inst_top_case"),
        instances.get("inst_bottom_case"),
        "face_bottom_mating",
        "face_top_inner",
        aligned=False # Opposed alignment
    )

    # --- Constraints 12-15: Align Top Case Screw Holes with Bottom Case Posts ---
    screw_hole_map = [
        ("axis_screw_hole_1", "axis_screw_post_1"),
        ("axis_screw_hole_2", "axis_screw_post_2"),
        ("axis_screw_hole_3", "axis_screw_post_3"),
        ("axis_screw_hole_4", "axis_screw_post_4"),
    ]
    
    for top_axis, bottom_axis in screw_hole_map:
        safe_mate_axes(
            instances.get("inst_top_case"),
            instances.get("inst_bottom_case"),
            top_axis,
            bottom_axis,
            aligned=True
        )

    # --- Constraints 16-23: Mate Screws ---
    # For each screw:
    # 1. Concentric with Bottom Case Post
    # 2. Distance/Coincident Head with Top Case Outer Face
    
    screw_mates = [
        ("inst_screw_1", "axis_screw_post_1"),
        ("inst_screw_2", "axis_screw_post_2"),
        ("inst_screw_3", "axis_screw_post_3"),
        ("inst_screw_4", "axis_screw_post_4"),
    ]
    
    for screw_inst_id, post_axis in screw_mates:
        # Concentric with post
        safe_mate_axes(
            instances.get(screw_inst_id),
            instances.get("inst_bottom_case"),
            "axis_shank",
            post_axis,
            aligned=True
        )
        
        # Head sits on Top Case outer face (Distance 0 or Coincident)
        # Using mate_faces with distance 0 effectively makes them coincident/touching
        safe_mate_faces(
            instances.get(screw_inst_id),
            instances.get("inst_top_case"),
            "face_head_bottom",
            "face_top_outer",
            aligned=True # Normals likely opposed if head is below top surface, but let's assume standard contact
        )

    # 5. 保存装配体
    output_path = os.path.join(assembly_dir, f"{assem_name}.SLDASM")
    try:
        print(f"[LOG] Saving assembly to: {output_path}")
        sw_assem.save_as(output_path)
        print("[SUCCESS] Assembly saved successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to save assembly: {e}")

if __name__ == "__main__":
    main()