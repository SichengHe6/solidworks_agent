from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from .agents import (
        AssemblyAgent,
        AssemblyPlanningAgent,
        PartModelingAgent,
        PartValidationAgent,
        RequirementAgent,
        extract_json_payload,
        extract_python_code,
    )
    from .config import AGENT_OUTPUT_ROOT
    from .executor import (
        execute_python_code,
        run_assembly_plan_checks,
        run_part_plan_checks,
    )
except ImportError:
    from agents import (
        AssemblyAgent,
        AssemblyPlanningAgent,
        PartModelingAgent,
        PartValidationAgent,
        RequirementAgent,
        extract_json_payload,
        extract_python_code,
    )
    from config import AGENT_OUTPUT_ROOT
    from executor import execute_python_code, run_assembly_plan_checks, run_part_plan_checks


def slugify(value: str, fallback: str) -> str:
    value = value.strip()
    value = re.sub(r"[^\w\-]+", "_", value, flags=re.UNICODE)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or fallback


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class MultiAgentOrchestrator:
    def __init__(self) -> None:
        self.requirement_agent = RequirementAgent()
        self.assembly_planning_agent = AssemblyPlanningAgent()
        self.assembly_agent = AssemblyAgent()

    def run(self) -> None:
        print("=== 多智能体 CAD 设计系统 ===")
        requirement_payload = self.collect_requirements()
        request_type = str(requirement_payload.get("request_type", "")).strip().lower()

        if request_type == "part":
            self.handle_part_request(requirement_payload)
            return

        if request_type == "assembly":
            self.handle_assembly_request(requirement_payload)
            return

        raise ValueError(f"Unsupported request_type: {request_type}")

    def collect_requirements(self) -> dict[str, Any]:
        print("\n[阶段 1] 需求分析（输入 'quit' 退出）")
        user_input = input("请输入您的设计需求：\n>> ").strip()

        while True:
            if user_input.lower() in {"quit", "exit"}:
                raise SystemExit(0)

            reply = self.requirement_agent.chat(user_input)
            print(f"\n[需求分析 Agent]\n{reply}\n")

            if "[CONFIRMED]" in reply:
                payload = extract_json_payload(reply)
                print(f">>> 已确认需求类型: {payload.get('request_type')}")
                return payload

            user_input = input(">> ").strip()

    def handle_part_request(self, requirement_payload: dict[str, Any]) -> None:
        workspace = self.create_single_part_workspace(requirement_payload)
        plan = self.build_single_part_plan(requirement_payload, workspace)
        write_json(Path(plan["workspace"]["plan_file"]), plan)

        print("\n[阶段 2] 单零件建模")
        success = self.run_part_pipeline(
            full_plan=plan,
            part_spec=plan["part"],
            enable_static_validation=False,
        )
        if success:
            print("\n=== 单零件需求执行完成 ===")
        else:
            print("\n=== 单零件需求执行失败，请根据日志调整需求或知识库 ===")

    def handle_assembly_request(self, requirement_payload: dict[str, Any]) -> None:
        workspace = self.create_assembly_workspace(requirement_payload)
        print("\n[阶段 2] 装配规划")
        plan = self.generate_assembly_plan(requirement_payload, workspace)

        print("\n[阶段 3] 零件建模分发")
        part_results: list[dict[str, Any]] = []
        for index, part_spec in enumerate(plan["assembly"]["parts"], start=1):
            print(f"\n  -> 零件 {index}/{len(plan['assembly']['parts'])}: {part_spec['name']}")
            success = self.run_part_pipeline(
                full_plan=plan,
                part_spec=part_spec,
                enable_static_validation=True,
            )
            part_results.append(
                {
                    "part_id": part_spec["part_id"],
                    "name": part_spec["name"],
                    "success": success,
                    "model_file": part_spec["workspace"]["model_file"],
                }
            )
            if not success:
                print("\n=== 零件建模未全部完成，停止装配阶段 ===")
                return

        print("\n[阶段 4] 装配生成与执行")
        assembly_success = self.run_assembly_pipeline(plan, part_results)
        if assembly_success:
            print("\n=== 装配需求执行完成 ===")
        else:
            print("\n=== 装配阶段失败，请查看输出目录日志 ===")

    def create_single_part_workspace(self, requirement_payload: dict[str, Any]) -> dict[str, str]:
        name = slugify(requirement_payload.get("name", "part"), "part")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        root_dir = AGENT_OUTPUT_ROOT / f"{name}-{timestamp}"
        part_dir = root_dir / "part"
        json_dir = root_dir / "json"
        logs_dir = root_dir / "logs"

        for directory in (root_dir, part_dir, json_dir, logs_dir):
            directory.mkdir(parents=True, exist_ok=True)

        return {
            "root_dir": str(root_dir),
            "part_dir": str(part_dir),
            "json_dir": str(json_dir),
            "logs_dir": str(logs_dir),
        }

    def build_single_part_plan(
        self,
        requirement_payload: dict[str, Any],
        workspace: dict[str, str],
    ) -> dict[str, Any]:
        part_id = slugify(requirement_payload.get("name", "part"), "part")
        part_name = requirement_payload.get("name", "Part")
        part_dir = Path(workspace["part_dir"])
        plan = {
            "request_type": "part",
            "name": part_name,
            "summary": requirement_payload.get("summary", ""),
            "key_requirements": requirement_payload.get("key_requirements", []),
            "assumptions": requirement_payload.get("assumptions", []),
            "requested_outputs": requirement_payload.get("requested_outputs", []),
            "interfaces": requirement_payload.get("interfaces", []),
            "workspace": {
                **workspace,
                "plan_file": str(Path(workspace["json_dir"]) / "part_request.json"),
            },
            "part": {
                "part_id": part_id,
                "name": part_name,
                "function": requirement_payload.get("summary", ""),
                "shape": "根据需求分析结果由建模智能体细化",
                "key_dimensions": requirement_payload.get("key_requirements", []),
                "material_or_notes": "; ".join(requirement_payload.get("assumptions", [])),
                "interfaces": {
                    "faces": [],
                    "axes": [],
                    "points": [],
                },
                "standalone_modeling_instructions": requirement_payload.get("key_requirements", []),
                "workspace": {
                    "part_dir": str(part_dir),
                    "code_file": str(part_dir / f"{part_id}_model.py"),
                    "model_file": str(part_dir / f"{part_id}.SLDPRT"),
                    "log_file": str(Path(workspace["logs_dir"]) / f"{part_id}_model.log"),
                    "spec_file": str(Path(workspace["json_dir"]) / f"{part_id}_spec.json"),
                },
            },
        }
        write_json(
            Path(plan["part"]["workspace"]["spec_file"]),
            {
                "request_type": "part",
                "part_context": {
                    "name": plan["name"],
                    "summary": plan["summary"],
                    "key_requirements": plan["key_requirements"],
                    "assumptions": plan["assumptions"],
                    "requested_outputs": plan["requested_outputs"],
                    "interfaces": plan["interfaces"],
                },
                "part": plan["part"],
            },
        )
        return plan

    def create_assembly_workspace(self, requirement_payload: dict[str, Any]) -> dict[str, str]:
        assembly_name = slugify(requirement_payload.get("name", "assembly"), "assembly")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        root_dir = AGENT_OUTPUT_ROOT / f"{assembly_name}-{timestamp}"
        parts_dir = root_dir / "parts"
        assembly_dir = root_dir / "assembly"
        json_dir = root_dir / "json"
        logs_dir = root_dir / "logs"

        for directory in (root_dir, parts_dir, assembly_dir, json_dir, logs_dir):
            directory.mkdir(parents=True, exist_ok=True)

        return {
            "root_dir": str(root_dir),
            "parts_dir": str(parts_dir),
            "assembly_dir": str(assembly_dir),
            "json_dir": str(json_dir),
            "logs_dir": str(logs_dir),
        }

    def generate_assembly_plan(
        self,
        requirement_payload: dict[str, Any],
        workspace: dict[str, str],
    ) -> dict[str, Any]:
        prompt = json.dumps(
            {
                "confirmed_requirement": requirement_payload,
                "precreated_workspace": {
                    **workspace,
                    "plan_file": str(Path(workspace["json_dir"]) / "assembly_plan.json"),
                    "assembly_output": {
                        "code_file": str(Path(workspace["assembly_dir"]) / "assembly_build.py"),
                        "model_file": str(
                            Path(workspace["assembly_dir"])
                            / f"{slugify(requirement_payload.get('name', 'assembly'), 'assembly')}.SLDASM"
                        ),
                        "log_file": str(Path(workspace["logs_dir"]) / "assembly.log"),
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
        )

        response = self.assembly_planning_agent.chat(prompt)
        plan = extract_json_payload(response)
        plan = self.enrich_assembly_plan(plan, workspace)
        write_json(Path(plan["assembly"]["workspace"]["plan_file"]), plan)
        return plan

    def enrich_assembly_plan(self, plan: dict[str, Any], workspace: dict[str, str]) -> dict[str, Any]:
        if plan.get("request_type") != "assembly":
            raise ValueError("AssemblyPlanningAgent returned a non-assembly plan.")

        assembly = plan.setdefault("assembly", {})
        assembly_name = slugify(assembly.get("name", "assembly"), "assembly")
        assembly_workspace = {
            **workspace,
            "plan_file": str(Path(workspace["json_dir"]) / "assembly_plan.json"),
        }
        assembly["workspace"] = assembly_workspace
        assembly.setdefault("summary", "")
        assembly.setdefault("global_coordinate_system", {})
        assembly.setdefault("design_rules", [])
        assembly.setdefault("assembly_sequence", [])
        assembly.setdefault("constraints", [])
        assembly["assembly_output"] = {
            "code_file": str(Path(workspace["assembly_dir"]) / "assembly_build.py"),
            "model_file": str(Path(workspace["assembly_dir"]) / f"{assembly_name}.SLDASM"),
            "log_file": str(Path(workspace["logs_dir"]) / "assembly.log"),
        }

        part_specs = assembly.get("parts", [])
        for part in part_specs:
            part_id = slugify(part.get("part_id") or part.get("name", "part"), "part")
            part_name = part.get("name", part_id)
            part_dir = Path(workspace["parts_dir"]) / part_id
            part_dir.mkdir(parents=True, exist_ok=True)

            part_workspace = {
                "part_dir": str(part_dir),
                "code_file": str(part_dir / f"{part_id}_model.py"),
                "model_file": str(part_dir / f"{part_id}.SLDPRT"),
                "log_file": str(Path(workspace["logs_dir"]) / f"{part_id}_model.log"),
                "spec_file": str(Path(workspace["json_dir"]) / f"{part_id}_spec.json"),
            }
            part["part_id"] = part_id
            part["name"] = part_name
            part["workspace"] = part_workspace
            part["interfaces"] = part.get("interfaces", {"faces": [], "axes": [], "points": []})
            part["standalone_modeling_instructions"] = part.get("standalone_modeling_instructions", [])
            write_json(
                Path(part_workspace["spec_file"]),
                {
                    "request_type": "assembly_part",
                    "assembly_context": {
                        "name": assembly.get("name", ""),
                        "summary": assembly.get("summary", ""),
                        "global_coordinate_system": assembly.get("global_coordinate_system", {}),
                        "design_rules": assembly.get("design_rules", []),
                        "assembly_sequence": assembly.get("assembly_sequence", []),
                    },
                    "part": part,
                },
            )

        return plan

    def run_part_pipeline(
        self,
        full_plan: dict[str, Any],
        part_spec: dict[str, Any],
        enable_static_validation: bool,
        max_retries: int = 3,
    ) -> bool:
        part_agent = PartModelingAgent()
        validation_agent = PartValidationAgent() if enable_static_validation else None

        current_prompt = self.build_part_prompt(full_plan, part_spec, None)
        for attempt in range(1, max_retries + 1):
            print(f"    [建模尝试 {attempt}/{max_retries}] 生成 {part_spec['name']} 代码")
            response = part_agent.chat(current_prompt)
            code = extract_python_code(response)

            workdir = Path(part_spec["workspace"]["part_dir"])
            script_name = Path(part_spec["workspace"]["code_file"]).name
            execution = execute_python_code(code, workdir=workdir, script_name=script_name)
            write_text(Path(part_spec["workspace"]["log_file"]), execution.log)

            if not execution.success:
                summary = execution.log.splitlines()[-1] if execution.log.splitlines() else execution.log
                print(f"    [执行失败] {summary}")
                current_prompt = self.build_part_prompt(full_plan, part_spec, execution.log)
                continue

            print("    [执行成功] 开始静态校验" if enable_static_validation else "    [执行成功] 动态校验通过")
            if not enable_static_validation:
                return True

            deterministic_issues = run_part_plan_checks(full_plan, part_spec, code)
            validator_feedback = self.validate_part_code(
                validation_agent=validation_agent,
                full_plan=full_plan,
                part_spec=part_spec,
                code=code,
                deterministic_issues=deterministic_issues,
            )
            if validator_feedback["pass"]:
                print("    [静态校验通过]")
                return True

            feedback = validator_feedback.get("feedback", "静态校验未通过")
            print(f"    [静态校验失败] {feedback}")
            current_prompt = self.build_part_prompt(full_plan, part_spec, feedback)

        return False

    def validate_part_code(
        self,
        validation_agent: PartValidationAgent | None,
        full_plan: dict[str, Any],
        part_spec: dict[str, Any],
        code: str,
        deterministic_issues: list[str],
    ) -> dict[str, Any]:
        if validation_agent is None:
            return {"pass": not deterministic_issues, "feedback": "; ".join(deterministic_issues)}

        prompt = json.dumps(
            {
                "full_plan": full_plan,
                "part_spec": part_spec,
                "generated_code": code,
                "deterministic_issues": deterministic_issues,
            },
            ensure_ascii=False,
            indent=2,
        )

        response = validation_agent.chat(prompt)
        try:
            validation = extract_json_payload(response)
        except ValueError:
            validation = {
                "pass": False,
                "feedback": "静态校验 agent 未返回可解析 JSON，请重新生成并明确路径、接口和方向关系。",
            }

        if deterministic_issues:
            merged_feedback = validation.get("feedback", "")
            validation["pass"] = False
            validation["feedback"] = "; ".join([*deterministic_issues, merged_feedback]).strip("; ")
        return validation

    def build_part_prompt(
        self,
        full_plan: dict[str, Any],
        part_spec: dict[str, Any],
        retry_feedback: str | None,
    ) -> str:
        payload = {
            "task": "请为下面的零件生成完整可执行 Python 建模代码。",
            "full_plan_summary": full_plan,
            "part_spec": part_spec,
        }
        if retry_feedback:
            payload["retry_feedback"] = retry_feedback
            payload["instruction"] = "请基于反馈完整重写代码，不要只给差异片段。"
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def run_assembly_pipeline(
        self,
        plan: dict[str, Any],
        part_results: list[dict[str, Any]],
        max_retries: int = 3,
    ) -> bool:
        current_prompt = self.build_assembly_prompt(plan, part_results, None)
        assembly_output = plan["assembly"]["assembly_output"]

        for attempt in range(1, max_retries + 1):
            print(f"  [装配尝试 {attempt}/{max_retries}] 生成装配代码")
            response = self.assembly_agent.chat(current_prompt)
            code = extract_python_code(response)

            workdir = Path(plan["assembly"]["workspace"]["assembly_dir"])
            script_name = Path(assembly_output["code_file"]).name
            execution = execute_python_code(code, workdir=workdir, script_name=script_name)
            write_text(Path(assembly_output["log_file"]), execution.log)

            if not execution.success:
                summary = execution.log.splitlines()[-1] if execution.log.splitlines() else execution.log
                print(f"  [装配执行失败] {summary}")
                current_prompt = self.build_assembly_prompt(plan, part_results, execution.log)
                continue

            issues = run_assembly_plan_checks(plan, code)
            if not issues:
                print("  [装配执行成功]")
                return True

            feedback = "; ".join(issues)
            print(f"  [装配静态检查失败] {feedback}")
            current_prompt = self.build_assembly_prompt(plan, part_results, feedback)

        return False

    def build_assembly_prompt(
        self,
        plan: dict[str, Any],
        part_results: list[dict[str, Any]],
        retry_feedback: str | None,
    ) -> str:
        payload = {
            "task": "请根据装配规划和已完成的零件输出，生成完整可执行 Python 装配代码。",
            "assembly_plan": plan,
            "part_results": part_results,
        }
        if retry_feedback:
            payload["retry_feedback"] = retry_feedback
            payload["instruction"] = "请基于反馈完整重写装配代码，不要只给差异片段。"
        return json.dumps(payload, ensure_ascii=False, indent=2)
