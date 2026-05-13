from pysw import SldWorksApp, PartDoc
import os

# 1. 初始化应用和路径
swapp = SldWorksApp()
# 零件规格参数
M = 0.002  # 模数 2mm
Z = 54     # 齿数
B = 0.01   # 齿宽 10mm
OD = 0.12  # 外径 120mm

# 目标保存路径
model_file = r"D:\a_src\python\sw_agent\agent_output\planetary_gearbox-20260512_170510\parts\ring_gear\part_output\code\ring_gear.SLDPRT"
workdir = os.path.dirname(model_file)

# 2. 物化标准件并打开工作副本
# 标准件源路径
standard_path = r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT"

# 复制并打开零件
sgear = PartDoc(swapp.copy_standard_part_to_workdir_and_open(
    standard_part_path=standard_path,
    workdir=workdir,
    new_part_name="ring_gear.SLDPRT"
))

print(f"Step 1: Standard part materialized and opened at {model_file}")

# 3. 设置齿轮主动参数
# 逻辑：标准件生成的是外齿轮。我们将利用生成的齿形作为“切除模板”。
sgear.set_global_variable("M", str(M * 1000)) # 模板接受mm字符串
sgear.set_global_variable("Z", str(Z))
sgear.set_global_variable("B", str(B * 1000))

print(f"Step 2: Global variables set: M={M*1000}, Z={Z}, B={B*1000}")

# 4. 二次加工：实现内齿逻辑
# 修复逻辑：
# 1. 模板已经生成了外齿轮实体。
# 2. 我们在 XY 平面创建一个外径为 120mm 的圆。
# 3. 关键：为了形成内齿空腔，我们必须切除掉齿轮的“齿谷”以外的所有部分。
# 考虑到 pysw 封装限制，最稳健的内齿模拟方式是：
# 在 XY 平面画一个圆，直径等于齿根圆（df），然后进行 extrude_cut 贯穿切除。
# 这样就去掉了外齿轮的轮毂部分，只剩下悬浮的齿。
# 然后再拉伸一个 OD=120, ID=df 的圆环，与这些齿合并。
# 齿根圆直径 df 约为 M*(Z-2.5) = 2*(54-2.5) = 103mm = 0.103m
df = M * (Z - 2.5) 

# 第一步：切除轮毂
sketch_bore = sgear.insert_sketch_on_plane("XY")
sgear.create_circle(0, 0, df / 2, "XY")
sgear.extrude_cut(sketch_bore, B)
print(f"Step 3.1: Hub removed by cutting circle with diameter {df}m.")

# 第二步：拉伸外环并合并
sketch_ring = sgear.insert_sketch_on_plane("XY")
sgear.create_circle(0, 0, OD / 2, "XY")
sgear.create_circle(0, 0, df / 2, "XY") 
sgear.extrude(sketch_ring, B)
print(f"Step 3.2: Ring body extruded (OD={OD}m, ID={df}m) and merged with remaining teeth.")

# 5. 创建接口
# 轴接口：中心旋转轴
sgear.create_axis((0, 0, 0), (0, 0, B), "central_axis")

# 面接口：固定安装面（根据规格要求，mounting_face 位于 Z=0）
sgear.create_ref_plane("XY", 0, "mounting_face")

# 点接口：中心点 (0,0,0)
# 显式创建参考轴，其起点即为 center_point
sgear.create_axis((0, 0, 0), (0, 0, 0.001), "center_point")

print("Step 4: Interfaces created: central_axis, mounting_face, center_point")

# 6. 保存零件
sgear.save_as(model_file)
print(f"Step 5: Part saved successfully to {model_file}")