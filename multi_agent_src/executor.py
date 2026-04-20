from __future__ import annotations

import ast
import os
import subprocess
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ExecutionResult:
    success: bool
    log: str
    script_path: Path


def execute_python_code(code: str, workdir: Path, script_name: str) -> ExecutionResult:
    workdir.mkdir(parents=True, exist_ok=True)
    script_path = workdir / script_name

    try:
        with script_path.open("w", encoding="utf-8") as file:
            if not code.startswith("# -*- coding: utf-8 -*-"):
                file.write("# -*- coding: utf-8 -*-\n")
            file.write(code)

        custom_env = os.environ.copy()
        custom_env["PYTHONIOENCODING"] = "utf-8"

        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(workdir),
            capture_output=True,
            env=custom_env,
        )

        def safe_decode(payload: bytes) -> str:
            if not payload:
                return ""
            try:
                return payload.decode("utf-8")
            except UnicodeDecodeError:
                return payload.decode("gbk", errors="replace")

        stdout = safe_decode(result.stdout).strip()
        stderr = safe_decode(result.stderr).strip()

        if result.returncode == 0:
            return ExecutionResult(
                success=True,
                log=stdout or "Execution Successful. (No console output)",
                script_path=script_path,
            )

        error_log = stderr or stdout or f"Process exited with code {result.returncode}"
        return ExecutionResult(
            success=False,
            log=f"Execution Failed with error:\n{error_log}",
            script_path=script_path,
        )
    except Exception:
        return ExecutionResult(
            success=False,
            log=f"System Error during subprocess call:\n{traceback.format_exc()}",
            script_path=script_path,
        )


def run_basic_python_checks(code: str) -> list[str]:
    issues: list[str] = []
    try:
        ast.parse(code)
    except SyntaxError as exc:
        issues.append(f"Python 语法错误: line {exc.lineno}, offset {exc.offset}, {exc.msg}")
    return issues


def run_part_plan_checks(full_plan: dict[str, Any], part_spec: dict[str, Any], code: str) -> list[str]:
    issues = run_basic_python_checks(code)

    workspace = part_spec.get("workspace", {})
    model_file = workspace.get("model_file", "")
    if model_file and model_file not in code:
        issues.append("代码中未显式使用 part_spec.workspace.model_file 指定的保存路径。")

    part_name = part_spec.get("name", "")
    if part_name and part_name not in code:
        issues.append("代码中未显式体现零件名称，后续排查日志会较困难。")

    interface_names: list[str] = []
    interfaces = part_spec.get("interfaces", {})
    for category in ("faces", "axes", "points"):
        for item in interfaces.get(category, []) or []:
            name = item.get("name")
            if name:
                interface_names.append(name)

    if interface_names and not any(name in code for name in interface_names):
        issues.append("代码中没有体现任何规划接口名称，可能无法支撑后续装配引用。")

    assembly_name = (
        full_plan.get("assembly", {}).get("name")
        if full_plan.get("request_type") == "assembly"
        else full_plan.get("name")
    )
    if assembly_name and assembly_name not in code:
        issues.append("代码中未包含装配或任务名称，建议补充到日志或文件名相关代码中。")

    return issues


def run_assembly_plan_checks(plan: dict[str, Any], code: str) -> list[str]:
    issues = run_basic_python_checks(code)

    assembly = plan.get("assembly", {})
    assembly_output = assembly.get("assembly_output", {})
    model_file = assembly_output.get("model_file", "")
    if model_file and model_file not in code:
        issues.append("装配代码中未显式使用 assembly_output.model_file 指定的保存路径。")

    for part in assembly.get("parts", []):
        model_path = part.get("workspace", {}).get("model_file", "")
        if model_path and model_path not in code:
            issues.append(f"装配代码中未显式使用零件路径: {model_path}")

    return issues
