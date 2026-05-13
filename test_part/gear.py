from pysw import SldWorksApp, PartDoc, AssemDoc
import pysw
import os

swapp = SldWorksApp()

sgear = PartDoc(swapp.copy_standard_part_to_workdir_and_open(
    standard_part_path=r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT",
    workdir=r"D:\work\assem_test",
    new_part_name="gear_001.SLDPRT",))

# 齿轮主动参数（不包含从动参数）：
# M = 2mm        # 模数
# Z = 30         # 齿数
# B = 10mm       # 齿宽
# Alpha = 20     # 压力角
# Hax = 1        # 齿顶高系数
# Cx = 0.25      # 顶隙系数
sgear.set_global_variable("Z","40")


# 下面是一些示例操作，展示如何使用 PartDoc 类的方法来二次修改零件
sketch1 = sgear.insert_sketch_on_plane("XY")
# 齿轮是从Z=0开始拉伸的，所以在XY平面上画一个圆，作为拉伸的轮廓
sgear.create_circle(0,0,0.01,"XY")
# 拉伸切除，从底面向上切除，切除深度为0.01mm=齿宽，切除后齿轮会有一个通孔
sgear.extrude_cut(sketch1,0.01)

sgear.create_axis([0,0,0], [0,0,0.01], "gear_axis")
sgear.create_ref_plane("XY", 0.01/2, "mid_plane")
sgear.create_ref_plane("XY", 0.01, "top_plane")
sgear.create_ref_plane("XY", 0, "bottom_plane")




