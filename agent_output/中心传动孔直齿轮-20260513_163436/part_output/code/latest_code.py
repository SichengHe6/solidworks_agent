from pysw import SldWorksApp, PartDoc
import os

# ── 零件规格 ──────────────────────────────────────────
part_id = "spur_gear_with_bore"
part_name = "中心传动孔直齿轮"

# 工作区路径
WORK_DIR = r"D:\a_src\python\sw_agent\agent_output\中心传动孔直齿轮-20260513_163436\part_output\code"
MODEL_FILE = os.path.join(WORK_DIR, "spur_gear_with_bore.SLDPRT")
STANDARD_PART = r"D:\a_src\python\sw_agent\standard_swpart\gear\spur_gear.SLDPRT"

# 尺寸常量（mm → m）
BORE_DIAMETER_MM = 20.0
BORE_RADIUS_M = BORE_DIAMETER_MM / 2.0 / 1000.0     # 0.01 m
GEAR_WIDTH_MM = 10.0
GEAR_WIDTH_M = GEAR_WIDTH_MM / 1000.0                # 0.01 m

swapp = SldWorksApp()
print("[步骤1] 复制标准件到工作区并打开 ...")

sgear = PartDoc(swapp.copy_standard_part_to_workdir_and_open(
    standard_part_path=STANDARD_PART,
    workdir=WORK_DIR,
    new_part_name="spur_gear_with_bore.SLDPRT",
))

# ── 设置齿轮主动参数 ──────────────────────────────
print("[步骤2] 设置齿轮参数 ...")
sgear.set_global_variable("M", "2mm")
sgear.set_global_variable("Z", "30")
sgear.set_global_variable("B", "10mm")
sgear.set_global_variable("Alpha", "20deg")
sgear.set_global_variable("Hax", "1")
sgear.set_global_variable("Cx", "0.25")

# ── 添加中心通孔 ────────────────────────────────
print("[步骤3] 创建中心通孔草图与拉伸切除 ...")
sketch_bore = sgear.insert_sketch_on_plane("XY")
sgear.create_circle(0.0, 0.0, BORE_RADIUS_M, "XY")
sgear.extrude_cut(sketch_bore, GEAR_WIDTH_M)

# ── 创建接口参考几何 ────────────────────────────
print("[步骤4] 创建命名接口：参考面与参考轴 ...")

# 齿轮中面（XY平面偏移 0，按要求位于 XY 平面）
sgear.create_ref_plane("XY", 0.0, "gear_mid_plane")

# 前端面（齿轮正端面，位于 Z = GEAR_WIDTH_M = 0.01）
sgear.create_ref_plane("XY", GEAR_WIDTH_M, "front_face")

# 后端面（齿轮起始面，位于 Z = 0）
sgear.create_ref_plane("XY", 0.0, "back_face")

# 中心旋转轴
sgear.create_axis([0.0, 0.0, 0.0], [0.0, 0.0, GEAR_WIDTH_M], "shaft_axis")

print("  - bore_cylindrical_face：通孔内圆柱面，可用于装配配合")

# ── 保存 ──────────────────────────────────────────
print(f"[步骤5] 保存模型到 {MODEL_FILE} ...")
save_ok = sgear.save_as(MODEL_FILE)
if save_ok:
    print("  √ 保存成功")
else:
    print("  × 保存失败，请检查路径权限")

print("=== 中心传动孔直齿轮建模完成 ===")