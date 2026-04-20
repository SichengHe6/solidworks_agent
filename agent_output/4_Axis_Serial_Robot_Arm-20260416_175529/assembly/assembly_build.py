# -*- coding: utf-8 -*-
from pyswassem import SldWorksApp, AssemDoc
import os

def assemble_robot():
    # 1. 初始化 SolidWorks 应用程序
    sw_app = SldWorksApp()
    assem_name = "4_Axis_Serial_Robot_Arm"
    save_path = r"D:\a_src\python\sw_agent\agent_output\4_Axis_Serial_Robot_Arm-20260416_175529\assembly\4_Axis_Serial_Robot_Arm.SLDASM"
    
    print(f"开始装配任务: {assem_name}")

    # 2. 创建并激活装配体文档
    sw_assem_ptr = sw_app.createAndActivate_sw_assembly(assem_name)
    if not sw_assem_ptr:
        print("错误: 无法创建装配体文档")
        return
    sw_assem = AssemDoc(sw_assem_ptr)

    # 3. 定义零件路径 (基于 part_results)
    parts_map = {
        "base_station": r"D:\a_src\python\sw_agent\agent_output\4_Axis_Serial_Robot_Arm-20260416_175529\parts\base_station\base_station.SLDPRT",
        "upper_arm": r"D:\a_src\python\sw_agent\agent_output\4_Axis_Serial_Robot_Arm-20260416_175529\parts\upper_arm\upper_arm.SLDPRT",
        "forearm": r"D:\a_src\python\sw_agent\agent_output\4_Axis_Serial_Robot_Arm-20260416_175529\parts\forearm\forearm.SLDPRT",
        "gripper_unit": r"D:\a_src\python\sw_agent\agent_output\4_Axis_Serial_Robot_Arm-20260416_175529\parts\gripper_unit\gripper_unit.SLDPRT"
    }

    # 4. 按顺序插入零件并记录组件名称
    comp_names = {}

    print("步骤 1: 插入底座 (基准件)")
    comp_names["base_station"] = sw_assem.add_component(parts_map["base_station"], 0, 0, 0)
    
    print("步骤 2: 插入大臂")
    comp_names["upper_arm"] = sw_assem.add_component(parts_map["upper_arm"], 0, 0, 0.1)
    
    print("步骤 3: 插入小臂")
    comp_names["forearm"] = sw_assem.add_component(parts_map["forearm"], 0.4, 0, 0.1)
    
    print("步骤 4: 插入夹爪组件")
    comp_names["gripper_unit"] = sw_assem.add_component(parts_map["gripper_unit"], 0.7, 0, 0.1)

    # 检查所有零件是否加载成功
    for p_id, c_name in comp_names.items():
        if not c_name:
            print(f"错误: 零件 {p_id} 插入失败")
            return

    # 5. 执行配合约束
    try:
        # --- 底座与大臂配合 ---
        print("执行配合: 大臂 -> 底座 (第一轴同心)")
        sw_assem.mate_axes(assem_name, comp_names["upper_arm"], comp_names["base_station"], 
                           "axis_1_conn", "axis_1_rot", aligned=True)
        
        print("执行配合: 大臂 -> 底座 (底面贴合)")
        sw_assem.mate_faces(assem_name, comp_names["upper_arm"], comp_names["base_station"], 
                            "arm_bottom_face", "base_top_face", aligned=False) # opposed

        # --- 大臂与小臂配合 ---
        print("执行配合: 小臂 -> 大臂 (第三轴同心)")
        sw_assem.mate_axes(assem_name, comp_names["forearm"], comp_names["upper_arm"], 
                           "axis_3_conn", "axis_3_rot", aligned=True)
        
        print("执行配合: 小臂 -> 大臂 (侧面贴合)")
        # 注意：规划中提到 1mm 间隙，当前标准 mate_faces 通常执行重合，间隙需在模型或后续微调中处理
        sw_assem.mate_faces(assem_name, comp_names["forearm"], comp_names["upper_arm"], 
                            "joint_face_3_conn", "joint_face_3", aligned=False)

        # --- 小臂与夹爪配合 ---
        print("执行配合: 夹爪 -> 小臂 (第四轴同心)")
        sw_assem.mate_axes(assem_name, comp_names["gripper_unit"], comp_names["forearm"], 
                           "axis_4_conn", "axis_4_rot", aligned=True)
        
        print("执行配合: 夹爪 -> 小臂 (末端贴合)")
        sw_assem.mate_faces(assem_name, comp_names["gripper_unit"], comp_names["forearm"], 
                            "mount_face", "end_face", aligned=False)

    except Exception as e:
        print(f"配合过程中发生异常: {str(e)}")

    # 6. 保存装配体
    print(f"正在保存装配体到: {save_path}")
    sw_assem.save_as(save_path)
    print("装配任务完成。")

if __name__ == "__main__":
    assemble_robot()