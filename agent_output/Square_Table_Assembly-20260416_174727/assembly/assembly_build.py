# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, AssemDoc
import os

def build_assembly():
    # 1. 初始化 SolidWorks 应用程序
    sw_app = SldWorksApp()
    assem_name = "Square_Table_Assembly"
    
    # 2. 创建并激活装配体文档
    print(f"开始创建装配体: {assem_name}")
    sw_assem_ptr = sw_app.createAndActivate_sw_assembly(assem_name)
    if not sw_assem_ptr:
        print("错误：无法创建装配体文档")
        return
    sw_assem = AssemDoc(sw_assem_ptr)

    # 3. 定义零件路径
    tabletop_path = r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_174727\parts\tabletop\tabletop.SLDPRT"
    table_leg_path = r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_174727\parts\table_leg\table_leg.SLDPRT"
    screw_path = r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_174727\parts\screw\screw.SLDPRT"
    output_path = r"D:\a_src\python\sw_agent\agent_output\Square_Table_Assembly-20260416_174727\assembly\Square_Table_Assembly.SLDASM"

    # 4. 插入组件并记录组件名称
    # 插入桌面 (基准件)
    print("正在插入桌面...")
    comp_tabletop = sw_assem.add_component(tabletop_path, 0, 0, 0)
    
    # 插入 4 个桌腿
    print("正在插入桌腿...")
    legs = []
    leg_positions = [(0.36, 0.36, -0.72), (-0.36, 0.36, -0.72), (-0.36, -0.36, -0.72), (0.36, -0.36, -0.72)]
    for i, pos in enumerate(leg_positions):
        leg_name = sw_assem.add_component(table_leg_path, pos[0], pos[1], pos[2])
        legs.append(leg_name)

    # 插入 4 个螺钉
    print("正在插入螺钉...")
    screws = []
    screw_positions = [(0.36, 0.36, 0.03), (-0.36, 0.36, 0.03), (-0.36, -0.36, 0.03), (0.36, -0.36, 0.03)]
    for i, pos in enumerate(screw_positions):
        screw_name = sw_assem.add_component(screw_path, pos[0], pos[1], pos[2])
        screws.append(screw_name)

    # 5. 执行配合约束
    if comp_tabletop:
        # 遍历 4 个位置进行配合 (根据规划，桌面有 hole_axis_1 到 4)
        for i in range(4):
            leg_comp = legs[i]
            screw_comp = screws[i]
            hole_axis = f"hole_axis_{i+1}"
            # 假设桌腿和螺钉的接口名称在所有实例中一致
            
            print(f"正在执行第 {i+1} 组配合...")
            
            # 桌腿与桌面配合
            if leg_comp:
                # 轴同心: 桌腿中心孔轴线 与 桌面孔轴线
                sw_assem.mate_axes(assem_name, leg_comp, comp_tabletop, "leg_hole_axis", hole_axis, aligned=True)
                # 面重合: 桌腿顶面 与 桌面底面
                sw_assem.mate_faces(assem_name, leg_comp, comp_tabletop, "top_face", "bottom_face", aligned=False)
            
            # 螺钉与桌面配合
            if screw_comp:
                # 轴同心: 螺钉轴线 与 桌面孔轴线
                sw_assem.mate_axes(assem_name, screw_comp, comp_tabletop, "screw_axis", hole_axis, aligned=True)
                # 面重合: 螺钉头下表面 与 桌面沉头座面 (规划中定义了 hole_step_face_1，此处简化逻辑)
                # 注意：如果规划中只定义了 hole_step_face_1，实际应用中可能需要对应各孔位面名
                step_face = "hole_step_face_1" # 依据规划 JSON 提供的接口名
                sw_assem.mate_faces(assem_name, screw_comp, comp_tabletop, "head_bottom_face", step_face, aligned=False)

    # 6. 保存装配体
    print(f"正在保存装配体到: {output_path}")
    sw_assem.save_as(output_path)
    print("装配任务完成。")

if __name__ == "__main__":
    try:
        build_assembly()
    except Exception as e:
        print(f"装配过程中发生异常: {str(e)}")