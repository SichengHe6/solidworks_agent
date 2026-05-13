## 额外要求：为 v3 预留 agent-specific skills 机制

请在 `multi_agent_src_v3` 中为每个 agent 预留独立的 skills 文档和渐进式加载接口。注意，这一版不要求完整实现复杂 skill 进化，只要求把目录结构、数据结构、加载逻辑和调用接口设计好，方便后续扩展。

### 1. skills 总体设计原则

v3 中不再采用所有 agent 共享一个大知识库的方式，而是采用 **agent-specific skill bundle**：

```text
每个 agent 只访问自己职责范围内的 skills。
Planner / Requirement Agent 访问需求补充和协议生成 skills。
Part Agent 访问零件建模、标准件、参数化资产、失败修复 skills。
Assembly Agent 访问装配协议、约束关系、齿轮配合、运动学检查 skills。
Evaluator / Repair 逻辑访问失败分类和修复策略 skills。
```

请实现时遵守：

```text
1. skills 是 agent 的能力补充，不是全量 prompt。
2. 每个 agent 只加载和当前任务相关的 skill 文档。
3. 第一版可以用简单关键词 / 标签匹配，不需要向量数据库。
4. skills 文档必须允许后续人工扩展。
5. 后续可以加入 assets，例如参数化标准件模板、零件库、sidecar schema。
6. 当前 v3 先预留接口，不强制实现复杂自进化。
```

---

### 2. 推荐目录结构

请在 `multi_agent_src_v3` 下创建：

```text
multi_agent_src_v3/
  skills/
    requirement_agent/
      SKILL.md
      skill_index.json
      references/
        requirement_completion_rules.md
        part_vs_assembly_rules.md
        default_engineering_assumptions.md
        output_protocol_schema.md

    part_agent/
      SKILL.md
      skill_index.json
      references/
        part_modeling_workflow.md
        solidworks_part_api_rules.md
        static_validation_rules.md
        dynamic_execution_check_rules.md
        repair_policy.md
        sidecar_schema.md
      assets/
        standard_parts/
          README.md

    assembly_agent/
      SKILL.md
      skill_index.json
      references/
        assembly_modeling_workflow.md
        mate_constraints_rules.md
        repeated_instances_rules.md
        gear_pair_mate_protocol.md
        kinematic_sampling_rules.md
        assembly_repair_policy.md
      assets/
        assembly_templates/
          README.md

    evaluator/
      SKILL.md
      skill_index.json
      references/
        failure_taxonomy.md
        screenshot_check_rules.md
        execution_log_classification.md
        static_vs_dynamic_failure_rules.md

    shared/
      references/
        workspace_rules.md
        output_file_conventions.md
        path_safety_rules.md
```

如果目录不存在，请自动创建。

---

### 3. 每个 agent 的 SKILL.md 用途

每个 `SKILL.md` 是该 agent 的总说明，不要写成长文知识库。它只负责说明：

```text
该 agent 的职责边界
该 agent 可用的 skill 类型
什么时候加载 references
什么时候读取 assets
输出格式要求
失败反馈如何使用
```

例如 `part_agent/SKILL.md` 应包含：

```markdown
# Part Agent Skills

## Role

The part agent is responsible for turning a detailed part specification into executable SolidWorks Python code, validating consistency with the design intent, running the dynamic execution pipeline, and repairing either modeling strategy or code when validation fails.

## Skill Loading Policy

Load only the references relevant to the current part type, feature tags, failure type, or repair target.

## Core Responsibilities

1. Think through the modeling strategy before code generation.
2. Generate or locally repair Python code.
3. Perform static consistency validation against the part specification.
4. Run dynamic execution, screenshots, and result checks through the tool pipeline.
5. Decide whether a failure is caused by modeling strategy or code implementation.
6. Store the final modeling strategy and final code in the part output folder.

## Output Persistence

Always save:
- latest_modeling_plan.md
- latest_code.py
- validation_report.json
- execution_report.json
- repair_history.jsonl
```

---

### 4. skill_index.json 设计

每个 agent 目录下的 `skill_index.json` 用于二级渐进式披露。第一版使用标签匹配即可。

示例：`part_agent/skill_index.json`

