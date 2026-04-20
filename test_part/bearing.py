from pyswassem import SldWorksApp, PartDoc, AssemDoc
import math

def build_cylindrical_roller_bearing():
    sw = SldWorksApp()
    workdir = sw.create_workdir("cylindrical_bearing_job")

    # ==========================================
    # 0. 全局核心参数 (单位: 米)
    # ==========================================
    ri = 0.030          # 内圈内径 (30mm)
    ro = 0.060          # 外圈外径 (60mm)
    rm = 0.045          # 滚子分布中心圆半径 (45mm)
    rr = 0.007          # 滚子半径 (7mm, 即直径14mm)
    bw = 0.025          # 轴承总宽度 (25mm)
    pw = 0.018          # 滚子长度/滚道宽度 (18mm)
    
    num_rollers = 12    # 滚子数量
    
    # 衍生径向尺寸
    r_track_in = rm - rr    # 内圈滚道底径 (38mm)
    r_flange_in = 0.042     # 内圈挡边外径 (保留4mm挡边)
    r_track_out = rm + rr   # 外圈滚道底径 (52mm)
    r_flange_out = 0.048    # 外圈挡边内径 (保留4mm挡边)

    inner_path = sw.get_part_path(workdir, "inner_ring")
    outer_path = sw.get_part_path(workdir, "outer_ring")
    cage_path = sw.get_part_path(workdir, "cage")
    roller_path = sw.get_part_path(workdir, "roller")
    assem_path = sw.get_assembly_path(workdir, "bearing_assem")

    # ==========================================
    # 1. 内圈 (Inner Ring) - 凹槽向外
    # ==========================================
    inner_ring = PartDoc(sw.createAndActivate_sw_part("inner_ring"))
    sk_inner = inner_ring.insert_sketch_on_plane("XY")
    
    # 绘制向外凹的闭合轮廓 (以Y轴为对称中心)
    pts_inner = [
        (ri, bw/2), (ri, -bw/2),                    # 内孔竖线
        (r_flange_in, -bw/2), (r_flange_in, -pw/2), # 下挡边
        (r_track_in, -pw/2), (r_track_in, pw/2),    # 滚道底
        (r_flange_in, pw/2), (r_flange_in, bw/2),   # 上挡边
        (ri, bw/2)                                  # 闭合回起点
    ]
    inner_ring.create_lines(pts_inner, sketch_ref="XY")
    inner_ring.create_construction_line(0, -0.1, 0, 0.1, sketch_ref="XY") # 旋转轴
    inner_ring.revolve(sk_inner, angle=360, merge=True)

    inner_ring.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_Main")
    inner_ring.create_ref_plane("XZ", offset_val=0.0, target_plane_name="Mate_Center")
    inner_ring.save_as(inner_path)

    # ==========================================
    # 2. 外圈 (Outer Ring) - 凹槽向内
    # ==========================================
    outer_ring = PartDoc(sw.createAndActivate_sw_part("outer_ring"))
    sk_outer = outer_ring.insert_sketch_on_plane("XY")
    
    # 绘制向内凹的闭合轮廓
    pts_outer = [
        (ro, bw/2), (ro, -bw/2),                      # 外圆竖线
        (r_flange_out, -bw/2), (r_flange_out, -pw/2), # 下挡边
        (r_track_out, -pw/2), (r_track_out, pw/2),    # 滚道顶
        (r_flange_out, pw/2), (r_flange_out, bw/2),   # 上挡边
        (ro, bw/2)                                    # 闭合
    ]
    outer_ring.create_lines(pts_outer, sketch_ref="XY")
    outer_ring.create_construction_line(0, -0.1, 0, 0.1, sketch_ref="XY")
    outer_ring.revolve(sk_outer, angle=360, merge=True)

    outer_ring.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_Main")
    outer_ring.create_ref_plane("XZ", offset_val=0.0, target_plane_name="Mate_Center")
    outer_ring.save_as(outer_path)

    # ==========================================
    # 3. 保持架 (Cage) - 旋转细长矩形 + 阵列切除
    # ==========================================
    cage = PartDoc(sw.createAndActivate_sw_part("cage"))
    sk_cage_prof = cage.insert_sketch_on_plane("XY")
    
    # 保持架环基体：厚度4mm，宽度22mm
    c_in, c_out = 0.043, 0.047
    c_y = 0.011
    pts_cage = [(c_in, c_y), (c_in, -c_y), (c_out, -c_y), (c_out, c_y), (c_in, c_y)]
    cage.create_lines(pts_cage, sketch_ref="XY")
    cage.create_construction_line(0, -0.1, 0, 0.1, sketch_ref="XY")
    cage.revolve(sk_cage_prof, angle=360, merge=True)

    # 在 XZ 面（俯视）一次性画出 12 个圆柱兜孔，直接切透！(替代布尔减)
    sk_pockets = cage.insert_sketch_on_plane("XZ")
    for i in range(num_rollers):
        theta = 2 * math.pi * i / num_rollers
        x = rm * math.cos(theta)
        z = rm * math.sin(theta)
        # 半径加 0.2mm 间隙，显得更加真实
        cage.create_circle(x, z, radius=rr + 0.0002, sketch_ref="XZ")
    
    # 双向拉伸切除，切透保持架环
    cage.extrude_cut(sk_pockets, depth=0.03, single_direction=False)

    # [装配基准预埋]
    cage.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_Main")
    cage.create_ref_plane("XZ", offset_val=0.0, target_plane_name="Mate_Center")
    
    # 为12个滚子预埋绝对装配轴 (-Y -> +Y)
    for i in range(num_rollers):
        theta = 2 * math.pi * i / num_rollers
        x = rm * math.cos(theta)
        z = rm * math.sin(theta)
        cage.create_axis((x, -0.1, z), (x, 0.1, z), f"Axis_Roller_{i}")
        
    cage.save_as(cage_path)

    # ==========================================
    # 4. 滚子 (Roller) - 简单圆柱拉伸
    # ==========================================
    roller = PartDoc(sw.createAndActivate_sw_part("roller"))
    sk_roller = roller.insert_sketch_on_plane("XZ")
    roller.create_circle(0, 0, radius=rr, sketch_ref="XZ")
    
    # 向上拉伸 18mm (从 Y=0 到 Y=0.018)
    roller.extrude(sk_roller, depth=pw, single_direction=True, merge=True)

    # 基准预埋
    roller.create_axis((0, -0.1, 0), (0, 0.1, 0), "Axis_Main")
    # 滚子的中面在 Y = 0.009
    roller.create_ref_plane("XZ", offset_val=pw/2, target_plane_name="Mate_Center_Roller")
    roller.save_as(roller_path)

    # ==========================================
    # 5. 总装配 (Assembly) - 完美执行你的物理顺序
    # ==========================================
    assem_name = "bearing_assem"
    assem = AssemDoc(sw.createAndActivate_sw_assembly(assem_name))

    # 导入保持架作为核心基准件
    comp_cage = assem.add_component(cage_path, 0, 0, 0)

    # 【第一步】先将 12 个滚子装配到保持架上
    for i in range(num_rollers):
        comp_roller = assem.add_component(roller_path, 0, 0.1, 0)
        
        # 轴配合：滚子主轴 对齐 保持架兜孔预埋轴
        assem.mate_axes(assem_name, comp_cage, comp_roller, f"Axis_Roller_{i}", "Axis_Main", aligned=True)
        # 面配合：调用最新 API，直接让两个不同名称的中面对齐
        assem.mate_faces(assem_name, comp_cage, comp_roller, plane_name1="Mate_Center", plane_name2="Mate_Center_Roller", aligned=True)

    # 【第二步】将内圈和外圈装配到已经挂满滚子的保持架上
    comp_inner = assem.add_component(inner_path, 0.1, 0, 0)
    comp_outer = assem.add_component(outer_path, -0.1, 0, 0)

    # 内圈对齐保持架
    assem.mate_axes(assem_name, comp_cage, comp_inner, "Axis_Main", "Axis_Main", aligned=True)
    assem.mate_faces(assem_name, comp_cage, comp_inner, plane_name1="Mate_Center", plane_name2="Mate_Center", aligned=True)

    # 外圈对齐保持架
    assem.mate_axes(assem_name, comp_cage, comp_outer, "Axis_Main", "Axis_Main", aligned=True)
    assem.mate_faces(assem_name, comp_cage, comp_outer, plane_name1="Mate_Center", plane_name2="Mate_Center", aligned=True)

    assem.save_as(assem_path)
    print(f"圆柱滚子轴承装配完毕！文件保存至: {assem_path}")

if __name__ == "__main__":
    build_cylindrical_roller_bearing()