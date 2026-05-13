# 重复实例规则

- 相同几何只建模一次，然后多次插入。
- `part_id -> model_file` 和 `instance_id -> component_name` 应保持为两套独立映射。
- 实例专属接口使用方式写入 `instances[].interface_usage`。