```json
{
  "references": [
    {
      "id": "part_modeling_workflow",
      "path": "references/part_modeling_workflow.md",
      "tags": ["core", "part_modeling", "modeling_plan"]
    },
    {
      "id": "solidworks_part_api_rules",
      "path": "references/solidworks_part_api_rules.md",
      "tags": ["core", "solidworks_api", "code_generation"]
    },
    {
      "id": "static_validation_rules",
      "path": "references/static_validation_rules.md",
      "tags": ["validation", "static_check", "requirement_consistency"]
    },
    {
      "id": "dynamic_execution_check_rules",
      "path": "references/dynamic_execution_check_rules.md",
      "tags": ["execution", "screenshot", "dynamic_check"]
    },
    {
      "id": "repair_policy",
      "path": "references/repair_policy.md",
      "tags": ["repair", "failure", "local_edit"]
    },
    {
      "id": "sidecar_schema",
      "path": "references/sidecar_schema.md",
      "tags": ["sidecar", "metadata", "interfaces"]
    }
  ],
  "assets": [
    {
      "id": "standard_parts_placeholder",
      "path": "assets/standard_parts/README.md",
      "tags": ["standard_part", "asset_backed", "placeholder"]
    }
  ]
}
```

示例：`assembly_agent/skill_index.json`

```json
{
  "references": [
    {
      "id": "assembly_modeling_workflow",
      "path": "references/assembly_modeling_workflow.md",
      "tags": ["core", "assembly_modeling"]
    },
    {
      "id": "mate_constraints_rules",
      "path": "references/mate_constraints_rules.md",
      "tags": ["mate", "constraint", "coincident", "concentric", "parallel", "distance"]
    },
    {
      "id": "repeated_instances_rules",
      "path": "references/repeated_instances_rules.md",
      "tags": ["instances", "part_reuse", "repeated_parts"]
    },
    {
      "id": "gear_pair_mate_protocol",
      "path": "references/gear_pair_mate_protocol.md",
      "tags": ["gear", "gear_pair", "gear_mate", "tangent_mate", "pitch_circle"]
    },
    {
      "id": "kinematic_sampling_rules",
      "path": "references/kinematic_sampling_rules.md",
      "tags": ["kinematic", "motion", "sampling", "collision_check"]
    },
    {
      "id": "assembly_repair_policy",
      "path": "references/assembly_repair_policy.md",
      "tags": ["repair", "assembly_failure", "constraint_failure"]
    }
  ],
  "assets": [
    {
      "id": "assembly_templates_placeholder",
      "path": "assets/assembly_templates/README.md",
      "tags": ["assembly_template", "placeholder"]
    }
  ]
}
```

---

### 5. 新增 SkillManager

请新增一个模块：

```text
multi_agent_src_v3/skill_manager.py
```

实现一个轻量级 `SkillManager`。

接口建议：

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass
class LoadedSkillContext:
    agent_name: str
    selected_references: list[dict[str, Any]]
    selected_assets: list[dict[str, Any]]
    context_text: str

class SkillManager:
    def __init__(self, skills_root: Path):
        self.skills_root = skills_root

    def load_agent_skill_header(self, agent_name: str) -> str:
        """Load the agent-specific SKILL.md if it exists."""

    def load_relevant_context(
        self,
        agent_name: str,
        tags: list[str],
        max_references: int = 5,
        include_assets: bool = True,
    ) -> LoadedSkillContext:
        """
        Load only references/assets whose tags match the requested tags.
        Use simple tag overlap scoring in v3.
        """

    def list_agent_skills(self, agent_name: str) -> dict[str, Any]:
        """Return parsed skill_index.json for debugging."""
```

要求：

```text
1. 如果 SKILL.md 缺失，不报错，返回空字符串。
2. 如果 skill_index.json 缺失，不报错，返回空 context。
3. 读取 reference 文件时要限制最大字符数，避免 prompt 过长。
4. 不允许 SkillManager 写入 skills 目录。
5. assets 第一版只返回路径和元信息，不自动执行。
```

---

### 6. 各 agent 如何使用 skills

#### Agent1：需求补充 Agent

在需求补充阶段，加载：

```text
requirement_agent/SKILL.md
```

根据用户需求标签加载：

```text
part_vs_assembly_rules
default_engineering_assumptions
output_protocol_schema
```

Agent1 的输出必须是完整设计协议，不再反问用户。

Agent1 输出：

```text
如果是零件：
- detailed_requirement
- part_spec
- interfaces
- assumptions
- required_outputs

