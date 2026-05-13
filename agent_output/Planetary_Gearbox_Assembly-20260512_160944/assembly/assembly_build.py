from pysw import SldWorksApp, AssemDoc
import os

def build_assembly():
    # 1. 初始化 SolidWorks 应用
    sw_app = SldWorksApp()
    assem_name = "Planetary_Gearbox_Assembly"
    
    # 2. 创建并激活装配体文档
    print(f"正在创建装配体: {assem_name}")
    sw_assem_ptr = sw_app.createAndActivate_sw_assembly(assem_name)
    if not sw_assem_ptr:
        print("错误: 无法创建装配体文档")
        return
    sw_assem = AssemDoc(sw_assem_ptr)

    # 3. 定义零件路径映射 (part_id -> model_file)
    part_paths = {
        "sun_gear": r"D:\a_src\python\sw_agent\agent_output\Planetary_Gearbox_Assembly-20260512_160944\parts\sun_gear\sun_gear.SLDPRT",
        "planet_gear": r"D:\a_src\python\sw_agent\agent_output\Planetary_Gearbox_Assembly-20260512_160944\parts\planet_gear\planet_gear.SLDPRT",
        "ring_gear": r"D:\a_src\python\sw_agent\agent_output\Planetary_Gearbox_Assembly-20260512_160944\parts\ring_gear\ring_gear.SLDPRT",
        "planet_carrier": r"D:\a_src\python\sw_agent\agent_output\Planetary_Gearbox_Assembly-20260512_160944\parts\planet_carrier\planet_carrier.SLDPRT"
    }

    # 4. 插入组件实例并记录组件名 (instance_id -> comp_name)
    instance_map = {}
    
    # 按装配顺序插入
    assembly_sequence = [
        ("ring_gear_inst", "ring_gear", 0, 0, 0),
        ("sun_gear_inst", "sun_gear", 0, 0, 0),
        ("carrier_inst", "planet_carrier", 0, 0, 0),
        ("planet_gear_1", "planet_gear", 36, 0, 0),
        ("planet_gear_2", "planet_gear", -18, 31.17, 0),
        ("planet_gear_3", "planet_gear", -18, -31.17, 0)
    ]

    for inst_id, part_id, x, y, z in assembly_sequence:
        file_path = part_paths[part_id]
        print(f"正在插入实例 {inst_id} (零件: {part_id})...")
        comp_name = sw_assem.add_component(file_path, x, y, z)
        if comp_name:
            instance_map[inst_id] = comp_name
            print(f"实例 {inst_id} 已插入，组件名: {comp_name}")
        else:
            print(f"警告: 实例 {inst_id} 插入失败")

    # 5. 执行配合约束
    print("开始施加配合约束...")

    # 约束 1: 固定内齿圈 (ring_gear_inst)
    # 注意：在 SolidWorks 中第一个插入的零件通常默认固定，这里显式处理或通过配合基准面
    # 规划中 target 为 GROUND，通常对应装配体的基准面
    
    # 约束 2: 太阳轮与内齿圈同轴
    if "sun_gear_inst" in instance_map and "ring_gear_inst" in instance_map:
        sw_assem.mate_axes(assem_name, instance_map["sun_gear_inst"], instance_map["ring_gear_inst"], 
                           "center_axis", "center_axis", aligned=True)
        print("约束: 太阳轮与内齿圈同轴 - 完成")

    # 约束 3: 太阳轮与内齿圈端面对齐
    if "sun_gear_inst" in instance_map and "ring_gear_inst" in instance_map:
        sw_assem.mate_faces(assem_name, instance_map["sun_gear_inst"], instance_map["ring_gear_inst"], 
                            "bottom_face", "bottom_face", aligned=True)
        print("约束: 太阳轮与内齿圈端面对齐 - 完成")

    # 约束 4: 行星架中心与太阳轮轴线重合
    if "carrier_inst" in instance_map and "sun_gear_inst" in instance_map:
        sw_assem.mate_axes(assem_name, instance_map["carrier_inst"], instance_map["sun_gear_inst"], 
                           "main_axis", "center_axis", aligned=True)
        print("约束: 行星架中心与太阳轮同轴 - 完成")

    # 约束 5-7: 行星轮安装到行星架销轴
    for i in range(1, 4):
        inst_id = f"planet_gear_{i}"
        pin_axis = f"pin_axis_{i}"
        if inst_id in instance_map and "carrier_inst" in instance_map:
            sw_assem.mate_axes(assem_name, instance_map[inst_id], instance_map["carrier_inst"], 
                               "center_axis", pin_axis, aligned=True)
            # 补充端面约束（根据规划和评审建议，所有齿轮端面共面）
            sw_assem.mate_faces(assem_name, instance_map[inst_id], instance_map["sun_gear_inst"], 
                                "bottom_face", "bottom_face", aligned=True)
            print(f"约束: 行星轮{i} 安装与端面对齐 - 完成")

    # 6. 保存装配体
    output_path = r"D:\a_src\python\sw_agent\agent_output\Planetary_Gearbox_Assembly-20260512_160944\assembly\Planetary_Gearbox_Assembly.SLDASM"
    print(f"正在保存装配体到: {output_path}")
    sw_assem.save_as(output_path)
    print("装配任务完成。")

if __name__ == "__main__":
    try:
        build_assembly()
    except Exception as e:
        print(f"装配过程中发生异常: {str(e)}")