import math
from pysw import SldWorksApp, PartDoc

def main():
    # 1. 初始化与创建零件
    # 零件参数 (单位换算: mm -> m)
    module = 2.0 / 1000.0
    teeth_count = 54
    width = 20.0 / 1000.0
    outer_diameter = 120.0 / 1000.0
    pitch_diameter = module * teeth_count  # 108mm
    
    # 齿轮几何计算 (简化建模：内齿圈内径通常为分度圆减去约1.25倍模数)
    # 为了装配演示，我们创建一个带内孔的圆环，并模拟内齿效果（简化为内径略大于分度圆的圆孔，或直接按分度圆切除）
    # 按照 instructions: 绘制120mm外圆和108mm内圆
    inner_diameter = pitch_diameter 
    
    model_path = r"D:\a_src\python\sw_agent\agent_output\Planetary_Gearbox_Assembly-20260512_160944\parts\ring_gear\ring_gear.SLDPRT"
    
    app = SldWorksApp()
    sw_doc = PartDoc(app.createAndActivate_sw_part("ring_gear"))
    print("开始构建内齿圈模型...")

    # 2. 创建主体圆环
    # 在 XY 平面绘制外圆和内圆
    sketch1 = sw_doc.insert_sketch_on_plane("XY")
    # 外圆
    sw_doc.create_circle(0, 0, outer_diameter / 2.0, "XY")
    # 内圆 (内齿圈的内径)
    sw_doc.create_circle(0, 0, inner_diameter / 2.0, "XY")
    
    # 拉伸生成实体
    sw_doc.extrude(sketch1, depth=width, single_direction=True)
    print(f"主体拉伸完成，厚度: {width}m")

    # 3. 创建接口
    # 接口1: bottom_face (装配基准面，位于 Z=0)
    # 我们在 XY 平面创建一个参考面，命名为 bottom_face
    sw_doc.create_ref_plane("XY", 0, target_plane_name="bottom_face")
    
    # 接口2: center_axis (中心轴线)
    # 从 (0,0,0) 到 (0,0,width) 的轴
    sw_doc.create_axis((0, 0, 0), (0, 0, width), axis_name="center_axis")
    
    print("接口创建完成: bottom_face, center_axis")

    # 4. 保存零件
    save_success = sw_doc.save_as(model_path)
    if save_success:
        print(f"内齿圈建模成功并保存至: {model_path}")
    else:
        print("零件保存失败，请检查路径或权限。")

if __name__ == "__main__":
    main()