如果是装配体：
- detailed_requirement
- assembly_protocol
- unique_parts
- instances
- constraints
- interfaces
- assumptions
- required_outputs
```

#### Agent2：零件 Agent

零件 Agent 内部需要两阶段 prompt：

```text
阶段 A：建模思路生成 / 修复
阶段 B：代码生成 / 局部修改
```

每个零件开始时加载：

```text
part_agent/SKILL.md
```

然后根据标签加载 references：

```text
part_type
features
standard_part
asset_backed
failure_type
repair_target
```

零件输出子目录必须包含：

```text
part_output/
  modeling_plan/
    latest_modeling_plan.md
    modeling_plan_history.jsonl
  code/
    latest_code.py
    code_history.jsonl
  execution/
    screenshots/
    execution_report.json
    execution_log.txt
  validation/
    static_validation_report.json
    dynamic_validation_report.json
  repair/
    repair_history.jsonl
```

当静态校验或动态执行失败时，零件 Agent 必须判断失败属于：

```text
modeling_plan_error
code_implementation_error
asset_binding_error
unknown
```

如果是 `modeling_plan_error`，优先修改建模思路，再重新生成代码。

如果是 `code_implementation_error`，优先读取 `latest_code.py` 做局部修复，不要整段重写。

#### Agent3：装配 Agent

装配体流程只有在 `request_type == assembly` 时启动。

装配 Agent 使用：

```text
assembly_agent/SKILL.md
```

根据 constraints 和 assembly tags 加载：

```text
mate_constraints_rules
repeated_instances_rules
gear_pair_mate_protocol
kinematic_sampling_rules
assembly_repair_policy
```

装配输出目录必须包含：

```text
assembly_output/
  modeling_plan/
    latest_assembly_plan.md
    assembly_plan_history.jsonl
  code/
    latest_assembly_code.py
    assembly_code_history.jsonl
  execution/
    screenshots/
    execution_report.json
    execution_log.txt
  validation/
    static_validation_report.json
    dynamic_validation_report.json
  repair/
    repair_history.jsonl
```

装配失败时也要判断：

```text
assembly_plan_error
assembly_code_error
constraint_error
asset_interface_error
unknown
```

并优先局部修改对应文件。

---

### 7. 标准库 / assets 预留规则

请在 v3 中预留标准库调用机制，但第一版不要求实现所有标准件。

要求新增：

```text
asset_manager.py
```

接口建议：

```python
@dataclass
class MaterializedAsset:
    asset_id: str
    source_path: str
    working_copy_path: str
    sidecar_path: str | None
    source_hash: str | None

class AssetManager:
    def materialize_asset(
        self,
        asset_id: str,
        instance_id: str,
        workspace_root: Path,
    ) -> MaterializedAsset:
        """
        Copy a read-only asset/template into the current task workspace.
        Never modify the source asset directly.
        """
```

路径原则：

```text
skills/assets 或 standard_library 是只读源。
所有需要修改的标准件必须先复制到当前任务 workspace。
BuilderAgent 只能修改 workspace 下的 working copy。
禁止直接修改 skills/assets 或 standard_library 原件。
```

在工具层加入写路径保护：

```text
read_only_roots:
- skills/
- standard_library/
- knowledge_base/

writable_roots:
- 当前任务输出目录
```

任何写入 read_only_roots 的行为必须报错。

---

### 8. skills 与自进化的预留

v3 第一版不需要自动改写正式 skills，但要预留后续自进化接口。

请创建目录：

```text
skills/candidates/
```

后续失败和成功案例可以生成 skill candidate，但不能自动覆盖正式 skill。

预留文件结构：

```text
skills/candidates/
  README.md
```

README 中写明：

```text
This directory is reserved for future skill candidates generated from repeated success cases or resolved failures. Official skills must not be modified automatically by agents.
```

---

### 9. failure taxonomy 预留

请在：

```text
skills/evaluator/references/failure_taxonomy.md
```

预置基础失败类型：

```text
json_parse_error
requirement_completion_error
part_modeling_plan_error
part_code_implementation_error
asset_binding_error
static_validation_error
solidworks_execution_error
screenshot_error
geometry_feature_missing
geometry_topology_invalid
assembly_plan_error
assembly_code_error
constraint_error
asset_interface_error
kinematic_validation_error
unknown
```

Evaluator / Repair 逻辑要使用这些类型输出结构化报告。

---

### 10. 需要在 README 或架构说明中写清楚

请在 v3 的架构说明中补充：

```text
v3 的 skills 机制是 agent-specific progressive disclosure：
1. agent 路由完成第一层能力域选择；
2. 每个 agent 内部基于 tags 加载自己 skill bundle 中的 reference / asset；
3. 不全量加载知识库；
4. 不允许 agent 修改正式 skills；
5. 标准件 assets 必须 materialize 到 workspace 后再修改；
6. 后续 self-evolution 只生成 candidates，不直接污染正式 skill。
```
