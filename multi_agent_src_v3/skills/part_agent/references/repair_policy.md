# 零件修复策略

- `modeling_plan_error`：先更新 `latest_modeling_plan.md`，再重新生成代码。
- `code_implementation_error`：读取 `latest_code.py` 并执行局部修复。
- `asset_binding_error`：在工作区中物化或重新绑定资产。
- `unknown`：除非几何意图明显错误，否则优先尝试小范围代码修复。
