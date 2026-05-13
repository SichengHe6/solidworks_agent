from __future__ import annotations

import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Callable
from typing import Any
from uuid import uuid4

try:
    from .agent_tools import AgentToolExecutor
    from .agents import (
        AssemblyAgent,
        AssemblyPlanningAgent,
        AssemblyPlanReviewAgent,
        PartModelingAgent,
        PartValidationAgent,
        RequirementAgent,
        RequirementReviewAgent,
        extract_json_payload,
        extract_python_code,
    )
    from .config import AGENT_OUTPUT_ROOT, KNOWLEDGE_BASE_ROOT, SKILLS_ROOT, STANDARD_LIBRARY_ROOT
    from .executor import (
        run_assembly_plan_checks,
        run_part_plan_checks,
    )
    from .pipeline_state import DEFAULT_STATE_POLICIES, PipelineState, StatePolicy
    from .skill_manager import SkillManager
except ImportError:
    from agent_tools import AgentToolExecutor
    from agents import (
        AssemblyAgent,
        AssemblyPlanningAgent,
        AssemblyPlanReviewAgent,
        PartModelingAgent,
        PartValidationAgent,
        RequirementAgent,
        RequirementReviewAgent,
        extract_json_payload,
        extract_python_code,
    )
    from config import AGENT_OUTPUT_ROOT, KNOWLEDGE_BASE_ROOT, SKILLS_ROOT, STANDARD_LIBRARY_ROOT
    from executor import run_assembly_plan_checks, run_part_plan_checks
    from pipeline_state import DEFAULT_STATE_POLICIES, PipelineState, StatePolicy
    from skill_manager import SkillManager


PART_PARALLELISM_LIMIT = 8


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


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(payload, ensure_ascii=False) + "\n")


