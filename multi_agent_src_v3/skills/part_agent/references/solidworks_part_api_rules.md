# SolidWorks 零件 API 规则

- 生成完整、可执行的 Python 代码。
- 将模型保存到 `part_spec.workspace.model_file`。
- 打印简短步骤日志。
- 优先使用确定性的特征名。接口名只在用户明确要求或装配规划会引用时作为必须项。
- 路径处理尽量基于工作区。
- 所有 SolidWorks Python API 长度值使用米，包括草图、拉伸/切除、参考面偏移和参考轴端点。
- `set_global_variable` 属于 SolidWorks 方程式修改，带单位变量按原方程单位写字符串，不按 API 米制一律换算。
