# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    # 1. 初始化应用与零件文档
    app = SldWorksApp()
    part_name = "Link1"
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_name))
    
    # 定义输出路径
    model_file_path = r"D:\a_src\python\sw_agent\agent_output\4Axis_RobotArm_Assembly-20260421_171347\parts\link1\link1.SLDPRT"
    
    print(f"开始建模: {part_name}")

    # 单位换算: mm -> m
    # Cylinder: D50 (R=0.025), L150 (0.15)
    # Blocks: 60x60x20 (0.06x0.06x0.02)
    # Bottom Hole: D50 (R=0.025)
    # Top Pin: D10 (R=0.005), L20 (0.02)
    
    cyl_radius = 0.025
    cyl_length = 0.15
    
    block_width = 0.06
    block_height = 0.06
    block_thickness = 0.02
    
    hole_radius_bottom = 0.025
    
    pin_radius_top = 0.005
    pin_length = 0.02
    
    chamfer_dist = 0.002 # C2 chamfer

    # --- Step 1: Central Cylinder ---
    # Sketch on XY plane at Z=0
    sketch_cyl = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(center_x=0, center_y=0, radius=cyl_radius, sketch_ref="XY")
    # Extrude along +Z from 0 to 0.15
    extrude_cyl = sw_doc.extrude(sketch_cyl, depth=cyl_length, single_direction=True, merge=True)
    print("Step 1: Central Cylinder created.")

    # --- Step 2: Bottom Block ---
    # Located at Z=-0.02 to Z=0. 
    # Create sketch on XY plane (which is at Z=0 relative to origin, but we need to extrude downwards)
    # Actually, the previous extrusion ended at Z=0.15. The base of the cylinder is at Z=0.
    # We want the bottom block to be attached to the bottom of the cylinder (Z=0).
    # So we sketch on XY (Z=0) and extrude in -Z direction.
    sketch_bot_block = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=block_width, height=block_height, sketch_ref="XY")
    # Extrude down by block_thickness
    extrude_bot_block = sw_doc.extrude(sketch_bot_block, depth=-block_thickness, single_direction=True, merge=True)
    print("Step 2: Bottom Block created.")

    # --- Step 3: Top Block ---
    # Located at Z=0.15 to Z=0.17.
    # We need a plane at Z=0.15 or sketch on the top face of the cylinder.
    # Let's create an offset plane at Z=0.15 for clarity, or just use the existing geometry reference if possible.
    # Using create_workplane_p_d to get a plane at Z=0.15 parallel to XY.
    plane_top = sw_doc.create_workplane_p_d(plane="XY", offset_val=cyl_length)
    
    sketch_top_block = sw_doc.insert_sketch_on_plane(plane_top)
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=block_width, height=block_height, sketch_ref="XY")
    # Extrude up by block_thickness
    extrude_top_block = sw_doc.extrude(sketch_top_block, depth=block_thickness, single_direction=True, merge=True)
    print("Step 3: Top Block created.")

    # --- Step 4: Bottom Hole ---
    # On bottom face of Bottom Block (Z = -0.02).
    # Create plane at Z = -0.02
    plane_bot_face = sw_doc.create_workplane_p_d(plane="XY", offset_val=-block_thickness)
    
    sketch_bot_hole = sw_doc.insert_sketch_on_plane(plane_bot_face)
    sw_doc.create_circle(center_x=0, center_y=0, radius=hole_radius_bottom, sketch_ref="XY")
    # Cut upwards through the block (depth = block_thickness)
    cut_bot_hole = sw_doc.extrude_cut(sketch_bot_hole, depth=block_thickness, single_direction=True)
    print("Step 4: Bottom Hole created.")

    # --- Step 5: Top Pin ---
    # On side face of Top Block. 
    # Top Block is centered at X=0, Y=0. Width/Height 0.06.
    # Side face at Y+ is at Y = 0.03.
    # Pin extends along +Y.
    # Pin center is at Z = 0.15 + 0.01 (mid-height of top block) = 0.16.
    # Pin center X = 0.
    
    # Create a plane parallel to XZ at Y = 0.03 (Right side face of top block)
    # Note: Standard planes are XY, XZ, ZY. 
    # To sketch on the Y+ face, we can use a plane offset from XZ? No, XZ is Y=0.
    # We need a plane parallel to XZ at Y=0.03.
    # create_workplane_p_d takes "XY", "XZ", "ZY". 
    # If we use "XZ" as base, offsetting it moves it along Y.
    plane_pin_side = sw_doc.create_workplane_p_d(plane="XZ", offset_val=block_width/2) # Y = 0.03
    
    sketch_pin = sw_doc.insert_sketch_on_plane(plane_pin_side)
    # In XZ plane context: X is X, Y is Z.
    # Center of pin: X=0, Z=0.16.
    # In sketch coordinates (X, Y_sketch): X=0, Y_sketch=0.16.
    sw_doc.create_circle(center_x=0, center_y=0.16, radius=pin_radius_top, sketch_ref="XZ")
    
    # Extrude outwards along +Y. 
    # The normal of the XZ plane at Y=0.03 points towards +Y? 
    # Usually, offset positive means moving in positive axis direction.
    # So extruding with positive depth should go further +Y.
    extrude_pin = sw_doc.extrude(sketch_pin, depth=pin_length, single_direction=True, merge=True)
    print("Step 5: Top Pin created.")

    # --- Step 6: Chamfers ---
    # Apply C2 chamfer to sharp edges of blocks.
    # This is tricky without specific edge selection API that uses IDs.
    # The API `chamfer_edges` requires points on the edges.
    
    # Bottom Block Edges (Z = -0.02 to 0, X/Y = +/- 0.03)
    # Top edges of bottom block (Z=0):
    # Points: (0.03, 0.03, 0), (-0.03, 0.03, 0), etc.
    # Bottom edges of bottom block (Z=-0.02):
    # Points: (0.03, 0.03, -0.02), etc.
    
    # Top Block Edges (Z = 0.15 to 0.17, X/Y = +/- 0.03)
    # Bottom edges of top block (Z=0.15):
    # Points: (0.03, 0.03, 0.15), etc.
    # Top edges of top block (Z=0.17):
    # Points: (0.03, 0.03, 0.17), etc.
    
    # Let's select representative points for the vertical edges and horizontal edges.
    # Vertical edges of Bottom Block:
    pts_bot_vert = [
        (0.03, 0.03, -0.01), # Corner approx
        (-0.03, 0.03, -0.01),
        (-0.03, -0.03, -0.01),
        (0.03, -0.03, -0.01)
    ]
    
    # Horizontal edges of Bottom Block (Top rim at Z=0)
    pts_bot_horiz_top = [
        (0.03, 0, 0), # Midpoint of edge
        (0, 0.03, 0),
        (-0.03, 0, 0),
        (0, -0.03, 0)
    ]
    
    # Horizontal edges of Bottom Block (Bottom rim at Z=-0.02)
    pts_bot_horiz_bot = [
        (0.03, 0, -0.02),
        (0, 0.03, -0.02),
        (-0.03, 0, -0.02),
        (0, -0.03, -0.02)
    ]
    
    # Vertical edges of Top Block:
    pts_top_vert = [
        (0.03, 0.03, 0.16),
        (-0.03, 0.03, 0.16),
        (-0.03, -0.03, 0.16),
        (0.03, -0.03, 0.16)
    ]
    
    # Horizontal edges of Top Block (Bottom rim at Z=0.15)
    pts_top_horiz_bot = [
        (0.03, 0, 0.15),
        (0, 0.03, 0.15),
        (-0.03, 0, 0.15),
        (0, -0.03, 0.15)
    ]
    
    # Horizontal edges of Top Block (Top rim at Z=0.17)
    pts_top_horiz_top = [
        (0.03, 0, 0.17),
        (0, 0.03, 0.17),
        (-0.03, 0, 0.17),
        (0, -0.03, 0.17)
    ]
    
    all_chamfer_pts = pts_bot_vert + pts_bot_horiz_top + pts_bot_horiz_bot + \
                      pts_top_vert + pts_top_horiz_bot + pts_top_horiz_top
    
    try:
        sw_doc.chamfer_edges(on_line_points=all_chamfer_pts, distance=chamfer_dist, angle=45.0)
        print("Step 6: Chamfers applied.")
    except Exception as e:
        print(f"Warning: Chamfer application might have failed or partially failed: {e}")

    # --- Step 7: Interfaces ---
    
    # 1. Face: bottom_face_block (Normal -Z)
    # This is the bottom face of the bottom block at Z = -0.02.
    # We can create a reference plane coincident with this face for mating purposes if needed, 
    # but usually faces are selected by geometry. However, the prompt asks to "expose interface names".
    # Creating a named reference plane at Z = -0.02.
    ref_plane_bottom = sw_doc.create_ref_plane(plane="XY", offset_val=-block_thickness, target_plane_name="bottom_face_block")
    
    # 2. Face: top_face_block (Normal +Z)
    # This is the top face of the top block at Z = 0.17.
    ref_plane_top = sw_doc.create_ref_plane(plane="XY", offset_val=cyl_length + block_thickness, target_plane_name="top_face_block")
    
    # 3. Axis: bottom_hole_axis (Along Z, centered)
    # From (0,0,-0.02) to (0,0,0) roughly, or just along Z through origin.
    axis_bottom_hole = sw_doc.create_axis(pt1=(0, 0, -0.05), pt2=(0, 0, 0.05), axis_name="bottom_hole_axis")
    
    # 4. Axis: top_pin_axis (Along Y, centered in top block side)
    # Center of pin is at X=0, Y=0.03 (face), Z=0.16.
    # Axis runs along Y.
    # Pt1: (0, 0.03 - 0.01, 0.16) -> (0, 0.02, 0.16)
    # Pt2: (0, 0.03 + 0.01, 0.16) -> (0, 0.04, 0.16)
    # Or simply define it passing through the center of the pin feature.
    axis_top_pin = sw_doc.create_axis(pt1=(0, 0.02, 0.16), pt2=(0, 0.04, 0.16), axis_name="top_pin_axis")

    print("Step 7: Interfaces created.")

    # --- Step 8: Save ---
    success = sw_doc.save_as(model_file_path)
    if success:
        print(f"Model saved successfully to {model_file_path}")
    else:
        print("Failed to save model.")

if __name__ == "__main__":
    main()