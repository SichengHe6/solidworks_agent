# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, PartDoc

def main():
    """
    零件建模：方柱桌腿 (table_leg)
    功能：支撑桌面，顶面中心设有安装孔
    """
    # 1. 初始化与路径配置
    part_id = "table_leg"
    model_file = r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_174727\parts\table_leg\table_leg.SLDPRT"
    
    app = SldWorksApp()
    # 创建并激活零件文档，显式指定零件名称
    sw_doc = PartDoc(app.createAndActivate_sw_part(part_id))
    print(f"开始建模零件: {part_id}")

    # 2. 建模参数换算 (mm -> m)
    leg_width = 50 * 0.001   # 0.050m
    leg_height = 720 * 0.001 # 0.720m
    hole_diam = 8 * 0.001    # 0.008m
    hole_depth = 30 * 0.001  # 0.030m

    # 3. 步骤一：创建桌腿主体
    # 在 XY 基准面绘制 50mm x 50mm 的中心矩形
    print(f"[{part_id}] 正在创建主体拉伸...")
    sketch_main = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_centre_rectangle(center_x=0, center_y=0, width=leg_width, height=leg_width, sketch_ref="XY")
    # 沿 Z 轴正向拉伸 720mm
    sw_doc.extrude(sketch_main, depth=leg_height, single_direction=True)

    # 4. 步骤二：在顶面切除安装孔
    # 在 Z = 0.720m 处创建参考平面作为顶面
    print(f"[{part_id}] 正在创建顶面安装孔...")
    top_plane = sw_doc.create_workplane_p_d("XY", leg_height)
    sketch_hole = sw_doc.insert_sketch_on_plane(top_plane)
    sw_doc.create_circle(center_x=0, center_y=0, radius=hole_diam/2, sketch_ref="XY")
    # 向实体内部（Z 负方向）切除 30mm
    sw_doc.extrude_cut(sketch_hole, depth=-hole_depth, single_direction=True)

    # 5. 步骤三：定义装配接口 (Interfaces)
    # 接口 1: top_face (用于与桌面底面贴合)
    # 重新命名或基于位置创建参考面，确保装配阶段可引用
    sw_doc.create_ref_plane("XY", leg_height, target_plane_name="top_face")
    
    # 接口 2: leg_hole_axis (用于同心约束)
    # 轴线定义为从顶面中心指向孔底
    sw_doc.create_axis(
        pt1=(0, 0, leg_height), 
        pt2=(0, 0, leg_height - hole_depth), 
        axis_name="leg_hole_axis"
    )
    print(f"[{part_id}] 装配接口 'top_face' 和 'leg_hole_axis' 已定义")

    # 6. 保存零件
    print(f"[{part_id}] 正在保存模型至: {model_file}")
    save_status = sw_doc.save_as(model_file)
    
    if save_status:
        print(f"[{part_id}] 建模任务成功完成。")
    else:
        print(f"[{part_id}] 错误：模型保存失败。")

if __name__ == "__main__":
    main()