class MultiAgentOrchestrator:
    def __init__(self, event_callback: Callable[[dict[str, Any]], None] | None = None) -> None:
        self.requirement_agent = RequirementAgent()
        self.requirement_review_agent = RequirementReviewAgent()
        self.assembly_planning_agent = AssemblyPlanningAgent()
        self.assembly_plan_review_agent = AssemblyPlanReviewAgent()
        self.assembly_agent = AssemblyAgent()
        self.event_callback = event_callback
        self.state_policies: dict[PipelineState, StatePolicy] = DEFAULT_STATE_POLICIES
        self.current_state = PipelineState.REQUIREMENT_CLARIFYING
        self.state_lock = threading.Lock()
        self.previous_attempts: dict[str, list[dict[str, Any]]] = {}
        self.previous_attempts_lock = threading.Lock()
        self.part_parallelism_limit = PART_PARALLELISM_LIMIT
        self.last_run_context: dict[str, Any] | None = None
        self.review_history: list[dict[str, Any]] = []
        self.skill_manager = SkillManager(SKILLS_ROOT)

    def emit_event(self, event_type: str, **payload: Any) -> None:
        if self.event_callback is None:
            return
        event = {"type": event_type, **payload}
        self.event_callback(event)

    def emit_status(self, message: str) -> None:
        self.emit_event("status", message=message)

    def set_state(self, state: PipelineState, **context: Any) -> None:
        with self.state_lock:
            self.current_state = state
        policy = self.state_policies[state]
        self.emit_event(
            "state",
            state=state.value,
            inputs=list(policy.inputs),
            success_state=policy.success_state.value,
            failure_state=policy.failure_state.value,
            max_retries=policy.max_retries,
            fallback_state=policy.fallback_state.value if policy.fallback_state else None,
            context=context,
        )
        self.emit_status(f"[STATE] {state.value}")

    def run_agent(self, agent_name: str, agent: Any, prompt: str) -> str:
        if self.event_callback is None:
            return agent.chat(prompt)

        message_id = uuid4().hex
        self.emit_event("message_start", role="agent", agent_name=agent_name, message_id=message_id)
        for chunk in agent.stream_chat(prompt):
            self.emit_event("delta", content=chunk, message_id=message_id)
        self.emit_event("message_end", message_id=message_id)
        return agent.history[-1]["content"]

    def run_agent_with_tools(
        self,
        agent_name: str,
        agent: Any,
        prompt: str,
        tool_executor: AgentToolExecutor,
        max_tool_steps: int = 8,
    ) -> str:
        current_prompt = prompt
        latest_response = ""

        for step in range(1, max_tool_steps + 1):
            latest_response = self.run_agent(agent_name, agent, current_prompt)
            action = self.extract_tool_action(latest_response)
            if action is None:
                return latest_response

            tool_name = str(action.get("tool", ""))
            self.emit_status(f"[TOOL {step}/{max_tool_steps}] {agent_name} -> {tool_name}")
            result = tool_executor.execute(action)
            agent.remember(f"{tool_name}: {'ok' if result.success else 'failed'} - {result.content[:500]}")
            current_prompt = json.dumps(
                {
                    "tool_result": result.to_payload(),
                    "instruction": (
                        "Use the tool result to continue. If more context is needed, output the next "
                        "JSON tool action. If the file is ready, either call write_file with the final "
                        "complete content or return the final Python code."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )

        return latest_response

    def extract_tool_action(self, response: str) -> dict[str, Any] | None:
        try:
            payload = extract_json_payload(response)
        except ValueError:
            return None

        action = payload.get("next_action") if isinstance(payload, dict) else None
        if not isinstance(action, dict):
            return None
        if not action.get("tool"):
            return None
        if not isinstance(action.get("args", {}), dict):
            action["args"] = {}
        return action

    def make_tool_executor(self, workspace_root: str | Path) -> AgentToolExecutor:
        root = Path(workspace_root)
        return AgentToolExecutor(
            workspace_roots=[root],
            knowledge_base_root=KNOWLEDGE_BASE_ROOT,
            read_only_roots=[KNOWLEDGE_BASE_ROOT, SKILLS_ROOT, STANDARD_LIBRARY_ROOT],
            previous_attempts=self.previous_attempts,
            event_callback=self.event_callback,
        )

    def run(self) -> None:
        print("=== 多智能体 CAD 设计系统 v3 ===")
        requirement_payload = self.collect_requirements()
        self.process_confirmed_requirement(requirement_payload)

    def process_confirmed_requirement(self, requirement_payload: dict[str, Any]) -> None:
        request_type = str(requirement_payload.get("request_type", "")).strip().lower()

        if request_type == "part":
            self.run_part_state_machine(requirement_payload)
            return

        if request_type == "assembly":
            self.run_assembly_state_machine(requirement_payload)
            return

        raise ValueError(f"Unsupported request_type: {request_type}")

    def can_handle_followup_modification(self, user_message: str) -> bool:
        if not self.last_run_context or self.last_run_context.get("request_type") != "part":
            return False
        text = user_message.strip().lower()
        modification_markers = [
            "修改",
            "调整",
            "改",
            "加",
            "增加",
            "减少",
            "缩小",
            "放大",
            "变",
            "优化",
            "倒角",
            "圆角",
            "孔",
            "厚度",
            "长度",
            "宽度",
            "高度",
            "move",
            "modify",
            "change",
            "adjust",
            "add",
            "remove",
            "larger",
            "smaller",
        ]
        new_design_markers = ["新建", "重新设计一个", "另做", "新的零件", "new part", "new assembly"]
        return any(marker in text for marker in modification_markers) and not any(
            marker in text for marker in new_design_markers
        )

    def process_followup_modification(self, user_message: str) -> bool:
        if not self.last_run_context or self.last_run_context.get("request_type") != "part":
            return False
        plan = self.last_run_context.get("plan")
        part_spec = self.last_run_context.get("part_spec")
        if not isinstance(plan, dict) or not isinstance(part_spec, dict):
            return False

        self.emit_status("[小幅修改] 复用当前零件工作目录，直接进入零件修改智能体")
        part_spec.setdefault("standalone_modeling_instructions", [])
        part_spec["standalone_modeling_instructions"] = [
            *list(part_spec.get("standalone_modeling_instructions") or []),
            *self.recent_review_comments(),
            f"Follow-up modification request: {user_message}",
        ]
        review_context = "\n".join(f"- {comment}" for comment in self.recent_review_comments())
        success = self.run_part_pipeline(
            full_plan=plan,
            part_spec=part_spec,
            enable_static_validation=True,
            initial_feedback=(
                f"User follow-up modification request: {user_message}\n"
                f"Recent review comments to preserve:\n{review_context or '(none)'}"
            ),
        )
        self.last_run_context = {
            "request_type": "part",
            "plan": plan,
            "part_spec": part_spec,
            "success": success,
        }
        self.write_review_history(plan.get("workspace"))
        self.set_state(PipelineState.DONE if success else PipelineState.FAILED_FATAL, request_type="part_modification")
        return True

    def review_requirement_payload(self, requirement_payload: dict[str, Any]) -> dict[str, Any]:
        prompt = json.dumps(
            {
                "requirement_payload": requirement_payload,
                "recent_review_history": self.review_history[-5:],
                "review_goal": "Soft-check CAD feasibility and prepare downstream comments. Only severity=fatal should block generation.",
                "severity_policy": {
                    "ok": "No meaningful issue; continue.",
                    "warning": "Issue can be solved by a reasonable engineering assumption or local dimension adjustment; continue and pass comments downstream.",
                    "fatal": "Issue cannot be solved without asking the user because it contradicts the design intent or makes modeling impossible.",
                },
                "interpretation_rules": [
                    "Treat bolt/hole radius as the radius of the hole itself, not the polar placement radius, unless the text explicitly says placement/distribution radius.",
                    "If a dimension conflict can be resolved by preserving semantic intent, provide a concrete correction in comments_for_next_agent and use severity=warning.",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        response = self.run_agent("RequirementReviewAgent", self.requirement_review_agent, prompt)
        try:
            review = extract_json_payload(response)
        except ValueError:
            review = {
                "pass": False,
                "severity": "warning",
                "feedback": "Requirement review did not return parseable JSON.",
                "comments_for_next_agent": [],
            }
        severity = str(review.get("severity") or ("ok" if review.get("pass") else "warning")).lower()
        if severity not in {"ok", "warning", "fatal"}:
            severity = "warning"
        review["severity"] = severity
        if severity in {"ok", "warning"}:
            review["pass"] = True
        comments = review.get("comments_for_next_agent", [])
        if comments:
            requirement_payload.setdefault("review_comments", comments)
        self.record_review("requirement", review, {"request_type": requirement_payload.get("request_type")})
        return review

    def review_assembly_plan_payload(self, plan: dict[str, Any]) -> dict[str, Any]:
        prompt = json.dumps(
            {
                "assembly_plan": plan,
                "recent_review_history": self.review_history[-5:],
                "review_goal": "Soft-review the assembly protocol before part modeling. Prefer pass=true with actionable comments.",
                "severity_policy": {
                    "ok": "No meaningful issue; continue.",
                    "warning": "Issue can be solved by comments, reasonable defaults, or local planning adjustment; continue and store comments in assembly.review_comments.",
                    "fatal": "Only use when current SolidWorks constraints cannot express the plan or the part/instance relation is irreconcilable.",
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        response = self.run_agent("AssemblyPlanReviewAgent", self.assembly_plan_review_agent, prompt)
        try:
            review = extract_json_payload(response)
        except ValueError:
            review = {
                "pass": True,
                "severity": "warning",
                "feedback": "Assembly plan review did not return parseable JSON.",
                "comments_for_next_agent": [],
            }
        severity = str(review.get("severity") or ("ok" if review.get("pass") else "warning")).lower()
        if severity not in {"ok", "warning", "fatal"}:
            severity = "warning"
        review["severity"] = severity
        if severity in {"ok", "warning"}:
            review["pass"] = True
        comments = review.get("comments_for_next_agent", [])
        if comments:
            plan.setdefault("assembly", {}).setdefault("review_comments", comments)
        self.record_review("assembly_plan", review, {"name": plan.get("assembly", {}).get("name")})
        return review

    def record_review(self, scope: str, review: dict[str, Any], context: dict[str, Any] | None = None) -> None:
        entry = {
            "scope": scope,
            "context": context or {},
            "review": review,
            "comments_for_next_agent": list(review.get("comments_for_next_agent", []) or []),
        }
        self.review_history.append(entry)
        self.review_history = self.review_history[-20:]

    def write_review_history(self, workspace: dict[str, str] | None) -> None:
        if not workspace:
            return
        json_dir = workspace.get("json_dir")
        if not json_dir:
            return
        write_json(Path(json_dir) / "reviews.json", {"reviews": self.review_history})

    def recent_review_comments(self) -> list[str]:
        comments: list[str] = []
        for entry in self.review_history[-8:]:
            comments.extend(entry.get("comments_for_next_agent", []) or [])
        return comments[-20:]

    def normalize_requirement_payload(self, payload: dict[str, Any], raw_user_input: str = "") -> dict[str, Any]:
        request_type = str(payload.get("request_type", "")).strip().lower()
        if request_type not in {"part", "assembly"}:
            text = json.dumps(payload, ensure_ascii=False) + raw_user_input
            assembly_markers = ("装配", "配合", "约束", "多个零件", "assembly", "mate", "constraint")
            request_type = "assembly" if any(marker in text.lower() for marker in assembly_markers) else "part"
        payload["request_type"] = request_type
        payload.setdefault("name", "assembly" if request_type == "assembly" else "part")
        payload.setdefault("summary", payload.get("detailed_requirement") or raw_user_input)
        payload.setdefault("detailed_requirement", payload.get("summary") or raw_user_input)
        payload.setdefault("assumptions", [])
        payload.setdefault("interfaces", [])
        payload.setdefault("required_outputs", payload.get("requested_outputs", ["SolidWorks model", "Python code"]))
        payload.setdefault("requested_outputs", payload.get("required_outputs", []))
        if request_type == "part" and isinstance(payload.get("part_spec"), dict):
            payload["part_spec"]["interfaces"] = self.normalize_interface_schema(
                payload["part_spec"].get("interfaces", {})
            )
        if request_type == "assembly":
            for part in payload.get("unique_parts", []) or []:
                if isinstance(part, dict):
                    part["interfaces"] = self.normalize_interface_schema(part.get("interfaces", {}))
        return payload

    def normalize_interface_schema(self, interfaces: Any) -> dict[str, list[dict[str, str]]]:
        normalized = {"faces": [], "axes": [], "points": []}
        if isinstance(interfaces, dict):
            for category in ("faces", "axes", "points"):
                normalized[category] = [
                    self.normalize_interface_item(item, category)
                    for item in (interfaces.get(category, []) or [])
                ]
            return normalized
        if isinstance(interfaces, list):
            for item in interfaces:
                text = str(item)
                lowered = text.lower()
                if "axis" in lowered or "轴" in text:
                    category = "axes"
                elif "point" in lowered or "点" in text:
                    category = "points"
                else:
                    category = "faces"
                normalized[category].append(self.normalize_interface_item(item, category))
        return normalized

    def normalize_interface_item(self, item: Any, category: str) -> dict[str, str]:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            purpose = str(item.get("purpose") or item.get("description") or "").strip()
            direction = str(
                item.get("normal_direction_relation")
                or item.get("direction_relation")
                or item.get("location_hint")
                or ""
            ).strip()
        else:
            text = str(item).strip()
            if ":" in text:
                name, purpose = [part.strip() for part in text.split(":", 1)]
            else:
                name, purpose = text, ""
            direction = ""
        if category == "faces":
            return {"name": name, "purpose": purpose, "normal_direction_relation": direction}
        if category == "axes":
            return {"name": name, "purpose": purpose, "direction_relation": direction}
        return {"name": name, "purpose": purpose, "location_hint": direction}

    def collect_requirements(self) -> dict[str, Any]:
        print("\n[阶段 1] 需求补全（输入 'quit' 退出）")
        user_input = input("请输入您的设计需求：\n>> ").strip()

        if user_input.lower() in {"quit", "exit"}:
            raise SystemExit(0)

        current_prompt = (
            "请直接补全下面的用户需求，输出 [CONFIRMED] 和严格 JSON。"
            "不要反问用户；缺失信息用工程假设补足。\n\n"
            f"用户需求：{user_input}"
        )
        for attempt in range(1, 4):
            reply = self.run_agent("RequirementAgent", self.requirement_agent, current_prompt)
            print(f"\n[需求补全 Agent]\n{reply}\n")
            try:
                payload = extract_json_payload(reply)
            except ValueError as exc:
                print(f"[需求补全解析失败] {exc}")
                self.emit_status(f"[需求补全解析失败] {exc}")
                current_prompt = (
                    "上一次需求补全没有返回可解析 JSON。请基于同一个用户需求重新输出 [CONFIRMED] "
                    "和一个严格 JSON 代码块，不要反问用户。\n"
                    f"解析错误：{exc}\n原始用户需求：{user_input}\n上次输出：{reply}"
                )
                continue
            payload = self.normalize_requirement_payload(payload, raw_user_input=user_input)
            print(f">>> 已补全需求类型: {payload.get('request_type')}")
            return payload

        raise ValueError("RequirementAgent failed to return a valid completed requirement JSON after retries.")

    def handle_part_request(self, requirement_payload: dict[str, Any]) -> None:
        self.run_part_state_machine(requirement_payload)

    def run_part_state_machine(self, requirement_payload: dict[str, Any]) -> None:
        self.set_state(PipelineState.REQUIREMENT_CLARIFYING, request_type="part")
        self.set_state(PipelineState.PLAN_GENERATING, request_type="part")
        review = self.review_requirement_payload(requirement_payload)
        self.emit_event("review_result", scope="requirement", **review)
        if review.get("severity") == "fatal":
            self.set_state(PipelineState.FAILED_RECOVERABLE, request_type="part", review=review)
            raise ValueError(f"Part requirement review failed: {review.get('feedback')}")
        workspace = self.create_single_part_workspace(requirement_payload)
        plan = self.build_single_part_plan(requirement_payload, workspace)
        write_json(Path(plan["workspace"]["plan_file"]), plan)
        self.write_review_history(plan["workspace"])

        print("\n[阶段 2] 单零件建模")
        self.emit_status("[阶段 2] 单零件建模")
        self.set_state(PipelineState.PART_MODELING, part_id=plan["part"]["part_id"])
        success = self.run_part_pipeline(
            full_plan=plan,
            part_spec=plan["part"],
            enable_static_validation=True,
        )
        self.last_run_context = {
            "request_type": "part",
            "plan": plan,
            "part_spec": plan["part"],
            "success": success,
        }
        self.write_review_history(plan["workspace"])
        if success:
            self.set_state(PipelineState.DONE, request_type="part")
            print("\n=== 单零件需求执行完成 ===")
        else:
            print("\n=== 单零件需求执行失败，请根据日志调整需求或知识库 ===")

    def handle_assembly_request(self, requirement_payload: dict[str, Any]) -> None:
        self.run_assembly_state_machine(requirement_payload)

    def run_assembly_state_machine(self, requirement_payload: dict[str, Any]) -> None:
        self.set_state(PipelineState.REQUIREMENT_CLARIFYING, request_type="assembly")
        self.set_state(PipelineState.PLAN_GENERATING, request_type="assembly")
        review = self.review_requirement_payload(requirement_payload)
        self.emit_event("review_result", scope="requirement", **review)
        if review.get("severity") == "fatal":
            self.set_state(PipelineState.FAILED_RECOVERABLE, request_type="assembly", review=review)
            raise ValueError(f"Assembly requirement review failed: {review.get('feedback')}")
        workspace = self.create_assembly_workspace(requirement_payload)
        print("\n[阶段 2] 装配规划")
        self.emit_status("[阶段 2] 装配规划")
        if isinstance(requirement_payload.get("assembly_protocol"), dict) or requirement_payload.get("unique_parts"):
            plan = self.enrich_assembly_plan(self.build_assembly_plan_from_requirement(requirement_payload, workspace), workspace)
            validation_errors = self.validate_assembly_plan_payload(plan)
            if validation_errors:
                self.emit_status("[装配协议补全] Agent1 协议需要规范化，启动规划 agent 修正")
                plan = self.generate_assembly_plan(requirement_payload, workspace)
            else:
                write_json(Path(plan["assembly"]["workspace"]["plan_file"]), plan)
        else:
            plan = self.generate_assembly_plan(requirement_payload, workspace)
        self.write_review_history(plan["assembly"]["workspace"])

        print("\n[阶段 3] 零件建模分发")
        self.emit_status("[阶段 3] 零件建模分发")
        part_results = self.run_parts_parallel(
            full_plan=plan,
            part_specs=plan["assembly"]["parts"],
            max_workers=self.part_parallelism_limit,
        )
        failed_parts = [result for result in part_results if not result.get("success")]
        if failed_parts:
            for result in failed_parts:
                self.set_state(PipelineState.FAILED_RECOVERABLE, part_id=result["part_id"])
            self.set_state(
                PipelineState.FAILED_FATAL,
                failed_part_ids=[result["part_id"] for result in failed_parts],
            )
            print("\n=== 零件建模未全部完成，停止装配阶段 ===")
            return

        print("\n[阶段 4] 装配生成与执行")
        self.emit_status("[阶段 4] 装配生成与执行")
        self.set_state(PipelineState.ASSEMBLY_MODELING, parts=len(part_results))
        assembly_success = self.run_assembly_pipeline(plan, part_results)
        if assembly_success:
            self.set_state(PipelineState.DONE, request_type="assembly")
            print("\n=== 装配需求执行完成 ===")
        else:
            print("\n=== 装配阶段失败，请查看输出目录日志 ===")
        self.last_run_context = {
            "request_type": "assembly",
            "plan": plan,
            "part_results": part_results,
            "success": assembly_success,
        }
        self.write_review_history(plan["assembly"]["workspace"])

    def create_single_part_workspace(self, requirement_payload: dict[str, Any]) -> dict[str, str]:
        name = slugify(requirement_payload.get("name", "part"), "part")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        root_dir = AGENT_OUTPUT_ROOT / f"{name}-{timestamp}"
        part_output_dir = root_dir / "part_output"
        modeling_plan_dir = part_output_dir / "modeling_plan"
        code_dir = part_output_dir / "code"
        execution_dir = part_output_dir / "execution"
        validation_dir = part_output_dir / "validation"
        repair_dir = part_output_dir / "repair"
        json_dir = root_dir / "json"
        screenshots_dir = execution_dir / "screenshots"

        for directory in (
            root_dir,
            part_output_dir,
            modeling_plan_dir,
            code_dir,
            execution_dir,
            screenshots_dir,
            validation_dir,
            repair_dir,
            json_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        return {
            "root_dir": str(root_dir),
            "part_output_dir": str(part_output_dir),
            "part_dir": str(code_dir),
            "modeling_plan_dir": str(modeling_plan_dir),
            "code_dir": str(code_dir),
            "execution_dir": str(execution_dir),
            "validation_dir": str(validation_dir),
            "repair_dir": str(repair_dir),
            "json_dir": str(json_dir),
            "screenshots_dir": str(screenshots_dir),
        }

    def build_single_part_plan(
        self,
        requirement_payload: dict[str, Any],
        workspace: dict[str, str],
    ) -> dict[str, Any]:
        part_id = slugify(requirement_payload.get("name", "part"), "part")
        part_name = requirement_payload.get("name", "Part")
        source_part_spec = requirement_payload.get("part_spec") if isinstance(requirement_payload.get("part_spec"), dict) else {}
        part_id = slugify(source_part_spec.get("part_id") or part_id, "part")
        part_name = source_part_spec.get("name") or part_name
        part_dir = Path(workspace["part_dir"])
        plan = {
            "request_type": "part",
            "name": part_name,
            "detailed_requirement": requirement_payload.get("detailed_requirement", requirement_payload.get("summary", "")),
            "summary": requirement_payload.get("summary", ""),
            "key_requirements": requirement_payload.get("key_requirements", source_part_spec.get("key_dimensions", [])),
            "assumptions": requirement_payload.get("assumptions", []),
            "requested_outputs": requirement_payload.get("required_outputs", requirement_payload.get("requested_outputs", [])),
            "interfaces": requirement_payload.get("interfaces", []),
            "workspace": {
                **workspace,
                "plan_file": str(Path(workspace["json_dir"]) / "part_request.json"),
            },
            "part": {
                "part_id": part_id,
                "name": part_name,
                "function": source_part_spec.get("function", requirement_payload.get("summary", "")),
                "shape": source_part_spec.get("shape", "根据补全需求由建模智能体细化"),
                "key_dimensions": source_part_spec.get("key_dimensions", requirement_payload.get("key_requirements", [])),
                "material_or_notes": source_part_spec.get("material_or_notes", "; ".join(requirement_payload.get("assumptions", []))),
                "interfaces": source_part_spec.get("interfaces", {
                    "faces": [],
                    "axes": [],
                    "points": [],
                }),
                "standalone_modeling_instructions": [
                    *list(source_part_spec.get("standalone_modeling_instructions", []) or []),
                    requirement_payload.get("detailed_requirement", ""),
                    *list(requirement_payload.get("key_requirements", []) or []),
                    *list(requirement_payload.get("review_comments", []) or []),
                ],
                "workspace": {
                    "part_output_dir": workspace["part_output_dir"],
                    "part_dir": str(part_dir),
                    "modeling_plan_file": str(Path(workspace["modeling_plan_dir"]) / "latest_modeling_plan.md"),
                    "modeling_plan_history_file": str(Path(workspace["modeling_plan_dir"]) / "modeling_plan_history.jsonl"),
                    "code_file": str(Path(workspace["code_dir"]) / "latest_code.py"),
                    "code_history_file": str(Path(workspace["code_dir"]) / "code_history.jsonl"),
                    "model_file": str(part_dir / f"{part_id}.SLDPRT"),
                    "log_file": str(Path(workspace["execution_dir"]) / "execution_log.txt"),
                    "execution_report_file": str(Path(workspace["execution_dir"]) / "execution_report.json"),
                    "screenshot_dir": str(Path(workspace["screenshots_dir"])),
                    "static_validation_report_file": str(Path(workspace["validation_dir"]) / "static_validation_report.json"),
                    "dynamic_validation_report_file": str(Path(workspace["validation_dir"]) / "dynamic_validation_report.json"),
                    "repair_history_file": str(Path(workspace["repair_dir"]) / "repair_history.jsonl"),
                    "spec_file": str(Path(workspace["part_output_dir"]) / "part_spec.json"),
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
        assembly_output_dir = root_dir / "assembly_output"
        assembly_plan_dir = assembly_output_dir / "modeling_plan"
        assembly_code_dir = assembly_output_dir / "code"
        assembly_execution_dir = assembly_output_dir / "execution"
        assembly_validation_dir = assembly_output_dir / "validation"
        assembly_repair_dir = assembly_output_dir / "repair"
        json_dir = root_dir / "json"
        screenshots_dir = assembly_execution_dir / "screenshots"

        for directory in (
            root_dir,
            parts_dir,
            assembly_output_dir,
            assembly_plan_dir,
            assembly_code_dir,
            assembly_execution_dir,
            screenshots_dir,
            assembly_validation_dir,
            assembly_repair_dir,
            json_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

        return {
            "root_dir": str(root_dir),
            "parts_dir": str(parts_dir),
            "assembly_output_dir": str(assembly_output_dir),
            "assembly_dir": str(assembly_code_dir),
            "assembly_plan_dir": str(assembly_plan_dir),
            "assembly_code_dir": str(assembly_code_dir),
            "assembly_execution_dir": str(assembly_execution_dir),
            "assembly_validation_dir": str(assembly_validation_dir),
            "assembly_repair_dir": str(assembly_repair_dir),
            "json_dir": str(json_dir),
            "screenshots_dir": str(screenshots_dir),
        }

    def generate_assembly_plan(
        self,
        requirement_payload: dict[str, Any],
        workspace: dict[str, str],
    ) -> dict[str, Any]:
        prompt = self.build_assembly_plan_prompt(requirement_payload, workspace)
        current_prompt = prompt

        for attempt in range(1, 4):
            print(f"  [装配规划尝试 {attempt}/3] 生成装配规划 JSON")
            self.emit_status(f"[装配规划尝试 {attempt}/3] 生成装配规划 JSON")
            response = self.run_agent("AssemblyPlanningAgent", self.assembly_planning_agent, current_prompt)

            try:
                plan = extract_json_payload(response)
            except ValueError:
                current_prompt = self.build_assembly_plan_retry_prompt(
                    requirement_payload=requirement_payload,
                    workspace=workspace,
                    model_response=response,
                    validation_errors=[
                        "上一次输出不是可严格解析的 JSON。",
                        "请只输出一个合法 JSON 对象，不要附带解释、前后缀、Markdown 说明或多余文本。",
                    ],
                )
                continue

            validation_errors = self.validate_assembly_plan_payload(plan)
            if validation_errors:
                current_prompt = self.build_assembly_plan_retry_prompt(
                    requirement_payload=requirement_payload,
                    workspace=workspace,
                    model_response=response,
                    validation_errors=validation_errors,
                )
                continue

            plan = self.enrich_assembly_plan(plan, workspace)
            plan_review = self.review_assembly_plan_payload(plan)
            self.emit_event("review_result", scope="assembly_plan", **plan_review)
            if plan_review.get("severity") == "fatal":
                current_prompt = self.build_assembly_plan_retry_prompt(
                    requirement_payload=requirement_payload,
                    workspace=workspace,
                    model_response=response,
                    validation_errors=[
                        f"Assembly plan review failed: {plan_review.get('feedback', '')}",
                        *list(plan_review.get("comments_for_next_agent", []) or []),
                    ],
                )
                continue
            write_json(Path(plan["assembly"]["workspace"]["plan_file"]), plan)
            return plan

        raise ValueError("AssemblyPlanningAgent failed to return a valid assembly planning JSON after retries.")

    def build_assembly_plan_from_requirement(
        self,
        requirement_payload: dict[str, Any],
        workspace: dict[str, str],
    ) -> dict[str, Any]:
        protocol = requirement_payload.get("assembly_protocol")
        if not isinstance(protocol, dict):
            protocol = {}
        return {
            "request_type": "assembly",
            "assembly": {
                "name": protocol.get("name") or requirement_payload.get("name", "Assembly"),
                "summary": protocol.get("summary") or requirement_payload.get("summary", ""),
                "workspace": {},
                "global_coordinate_system": protocol.get(
                    "global_coordinate_system",
                    {"origin": "assembly origin", "x_direction": "right", "y_direction": "front", "z_direction": "up"},
                ),
                "design_rules": list(protocol.get("design_rules", []) or requirement_payload.get("assumptions", [])),
                "parts": list(requirement_payload.get("unique_parts", []) or []),
                "instances": list(requirement_payload.get("instances", []) or []),
                "assembly_sequence": list(protocol.get("assembly_sequence", []) or []),
                "constraints": list(requirement_payload.get("constraints", []) or []),
                "assembly_output": {},
            },
        }

    def build_assembly_plan_prompt(
        self,
        requirement_payload: dict[str, Any],
        workspace: dict[str, str],
    ) -> str:
        assembly_output = {
            "code_file": str(Path(workspace["assembly_code_dir"]) / "latest_assembly_code.py"),
            "model_file": str(
                Path(workspace["assembly_code_dir"])
                / f"{slugify(requirement_payload.get('name', 'assembly'), 'assembly')}.SLDASM"
            ),
            "log_file": str(Path(workspace["assembly_execution_dir"]) / "execution_log.txt"),
            "screenshot_dir": str(Path(workspace["assembly_execution_dir"]) / "screenshots"),
        }

        return (
            "请根据下面的装配需求和预先创建好的工作空间，直接输出严格合法的 JSON 装配规划。\n\n"
            "【已确认的装配需求】\n"
            f"{json.dumps(requirement_payload, ensure_ascii=False, indent=2)}\n\n"
            "【预先创建的工作空间】\n"
            f"{json.dumps({**workspace, 'plan_file': str(Path(workspace['json_dir']) / 'assembly_plan.json'), 'assembly_output': assembly_output}, ensure_ascii=False, indent=2)}\n\n"
            "要求：\n"
            "1. 输入即使不是标准 JSON 语义，也要正常分析并完成规划。\n"
            "2. 输出必须是一个可直接被 json.loads 解析的 JSON 对象。\n"
            "3. 如果装配中存在多个相同零件，`parts` 中只保留唯一零件定义，通过 `instances` 表达多个实例；不要把重复件展开成多个重复 part。\n"
            "4. 相同几何但接口用途不同的实例，仍然优先复用同一个 part，并在实例层写清接口使用方式。\n"
            "5. 不要输出解释、标题、注释、Markdown 代码块或额外文本。\n"
            "6. 输出前请自行检查 JSON 合法性和字段完整性。\n"
        )

    def build_assembly_plan_retry_prompt(
        self,
        requirement_payload: dict[str, Any],
        workspace: dict[str, str],
        model_response: str,
        validation_errors: list[str],
    ) -> str:
        return (
            self.build_assembly_plan_prompt(requirement_payload, workspace)
            + "\n【上一次输出】\n"
            + model_response
            + "\n\n【必须修复的问题】\n- "
            + "\n- ".join(validation_errors)
            + "\n\n请基于同一需求重新输出完整 JSON，且只输出最终 JSON。"
        )

    def validate_assembly_plan_payload(self, plan: dict[str, Any]) -> list[str]:
        issues: list[str] = []

        if not isinstance(plan, dict):
            return ["顶层输出必须是 JSON 对象。"]

        if plan.get("request_type") != "assembly":
            issues.append("顶层字段 `request_type` 必须是 `assembly`。")

        assembly = plan.get("assembly")
        if not isinstance(assembly, dict):
            issues.append("必须包含对象类型的 `assembly` 字段。")
            return issues

        required_assembly_fields = [
            "name",
            "summary",
            "workspace",
            "global_coordinate_system",
            "design_rules",
            "parts",
            "instances",
            "assembly_sequence",
            "constraints",
            "assembly_output",
        ]
        for field in required_assembly_fields:
            if field not in assembly:
                issues.append(f"`assembly.{field}` 缺失。")

        parts = assembly.get("parts")
        part_ids: set[str] = set()
        if not isinstance(parts, list) or not parts:
            issues.append("`assembly.parts` 必须是非空数组。")
        else:
            required_part_fields = [
                "part_id",
                "name",
                "function",
                "shape",
                "key_dimensions",
                "material_or_notes",
                "quantity",
                "instance_ids",
                "interfaces",
                "assembly_relation_notes",
                "workspace",
                "standalone_modeling_instructions",
            ]
            for index, part in enumerate(parts, start=1):
                if not isinstance(part, dict):
                    issues.append(f"`assembly.parts[{index}]` 必须是对象。")
                    continue

                for field in required_part_fields:
                    if field not in part:
                        issues.append(f"`assembly.parts[{index}].{field}` 缺失。")

                part_id = part.get("part_id")
                if isinstance(part_id, str) and part_id:
                    if part_id in part_ids:
                        issues.append(f"`assembly.parts[{index}].part_id` 重复：{part_id}")
                    part_ids.add(part_id)

                interfaces = part.get("interfaces", {})
                if not isinstance(interfaces, dict):
                    issues.append(f"`assembly.parts[{index}].interfaces` 必须是对象。")
                else:
                    for key in ("faces", "axes", "points"):
                        if key not in interfaces:
                            issues.append(f"`assembly.parts[{index}].interfaces.{key}` 缺失。")
                        elif not isinstance(interfaces.get(key), list):
                            issues.append(f"`assembly.parts[{index}].interfaces.{key}` 必须是数组。")

                if "quantity" in part and not isinstance(part.get("quantity"), int):
                    issues.append(f"`assembly.parts[{index}].quantity` 必须是整数。")

                if "instance_ids" in part and not isinstance(part.get("instance_ids"), list):
                    issues.append(f"`assembly.parts[{index}].instance_ids` 必须是数组。")

        instances = assembly.get("instances")
        instance_ids: set[str] = set()
        instances_by_part: dict[str, list[str]] = {}
        if not isinstance(instances, list) or not instances:
            issues.append("`assembly.instances` 必须是非空数组。")
        else:
            required_instance_fields = [
                "instance_id",
                "part_id",
                "name",
                "instance_role",
                "placement_notes",
                "interface_usage",
            ]
            for index, instance in enumerate(instances, start=1):
                if not isinstance(instance, dict):
                    issues.append(f"`assembly.instances[{index}]` 必须是对象。")
                    continue

                for field in required_instance_fields:
                    if field not in instance:
                        issues.append(f"`assembly.instances[{index}].{field}` 缺失。")

                instance_id = instance.get("instance_id")
                if isinstance(instance_id, str) and instance_id:
                    if instance_id in instance_ids:
                        issues.append(f"`assembly.instances[{index}].instance_id` 重复：{instance_id}")
                    instance_ids.add(instance_id)

                part_id = instance.get("part_id")
                if isinstance(part_id, str) and part_id:
                    if part_ids and part_id not in part_ids:
                        issues.append(f"`assembly.instances[{index}].part_id` 未在 `assembly.parts` 中定义：{part_id}")
                    if isinstance(instance_id, str) and instance_id:
                        instances_by_part.setdefault(part_id, []).append(instance_id)

                interface_usage = instance.get("interface_usage", {})
                if not isinstance(interface_usage, dict):
                    issues.append(f"`assembly.instances[{index}].interface_usage` 必须是对象。")
                else:
                    for key in ("faces", "axes", "points"):
                        if key not in interface_usage:
                            issues.append(f"`assembly.instances[{index}].interface_usage.{key}` 缺失。")
                        elif not isinstance(interface_usage.get(key), list):
                            issues.append(f"`assembly.instances[{index}].interface_usage.{key}` 必须是数组。")

            for index, part in enumerate(parts or [], start=1):
                part_id = part.get("part_id")
                declared_instance_ids = part.get("instance_ids", [])
                if isinstance(part_id, str) and isinstance(declared_instance_ids, list):
                    actual_instance_ids = instances_by_part.get(part_id, [])
                    if set(declared_instance_ids) != set(actual_instance_ids):
                        issues.append(
                            f"`assembly.parts[{index}].instance_ids` 与 `assembly.instances` 中引用该 part 的实例不一致。"
                        )
                    quantity = part.get("quantity")
                    if isinstance(quantity, int) and quantity != len(actual_instance_ids):
                        issues.append(
                            f"`assembly.parts[{index}].quantity` 应等于该 part 对应的实例数量 {len(actual_instance_ids)}。"
                        )

        constraints = assembly.get("constraints")
        if constraints is not None and not isinstance(constraints, list):
            issues.append("`assembly.constraints` 必须是数组。")
        elif isinstance(constraints, list):
            required_constraint_fields = [
                "source_instance_id",
                "source_part_id",
                "source_interface",
                "target_instance_id",
                "target_part_id",
                "target_interface",
                "relation",
                "alignment",
                "offset_mm",
                "notes",
            ]
            for index, constraint in enumerate(constraints, start=1):
                if not isinstance(constraint, dict):
                    issues.append(f"`assembly.constraints[{index}]` 必须是对象。")
                    continue
                for field in required_constraint_fields:
                    if field not in constraint:
                        issues.append(f"`assembly.constraints[{index}].{field}` 缺失。")
                source_instance_id = constraint.get("source_instance_id")
                if source_instance_id not in instance_ids:
                    issues.append(f"`assembly.constraints[{index}].source_instance_id` 未在 `assembly.instances` 中定义。")
                target_instance_id = constraint.get("target_instance_id")
                if target_instance_id != "GROUND" and target_instance_id not in instance_ids:
                    issues.append(f"`assembly.constraints[{index}].target_instance_id` 未在 `assembly.instances` 中定义。")

        sequence = assembly.get("assembly_sequence")
        if sequence is not None and not isinstance(sequence, list):
            issues.append("`assembly.assembly_sequence` 必须是数组。")

        design_rules = assembly.get("design_rules")
        if design_rules is not None and not isinstance(design_rules, list):
            issues.append("`assembly.design_rules` 必须是数组。")

        global_coordinate_system = assembly.get("global_coordinate_system")
        if global_coordinate_system is not None and not isinstance(global_coordinate_system, dict):
            issues.append("`assembly.global_coordinate_system` 必须是对象。")

        return issues

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
        assembly.setdefault("instances", [])
        assembly.setdefault("assembly_sequence", [])
        assembly.setdefault("constraints", [])
        assembly["assembly_output"] = {
            "assembly_output_dir": workspace["assembly_output_dir"],
            "modeling_plan_file": str(Path(workspace["assembly_plan_dir"]) / "latest_assembly_plan.md"),
            "modeling_plan_history_file": str(Path(workspace["assembly_plan_dir"]) / "assembly_plan_history.jsonl"),
            "code_file": str(Path(workspace["assembly_code_dir"]) / "latest_assembly_code.py"),
            "code_history_file": str(Path(workspace["assembly_code_dir"]) / "assembly_code_history.jsonl"),
            "model_file": str(Path(workspace["assembly_code_dir"]) / f"{assembly_name}.SLDASM"),
            "log_file": str(Path(workspace["assembly_execution_dir"]) / "execution_log.txt"),
            "execution_report_file": str(Path(workspace["assembly_execution_dir"]) / "execution_report.json"),
            "screenshot_dir": str(Path(workspace["assembly_execution_dir"]) / "screenshots"),
            "static_validation_report_file": str(Path(workspace["assembly_validation_dir"]) / "static_validation_report.json"),
            "dynamic_validation_report_file": str(Path(workspace["assembly_validation_dir"]) / "dynamic_validation_report.json"),
            "repair_history_file": str(Path(workspace["assembly_repair_dir"]) / "repair_history.jsonl"),
        }

        part_specs = assembly.get("parts", [])
        existing_instances = assembly.get("instances", [])
        instance_map: dict[str, list[dict[str, Any]]] = {}
        for instance in existing_instances:
            if not isinstance(instance, dict):
                continue
            instance_id = slugify(instance.get("instance_id") or instance.get("name", "instance"), "instance")
            part_id = slugify(instance.get("part_id", "part"), "part")
            instance["instance_id"] = instance_id
            instance["part_id"] = part_id
            interface_usage = instance.get("interface_usage")
            if not isinstance(interface_usage, dict):
                interface_usage = {}
            instance["interface_usage"] = {
                "faces": list(interface_usage.get("faces", []) or []),
                "axes": list(interface_usage.get("axes", []) or []),
                "points": list(interface_usage.get("points", []) or []),
            }
            instance_map.setdefault(part_id, []).append(instance)

        for part in part_specs:
            part_id = slugify(part.get("part_id") or part.get("name", "part"), "part")
            part_name = part.get("name", part_id)
            part_output_dir = Path(workspace["parts_dir"]) / part_id / "part_output"
            part_modeling_plan_dir = part_output_dir / "modeling_plan"
            part_code_dir = part_output_dir / "code"
            part_execution_dir = part_output_dir / "execution"
            part_screenshot_dir = part_execution_dir / "screenshots"
            part_validation_dir = part_output_dir / "validation"
            part_repair_dir = part_output_dir / "repair"
            for directory in (
                part_output_dir,
                part_modeling_plan_dir,
                part_code_dir,
                part_execution_dir,
                part_screenshot_dir,
                part_validation_dir,
                part_repair_dir,
            ):
                directory.mkdir(parents=True, exist_ok=True)

            part_workspace = {
                "part_output_dir": str(part_output_dir),
                "part_dir": str(part_code_dir),
                "modeling_plan_file": str(part_modeling_plan_dir / "latest_modeling_plan.md"),
                "modeling_plan_history_file": str(part_modeling_plan_dir / "modeling_plan_history.jsonl"),
                "code_file": str(part_code_dir / "latest_code.py"),
                "code_history_file": str(part_code_dir / "code_history.jsonl"),
                "model_file": str(part_code_dir / f"{part_id}.SLDPRT"),
                "log_file": str(part_execution_dir / "execution_log.txt"),
                "execution_report_file": str(part_execution_dir / "execution_report.json"),
                "screenshot_dir": str(part_screenshot_dir),
                "static_validation_report_file": str(part_validation_dir / "static_validation_report.json"),
                "dynamic_validation_report_file": str(part_validation_dir / "dynamic_validation_report.json"),
                "repair_history_file": str(part_repair_dir / "repair_history.jsonl"),
                "spec_file": str(part_output_dir / "part_spec.json"),
            }
            part["part_id"] = part_id
            part["name"] = part_name
            part_instances = instance_map.get(part_id, [])
            fallback_instance_ids = part.get("instance_ids", [])
            if not isinstance(fallback_instance_ids, list):
                fallback_instance_ids = []
            normalized_instance_ids = [
                slugify(instance_id, f"{part_id}_instance") for instance_id in fallback_instance_ids if instance_id
            ]
            if not part_instances and normalized_instance_ids:
                part_instances = [
                    {
                        "instance_id": instance_id,
                        "part_id": part_id,
                        "name": instance_id,
                        "instance_role": f"{part_name} 实例",
                        "placement_notes": "",
                        "interface_usage": {"faces": [], "axes": [], "points": []},
                    }
                    for instance_id in normalized_instance_ids
                ]
                instance_map[part_id] = part_instances
            part["quantity"] = int(part.get("quantity") or max(len(part_instances), 1))
            part["instance_ids"] = [instance["instance_id"] for instance in part_instances] or normalized_instance_ids or [part_id]
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
                        "review_comments": assembly.get("review_comments", []),
                        "instances": part_instances,
                        "assembly_sequence": assembly.get("assembly_sequence", []),
                    },
                    "part": part,
                },
            )

        if not assembly["instances"]:
            synthesized_instances: list[dict[str, Any]] = []
            for part in part_specs:
                for instance_id in part.get("instance_ids", []) or []:
                    synthesized_instances.append(
                        {
                            "instance_id": instance_id,
                            "part_id": part["part_id"],
                            "name": instance_id,
                            "instance_role": f"{part['name']} 实例",
                            "placement_notes": "",
                            "interface_usage": {"faces": [], "axes": [], "points": []},
                        }
                    )
            assembly["instances"] = synthesized_instances

        return plan

    def run_parts_parallel(
        self,
        full_plan: dict[str, Any],
        part_specs: list[dict[str, Any]],
        max_workers: int = PART_PARALLELISM_LIMIT,
    ) -> list[dict[str, Any]]:
        worker_count = max(1, min(max_workers, PART_PARALLELISM_LIMIT, len(part_specs) or 1))
        self.emit_status(f"[零件并行] 启动 {len(part_specs)} 个零件任务，并行上限 {worker_count}")
        self.emit_event(
            "parallel_parts_start",
            total=len(part_specs),
            max_workers=worker_count,
            part_ids=[part.get("part_id") for part in part_specs],
        )

        results_by_index: dict[int, dict[str, Any]] = {}
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="part-agent") as executor:
            future_to_context = {
                executor.submit(
                    self.run_part_pipeline,
                    full_plan=full_plan,
                    part_spec=part_spec,
                    enable_static_validation=True,
                ): (index, part_spec)
                for index, part_spec in enumerate(part_specs)
            }

            for future in as_completed(future_to_context):
                index, part_spec = future_to_context[future]
                part_id = part_spec["part_id"]
                try:
                    success = future.result()
                    error = None
                except Exception as exc:
                    success = False
                    error = str(exc)
                    self.emit_event("error", error=f"Part {part_id} failed with exception: {exc}")

                result = {
                    "part_id": part_id,
                    "name": part_spec["name"],
                    "success": success,
                    "model_file": part_spec["workspace"]["model_file"],
                }
                if error:
                    result["error"] = error
                results_by_index[index] = result
                self.emit_event("parallel_part_done", **result)
                self.emit_status(
                    f"[零件并行] {part_spec['name']} {'完成' if success else '失败'} "
                    f"({len(results_by_index)}/{len(part_specs)})"
                )

        ordered_results = [results_by_index[index] for index in range(len(part_specs))]
        self.emit_event("parallel_parts_end", results=ordered_results)
        return ordered_results

    def run_part_pipeline(
        self,
        full_plan: dict[str, Any],
        part_spec: dict[str, Any],
        enable_static_validation: bool,
        max_retries: int = 3,
        initial_feedback: str | None = None,
    ) -> bool:
        part_agent = PartModelingAgent()
        validation_agent = PartValidationAgent() if enable_static_validation else None
        workspace_root = (
            full_plan.get("workspace", {}).get("root_dir")
            or full_plan.get("assembly", {}).get("workspace", {}).get("root_dir")
            or part_spec["workspace"]["part_dir"]
        )
        tool_executor = self.make_tool_executor(workspace_root)
        initial_skill_context = self.load_part_skill_context(part_spec, initial_feedback, stage="modeling_plan")
        if initial_skill_context.get("selected_references"):
            self.emit_status(
                f"[skills] {part_spec.get('name', part_spec.get('part_id'))} 加载 "
                + ", ".join(initial_skill_context["selected_references"])
            )
        current_modeling_feedback = initial_feedback
        modeling_plan = ""
        current_code_feedback: str | None = None
        for attempt in range(1, max_retries + 1):
            should_refresh_modeling_plan = attempt == 1 or bool(current_modeling_feedback) or not modeling_plan
            if should_refresh_modeling_plan:
                print(f"    [建模尝试 {attempt}/{max_retries}] 生成 {part_spec['name']} 建模思路")
                self.emit_status(f"[建模尝试 {attempt}/{max_retries}] 生成 {part_spec['name']} 建模思路")
                plan_prompt = self.build_part_modeling_plan_prompt(full_plan, part_spec, current_modeling_feedback)
                modeling_plan = self.run_agent("PartModelingAgent", part_agent, plan_prompt)
                self.persist_part_modeling_plan(part_spec, modeling_plan, attempt)
                current_modeling_feedback = None
            else:
                print(f"    [建模尝试 {attempt}/{max_retries}] 复用 {part_spec['name']} 最新建模思路")
                self.emit_status(f"[建模尝试 {attempt}/{max_retries}] 复用 {part_spec['name']} 最新建模思路，进入代码局部修复")

            print(f"    [代码尝试 {attempt}/{max_retries}] 生成 {part_spec['name']} 代码")
            self.emit_status(f"[代码尝试 {attempt}/{max_retries}] 生成 {part_spec['name']} 代码")
            current_prompt = self.build_part_prompt(full_plan, part_spec, modeling_plan, current_code_feedback)
            response = self.run_agent_with_tools("PartModelingAgent", part_agent, current_prompt, tool_executor)
            code_file = Path(part_spec["workspace"]["code_file"])
            response_code = extract_python_code(response)
            if "```python" in response.lower() or (response_code and not response.strip().startswith("{")):
                code = response_code
            elif code_file.exists():
                code = code_file.read_text(encoding="utf-8", errors="replace")
            else:
                code = extract_python_code(response)

            workdir = Path(part_spec["workspace"]["part_dir"])
            script_name = Path(part_spec["workspace"]["code_file"]).name
            write_text(workdir / script_name, code)
            self.persist_part_code(part_spec, code, attempt)

            self.set_state(PipelineState.PART_VALIDATING, part_id=part_spec["part_id"], attempt=attempt, phase="static")
            static_issues = run_part_plan_checks(full_plan, part_spec, code)
            static_feedback = self.validate_part_code(
                validation_agent=validation_agent,
                full_plan=full_plan,
                part_spec=part_spec,
                code=code,
                deterministic_issues=static_issues,
                execution_result=None,
            )
            write_json(Path(part_spec["workspace"]["static_validation_report_file"]), static_feedback)
            if enable_static_validation and not static_feedback["pass"]:
                feedback = static_feedback.get("feedback", "静态校验未通过")
                failure_type = self.classify_part_failure(feedback, stage="static", explicit=static_feedback.get("failure_type"))
                self.record_part_repair(part_spec, attempt, failure_type, "static_validation", feedback)
                print(f"    [静态校验失败] {feedback}")
                self.emit_status(f"[静态校验失败] {feedback}")
                if failure_type == "modeling_plan_error":
                    current_modeling_feedback = feedback
                    current_code_feedback = None
                else:
                    current_modeling_feedback = None
                    current_code_feedback = feedback
                    part_agent.remember("Static validation failed. Prefer a local edit of latest_code.py if the modeling plan remains valid.")
                continue

            self.set_state(PipelineState.PART_EXECUTING, part_id=part_spec["part_id"], attempt=attempt)
            execution = tool_executor.execute(
                {
                    "tool": "run_solidworks_pipeline",
                    "args": {
                        "script_path": str(workdir / script_name),
                        "screenshot_dir": part_spec["workspace"].get("screenshot_dir") or str(workdir / "screenshots"),
                        "screenshot_base_name": f"{part_spec['part_id']}_attempt_{attempt}",
                    },
                }
            )
            write_text(Path(part_spec["workspace"]["log_file"]), execution.content)
            write_json(Path(part_spec["workspace"]["execution_report_file"]), execution.to_payload())
            self.emit_event("execution_log", title=f"{part_spec['name']} 执行与截图日志", content=execution.content)

            self.record_attempt(part_spec["part_id"], attempt, code, execution.content, execution.success)

            if not execution.success:
                summary = execution.content.splitlines()[-1] if execution.content.splitlines() else execution.content
                print(f"    [执行失败] {summary}")
                self.emit_status(f"[执行失败] {summary}")
                failure_type = self.classify_part_failure(execution.content, stage="dynamic")
                self.record_part_repair(part_spec, attempt, failure_type, "dynamic_execution", execution.content)
                if failure_type == "modeling_plan_error":
                    current_modeling_feedback = execution.content
                    current_code_feedback = None
                else:
                    current_modeling_feedback = None
                    current_code_feedback = execution.content
                    part_agent.remember(f"Attempt {attempt} failed. Edit latest_code.py locally instead of regenerating from scratch.")
                continue

            print("    [执行成功] 开始动态截图检查" if enable_static_validation else "    [执行成功] 动态校验通过")
            self.emit_status("    [执行成功] 开始动态截图检查" if enable_static_validation else "    [执行成功] 动态校验通过")
            if not enable_static_validation:
                return True

            self.set_state(PipelineState.PART_VALIDATING, part_id=part_spec["part_id"], attempt=attempt, phase="dynamic")
            dynamic_feedback = self.validate_part_code(
                validation_agent=validation_agent,
                full_plan=full_plan,
                part_spec=part_spec,
                code=code,
                deterministic_issues=[],
                execution_result=execution.to_payload(),
            )
            write_json(Path(part_spec["workspace"]["dynamic_validation_report_file"]), dynamic_feedback)
            if dynamic_feedback["pass"]:
                print("    [动态截图检查通过]")
                self.emit_status("[动态截图检查通过]")
                return True

            feedback = dynamic_feedback.get("feedback", "动态截图检查未通过")
            failure_type = self.classify_part_failure(feedback, stage="dynamic", explicit=dynamic_feedback.get("failure_type"))
            self.record_part_repair(part_spec, attempt, failure_type, "dynamic_validation", feedback)
            print(f"    [动态截图检查失败] {feedback}")
            self.emit_status(f"[动态截图检查失败] {feedback}")
            if failure_type == "modeling_plan_error":
                current_modeling_feedback = feedback
                current_code_feedback = None
            else:
                current_modeling_feedback = None
                current_code_feedback = feedback

        return False

    def record_attempt(self, part_id: str, attempt: int, code: str, log: str, success: bool) -> None:
        with self.previous_attempts_lock:
            attempts = self.previous_attempts.setdefault(str(part_id), [])
            attempts.append(
                {
                    "attempt": attempt,
                    "success": success,
                    "code_excerpt": code[-4000:],
                    "log_summary": "\n".join(log.splitlines()[-30:]),
                }
            )
            self.previous_attempts[str(part_id)] = attempts[-5:]

    def validate_part_code(
        self,
        validation_agent: PartValidationAgent | None,
        full_plan: dict[str, Any],
        part_spec: dict[str, Any],
        code: str,
        deterministic_issues: list[str],
        execution_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if validation_agent is None:
            return {"pass": not deterministic_issues, "feedback": "; ".join(deterministic_issues)}

        prompt = json.dumps(
            {
                "full_plan": full_plan,
                "part_spec": part_spec,
                "generated_code": code,
                "deterministic_issues": deterministic_issues,
                "execution_result": execution_result or {},
                "screenshot_files": (execution_result or {}).get("data", {}).get("screenshots", []),
            },
            ensure_ascii=False,
            indent=2,
        )

        screenshot_files = (execution_result or {}).get("data", {}).get("screenshots", [])
        if screenshot_files:
            response = validation_agent.chat_with_images(prompt, list(screenshot_files))
        else:
            response = self.run_agent("PartValidationAgent", validation_agent, prompt)
        try:
            validation = extract_json_payload(response)
        except ValueError:
            validation = {
                "pass": False,
                "feedback": "静态校验 agent 未返回可解析 JSON，请重新生成并明确路径、接口和方向关系。",
            }

        hard_issues = [issue for issue in deterministic_issues if issue.startswith("HARD:")]
        soft_issues = [issue for issue in deterministic_issues if not issue.startswith("HARD:")]

        if hard_issues:
            merged_feedback = validation.get("feedback", "")
            validation["pass"] = False
            validation.setdefault("failure_type", "code_implementation_error")
            validation["feedback"] = "; ".join([*hard_issues, merged_feedback]).strip("; ")
            return validation

        if soft_issues:
            merged_feedback = validation.get("feedback", "")
            if validation.get("pass", False):
                validation["feedback"] = "; ".join([merged_feedback, *soft_issues]).strip("; ")
            else:
                validation["feedback"] = "; ".join([*soft_issues, merged_feedback]).strip("; ")
        validation.setdefault("pass", not deterministic_issues)
        validation.setdefault("failure_type", "unknown")
        validation.setdefault("feedback", "")
        return validation

    def build_part_modeling_plan_prompt(
        self,
        full_plan: dict[str, Any],
        part_spec: dict[str, Any],
        retry_feedback: str | None,
    ) -> str:
        payload = {
            "stage": "modeling_plan",
            "task": "请先为该零件生成建模思路，不要输出代码。需要说明特征顺序、关键草图、基准、接口命名、保存目标和风险点。",
            "full_plan_summary": full_plan,
            "part_spec": part_spec,
            "dynamic_skill_context": self.load_part_skill_context(part_spec, retry_feedback, stage="modeling_plan"),
            "output_file": part_spec.get("workspace", {}).get("modeling_plan_file"),
            "required_persistence": {
                "latest_modeling_plan": part_spec.get("workspace", {}).get("modeling_plan_file"),
                "history": part_spec.get("workspace", {}).get("modeling_plan_history_file"),
            },
        }
        if retry_feedback:
            payload["retry_feedback"] = retry_feedback
            payload["failure_policy"] = "优先判断是否需要修改建模策略；如果是代码实现问题，只指出应保持的建模意图。"
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def persist_part_modeling_plan(self, part_spec: dict[str, Any], modeling_plan: str, attempt: int) -> None:
        workspace = part_spec.get("workspace", {})
        write_text(Path(workspace["modeling_plan_file"]), modeling_plan)
        append_jsonl(
            Path(workspace["modeling_plan_history_file"]),
            {"attempt": attempt, "modeling_plan": modeling_plan},
        )

    def persist_part_code(self, part_spec: dict[str, Any], code: str, attempt: int) -> None:
        workspace = part_spec.get("workspace", {})
        write_text(Path(workspace["code_file"]), code)
        append_jsonl(Path(workspace["code_history_file"]), {"attempt": attempt, "code": code})

    def record_part_repair(self, part_spec: dict[str, Any], attempt: int, failure_type: str, stage: str, feedback: str) -> None:
        append_jsonl(
            Path(part_spec["workspace"]["repair_history_file"]),
            {
                "attempt": attempt,
                "stage": stage,
                "failure_type": failure_type,
                "feedback": feedback,
            },
        )

    def classify_part_failure(self, feedback: str, stage: str, explicit: str | None = None) -> str:
        allowed = {"modeling_plan_error", "code_implementation_error", "asset_binding_error", "unknown"}
        text = str(feedback).lower()
        code_markers = (
            "syntax",
            "traceback",
            "exception",
            "attributeerror",
            "typeerror",
            "importerror",
            "extrude_cut",
            "insertsketch2",
            "selectbyid2",
            "sw_doc",
            "sw_instance",
            "com_error",
            "selection",
            "sketch",
            "failed to select",
            "featuremanager",
            "语法",
            "异常",
            "报错",
            "草图选择失败",
            "无法拉伸",
            "无法切除",
            "拉伸切除",
            "显式选中",
            "选择逻辑",
            "代码执行日志",
        )
        if any(marker in text for marker in code_markers):
            return "code_implementation_error"
        if any(marker in text for marker in ("asset", "standard part", "template", "binding", "materialize", "标准件", "资产")):
            return "asset_binding_error"
        if explicit in allowed:
            return explicit
        if any(marker in text for marker in ("missing feature", "topology", "geometry", "shape", "interface missing", "特征缺失", "拓扑", "几何", "接口缺失")):
            return "modeling_plan_error"
        if stage == "dynamic":
            return "code_implementation_error"
        return "unknown"

    def load_part_skill_context(self, part_spec: dict[str, Any], feedback: str | None, stage: str) -> dict[str, Any]:
        tags = self.infer_part_skill_tags(part_spec, feedback, stage)
        context = self.skill_manager.load_relevant_context(
            "part_agent",
            tags=tags,
            max_references=8,
            include_assets=True,
        )
        return {
            "tags": tags,
            "selected_references": [item.get("id") for item in context.selected_references],
            "selected_assets": context.selected_assets,
            "context_text": context.context_text,
        }

    def infer_part_skill_tags(self, part_spec: dict[str, Any], feedback: str | None, stage: str) -> list[str]:
        tags = {
            "core",
            "part_modeling",
            "modeling_plan",
            "solidworks_api",
            "api_reference",
            "code_generation",
            "repair",
            "interfaces",
            "units",
            "assembly_reuse",
            "reference_axis",
            "reference_plane",
        }
        if stage in {"code_generation", "code_repair"}:
            tags.update({"local_edit", "solidworks_api"})
        if feedback:
            tags.update({"failure", "local_edit"})

        text = json.dumps(part_spec, ensure_ascii=False).lower() + "\n" + str(feedback or "").lower()
        gear_markers = (
            "gear",
            "spur_gear",
            "planet",
            "planetary",
            "sun_gear",
            "planet_gear",
            "ring_gear",
            "齿轮",
            "太阳轮",
            "行星轮",
            "内齿圈",
            "齿圈",
            "模数",
            "齿数",
            "分度圆",
        )
        if any(marker in text for marker in gear_markers):
            tags.update(
                {
                    "gear",
                    "spur_gear",
                    "standard_part",
                    "asset_backed",
                    "parameters",
                    "secondary_edit",
                    "interfaces",
                }
            )
        if any(marker in text for marker in ("孔", "通孔", "轴孔", "bore", "shaft", "keyway", "键槽")):
            tags.update({"secondary_edit", "interfaces"})
        return sorted(tags)

    def build_part_prompt(
        self,
        full_plan: dict[str, Any],
        part_spec: dict[str, Any],
        modeling_plan: str,
        retry_feedback: str | None,
    ) -> str:
        payload = {
            "stage": "code_repair" if retry_feedback else "code_generation",
            "mode": "tool_first_local_edit",
            "tool_protocol": {
                "response_shape": {"thought": "...", "next_action": {"tool": "read_file", "args": {"path": "..."}}},
                "available_tools": [
                    "read_file(path)",
                    "write_file(path, content)",
                    "run_python(script_path)",
                    "run_solidworks_pipeline(script_path, screenshot_dir, screenshot_base_name)",
                    "list_dir(path)",
                    "search_in_kb(query)",
                    "load_previous_attempt(part_id)",
                    "summarize_log(log)",
                ],
            },
            "local_edit_policy": "If code_file already exists or retry_feedback is present, inspect/read the existing file and change only the necessary parts before writing the complete updated file.",
            "execution_policy": "After code generation the orchestrator will run: clear SolidWorks -> execute code -> capture screenshots under a SolidWorks lock. Feedback includes execution log and screenshot files.",
            "task": "请为下面的零件生成完整可执行 Python 建模代码；如果该零件会被多个实例复用，也只建模一次通用零件模板。",
            "latest_modeling_plan": modeling_plan,
            "latest_modeling_plan_file": part_spec.get("workspace", {}).get("modeling_plan_file"),
            "dynamic_skill_context": self.load_part_skill_context(
                part_spec,
                retry_feedback,
                stage="code_repair" if retry_feedback else "code_generation",
            ),
            "full_plan_summary": full_plan,
            "part_spec": part_spec,
            "code_file": part_spec.get("workspace", {}).get("code_file"),
            "required_persistence": {
                "latest_code": part_spec.get("workspace", {}).get("code_file"),
                "code_history": part_spec.get("workspace", {}).get("code_history_file"),
            },
        }
        if retry_feedback:
            payload["retry_feedback"] = retry_feedback
            payload["instruction"] = (
                "Prefer a local edit of the existing code_file. Use read_file/load_previous_attempt first when useful, "
                "then write_file the complete corrected file. If feedback says 草图选择失败/无法拉伸/extrude_cut failed, "
                "do not change the modeling intent; repair sketch creation and cut invocation in latest_code.py. For gear standard parts, "
                "use the proven wrapper pattern only: sketch = sgear.insert_sketch_on_plane('XY'); "
                "sgear.create_circle(..., 'XY'); sgear.extrude_cut(sketch, depth). Do not add SelectByID2, InsertSketch2, sw_doc, or sw_instance."
            )
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def run_assembly_pipeline(
        self,
        plan: dict[str, Any],
        part_results: list[dict[str, Any]],
        max_retries: int = 3,
    ) -> bool:
        assembly_output = plan["assembly"]["assembly_output"]
        tool_executor = self.make_tool_executor(plan["assembly"]["workspace"]["root_dir"])
        assembly_agent = AssemblyAgent()
        current_plan_feedback: str | None = None
        current_code_feedback: str | None = None
        modeling_plan = ""

        for attempt in range(1, max_retries + 1):
            print(f"  [装配尝试 {attempt}/{max_retries}] 生成装配思路")
            self.emit_status(f"[装配尝试 {attempt}/{max_retries}] 生成装配思路")
            modeling_plan = self.run_agent(
                "AssemblyAgent",
                assembly_agent,
                self.build_assembly_modeling_plan_prompt(plan, part_results, current_plan_feedback),
            )
            self.persist_assembly_modeling_plan(plan, modeling_plan, attempt)

            print(f"  [装配尝试 {attempt}/{max_retries}] 生成装配代码")
            self.emit_status(f"[装配尝试 {attempt}/{max_retries}] 生成装配代码")
            current_prompt = self.build_assembly_prompt(plan, part_results, modeling_plan, current_code_feedback)
            response = self.run_agent_with_tools("AssemblyAgent", assembly_agent, current_prompt, tool_executor)
            code_file = Path(assembly_output["code_file"])
            response_code = extract_python_code(response)
            if "```python" in response.lower() or (response_code and not response.strip().startswith("{")):
                code = response_code
            elif code_file.exists():
                code = code_file.read_text(encoding="utf-8", errors="replace")
            else:
                code = extract_python_code(response)

            workdir = Path(plan["assembly"]["workspace"]["assembly_dir"])
            script_name = Path(assembly_output["code_file"]).name
            write_text(workdir / script_name, code)
            self.persist_assembly_code(plan, code, attempt)

            issues = run_assembly_plan_checks(plan, code)
            static_report = {"pass": not issues, "failure_type": "unknown", "feedback": "; ".join(issues)}
            if issues:
                failure_type = self.classify_assembly_failure(static_report["feedback"], stage="static")
                static_report["failure_type"] = failure_type
                write_json(Path(assembly_output["static_validation_report_file"]), static_report)
                self.record_assembly_repair(plan, attempt, failure_type, "static_validation", static_report["feedback"])
                print(f"  [装配静态检查失败] {static_report['feedback']}")
                self.emit_status(f"[装配静态检查失败] {static_report['feedback']}")
                if failure_type == "assembly_plan_error":
                    current_plan_feedback = static_report["feedback"]
                    current_code_feedback = None
                else:
                    current_plan_feedback = None
                    current_code_feedback = static_report["feedback"]
                continue
            write_json(Path(assembly_output["static_validation_report_file"]), static_report)

            self.set_state(PipelineState.ASSEMBLY_EXECUTING, attempt=attempt)
            execution = tool_executor.execute(
                {
                    "tool": "run_solidworks_pipeline",
                    "args": {
                        "script_path": str(workdir / script_name),
                        "screenshot_dir": assembly_output.get("screenshot_dir") or str(workdir / "screenshots"),
                        "screenshot_base_name": f"assembly_attempt_{attempt}",
                    },
                }
            )
            write_text(Path(assembly_output["log_file"]), execution.content)
            write_json(Path(assembly_output["execution_report_file"]), execution.to_payload())
            self.emit_event("execution_log", title="装配执行与截图日志", content=execution.content)

            if not execution.success:
                summary = execution.content.splitlines()[-1] if execution.content.splitlines() else execution.content
                print(f"  [装配执行失败] {summary}")
                self.emit_status(f"[装配执行失败] {summary}")
                failure_type = self.classify_assembly_failure(execution.content, stage="dynamic")
                self.record_assembly_repair(plan, attempt, failure_type, "dynamic_execution", execution.content)
                if failure_type == "assembly_plan_error":
                    current_plan_feedback = execution.content
                    current_code_feedback = None
                else:
                    current_plan_feedback = None
                    current_code_feedback = execution.content
                continue

            dynamic_report = {
                "pass": True,
                "failure_type": "unknown",
                "feedback": "Execution and screenshot pipeline completed.",
                "screenshots": execution.data.get("screenshots", []),
            }
            write_json(Path(assembly_output["dynamic_validation_report_file"]), dynamic_report)
            print("  [装配执行成功]")
            self.emit_status("[装配执行成功]")
            return True

        return False

    def build_assembly_prompt(
        self,
        plan: dict[str, Any],
        part_results: list[dict[str, Any]],
        modeling_plan: str,
        retry_feedback: str | None,
    ) -> str:
        payload = {
            "stage": "code_repair" if retry_feedback else "code_generation",
            "task": "请根据装配规划和已完成的零件输出，生成完整可执行 Python 装配代码；对于重复件要复用同一个零件文件并按 instance_id 插入多个组件实例。",
            "mode": "tool_first_local_edit",
            "tool_protocol": {
                "response_shape": {"thought": "...", "next_action": {"tool": "read_file", "args": {"path": "..."}}},
                "available_tools": [
                    "read_file(path)",
                    "write_file(path, content)",
                    "run_python(script_path)",
                    "run_solidworks_pipeline(script_path, screenshot_dir, screenshot_base_name)",
                    "list_dir(path)",
                    "search_in_kb(query)",
                    "load_previous_attempt(part_id)",
                    "summarize_log(log)",
                ],
            },
            "local_edit_policy": "If assembly code already exists or retry_feedback is present, inspect/read the existing file and change only the necessary parts before writing the complete updated file.",
            "execution_policy": "After code generation the orchestrator will run: clear SolidWorks -> execute code -> capture screenshots under a SolidWorks lock. Feedback includes execution log and screenshot files.",
            "latest_assembly_plan": modeling_plan,
            "latest_assembly_plan_file": plan.get("assembly", {}).get("assembly_output", {}).get("modeling_plan_file"),
            "code_file": plan.get("assembly", {}).get("assembly_output", {}).get("code_file"),
            "assembly_plan": plan,
            "part_results": part_results,
            "required_persistence": {
                "latest_assembly_code": plan.get("assembly", {}).get("assembly_output", {}).get("code_file"),
                "assembly_code_history": plan.get("assembly", {}).get("assembly_output", {}).get("code_history_file"),
            },
        }
        if retry_feedback:
            payload["retry_feedback"] = retry_feedback
            payload["instruction"] = "Prefer a local edit of the existing assembly code_file. Use read_file first when useful, then write_file the complete corrected file."
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def build_assembly_modeling_plan_prompt(
        self,
        plan: dict[str, Any],
        part_results: list[dict[str, Any]],
        retry_feedback: str | None,
    ) -> str:
        payload = {
            "stage": "assembly_plan",
            "task": "请先生成装配建模思路，不要输出代码。需要说明零件插入顺序、实例映射、配合约束、重复件复用、坐标/基准和风险点。",
            "assembly_plan": plan,
            "part_results": part_results,
            "output_file": plan.get("assembly", {}).get("assembly_output", {}).get("modeling_plan_file"),
        }
        if retry_feedback:
            payload["retry_feedback"] = retry_feedback
            payload["failure_policy"] = "优先判断失败属于装配思路、代码实现、约束表达或资产接口问题。"
        return json.dumps(payload, ensure_ascii=False, indent=2)

    def persist_assembly_modeling_plan(self, plan: dict[str, Any], modeling_plan: str, attempt: int) -> None:
        output = plan["assembly"]["assembly_output"]
        write_text(Path(output["modeling_plan_file"]), modeling_plan)
        append_jsonl(Path(output["modeling_plan_history_file"]), {"attempt": attempt, "modeling_plan": modeling_plan})

    def persist_assembly_code(self, plan: dict[str, Any], code: str, attempt: int) -> None:
        output = plan["assembly"]["assembly_output"]
        write_text(Path(output["code_file"]), code)
        append_jsonl(Path(output["code_history_file"]), {"attempt": attempt, "code": code})

    def record_assembly_repair(
        self,
        plan: dict[str, Any],
        attempt: int,
        failure_type: str,
        stage: str,
        feedback: str,
    ) -> None:
        append_jsonl(
            Path(plan["assembly"]["assembly_output"]["repair_history_file"]),
            {
                "attempt": attempt,
                "stage": stage,
                "failure_type": failure_type,
                "feedback": feedback,
            },
        )

    def classify_assembly_failure(self, feedback: str, stage: str) -> str:
        text = str(feedback).lower()
        if any(marker in text for marker in ("constraint", "mate", "coincident", "concentric", "约束", "配合")):
            return "constraint_error"
        if any(marker in text for marker in ("interface", "asset", "model_file", "missing part", "接口", "资产", "零件路径")):
            return "asset_interface_error"
        if any(marker in text for marker in ("topology", "sequence", "instance", "placement", "拓扑", "实例", "位置")):
            return "assembly_plan_error"
        if any(marker in text for marker in ("syntax", "traceback", "exception", "attributeerror", "typeerror", "语法", "异常", "报错")):
            return "assembly_code_error"
        return "assembly_code_error" if stage == "dynamic" else "unknown"
