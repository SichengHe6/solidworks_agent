from pysw import SldWorksApp, PartDoc
import os

# 零件参数定义 (单位换算: mm -> m)
MODULUS = 0.002
TEETH_COUNT = 18
GEAR_WIDTH = 0.020
HOLE_DIAMETER = 0.008
PITCH_DIAMETER = MODULUS * TEETH_COUNT  # 0.036m

# 文件路径
model_file = r"D:\a_src\python\sw_agent\agent_output\Planetary_Gearbox_Assembly-20260512_160944\parts\planet_gear\planet_gear.SLDPRT"
model_dir = os.path.dirname(model_file)

def main():
    # 1. 初始化
    app = SldWorksApp()
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        
    # 2. 创建零件
    sw_doc = PartDoc(app.createAndActivate_sw_part("planet_gear"))
    print("开始建模行星轮...")

    # 3. 绘制齿轮主体 (简化建模：使用分度圆作为主体，实际齿轮廓形通常由插件生成，此处按指令绘制分度圆拉伸)
    # 在 XY 平面绘制分度圆
    sketch_main = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(0, 0, PITCH_DIAMETER / 2, "XY")
    
    # 拉伸 20mm
    sw_doc.extrude(sketch_main, depth=GEAR_WIDTH, single_direction=True)
    print(f"完成齿轮主体拉伸，厚度: {GEAR_WIDTH}m")

    # 4. 切除中心通孔
    # 在拉伸后的顶面或原 XY 平面切孔
    sketch_hole = sw_doc.insert_sketch_on_plane("XY")
    sw_doc.create_circle(0, 0, HOLE_DIAMETER / 2, "XY")
    
    # 拉伸切除
    sw_doc.extrude_cut(sketch_hole, depth=GEAR_WIDTH, single_direction=True)
    print(f"完成中心孔切除，孔径: {HOLE_DIAMETER}m")

    # 5. 创建装配接口
    # 接口1: bottom_face (装配基准面，位于 Z=0)
    sw_doc.create_ref_plane("XY", 0, "bottom_face")
    
    # 接口2: center_axis (旋转中心轴)
    sw_doc.create_axis((0, 0, 0), (0, 0, GEAR_WIDTH), "center_axis")
    print("已创建装配接口: bottom_face, center_axis")

    # 6. 保存零件
    save_status = sw_doc.save_as(model_file)
    if save_status:
        print(f"行星轮模型成功保存至: {model_file}")
    else:
        print("保存失败，请检查路径或权限。")

if __name__ == "__main__":
    main()