from pysw import SldWorksApp, PartDoc, AssemDoc
import pysw
import os

swapp = SldWorksApp()


sgear = PartDoc(swapp.copy_standard_part_to_workdir_and_open(
    standard_part_path=r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT",
    workdir=r"D:\work\assem_test",
    new_part_name="gear_001.SLDPRT",))

sgear.set_global_variable("Z","30")
s1 = sgear.insert_sketch_on_plane("XY")
sgear.create_circle(0,0,0.001,"XY")
sgear.extrude_cut(s1,0.02)
