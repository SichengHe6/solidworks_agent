import os
from pathlib import Path

from pysw import SldWorksApp
import inspect

print("SldWorksApp module:", SldWorksApp.__module__)
print("SldWorksApp file:", inspect.getfile(SldWorksApp))

sw_app = SldWorksApp()
print("has capture:", hasattr(sw_app, "capture_active_model_views"))
print("capture methods:", [m for m in dir(sw_app) if "capture" in m])

def main():
    sw_app = SldWorksApp()

    out_dir = r"D:\a_src\python\sw_agent\agent_output\screen_shoot"
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    shots = sw_app.capture_active_model_views(
        output_dir=out_dir,
        base_name="active_model_test",
        width=1600,
        height=1200,
        delay=0.3,
    )

    print("\n===== 截图结果 =====")
    if not shots:
        print("❌ 没有生成任何截图。请确认 SOLIDWORKS 当前有打开的零件或装配体。")
        return

    for view_name, file_path in shots.items():
        exists = os.path.exists(file_path)
        size = os.path.getsize(file_path) if exists else 0

        if exists and size > 0:
            print(f"✅ {view_name}: {file_path}  ({size} bytes)")
        else:
            print(f"❌ {view_name}: 文件不存在或为空 -> {file_path}")


if __name__ == "__main__":
    main()