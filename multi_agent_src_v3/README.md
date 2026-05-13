# multi_agent_src_v3 Architecture

v3 refactors the v2 CAD pipeline into three primary agent stages:

1. Requirement Agent: completes the user request without asking follow-up questions. Missing dimensions, interfaces, materials, and coordinate assumptions are filled with conservative engineering defaults. Output is a detailed part spec or an assembly protocol.
2. Part Agent: runs per unique part in its own output folder. It generates a modeling plan, generates or locally repairs code, performs static requirement consistency validation, then runs the dynamic SolidWorks execution/screenshot/check pipeline.
3. Assembly Agent: runs only when `request_type == "assembly"`. It follows the same plan/code/static/dynamic/repair flow for the assembly.

Each unique part gets an isolated folder:

```text
parts/<part_id>/part_output/
  modeling_plan/latest_modeling_plan.md
  modeling_plan/modeling_plan_history.jsonl
  code/latest_code.py
  code/code_history.jsonl
  execution/screenshots/
  execution/execution_report.json
  execution/execution_log.txt
  validation/static_validation_report.json
  validation/dynamic_validation_report.json
  repair/repair_history.jsonl
```

Assembly output uses the same convention under `assembly_output/`.

## Skills

v3 uses agent-specific progressive disclosure:

1. Agent routing completes the first-level capability-domain choice.
2. Each agent loads references/assets from its own skill bundle by tags.
3. The pipeline does not load the whole knowledge base into every agent.
4. Agents must not modify official skills.
5. Standard-part assets must be materialized into the task workspace before modification.
6. Future self-evolution may generate files under `skills/candidates/`, but must not overwrite official skills automatically.

`skill_manager.py` provides the lightweight tag loader. `asset_manager.py` reserves the read-only asset materialization interface.
