from __future__ import annotations

import json
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
    """Lightweight agent-specific progressive-disclosure skill loader."""

    def __init__(self, skills_root: Path, max_reference_chars: int = 6000) -> None:
        self.skills_root = skills_root.resolve()
        self.max_reference_chars = max_reference_chars

    def load_agent_skill_header(self, agent_name: str) -> str:
        """Load the agent-specific SKILL.md if it exists."""
        skill_file = self.skills_root / agent_name / "SKILL.md"
        if not self._is_under_skills(skill_file) or not skill_file.is_file():
            return ""
        return skill_file.read_text(encoding="utf-8", errors="replace")

    def load_relevant_context(
        self,
        agent_name: str,
        tags: list[str],
        max_references: int = 5,
        include_assets: bool = True,
    ) -> LoadedSkillContext:
        """
        Load only references/assets whose tags match the requested tags.
        Uses simple tag-overlap scoring in v3.
        """
        index = self.list_agent_skills(agent_name)
        if not index:
            return LoadedSkillContext(agent_name, [], [], "")

        requested_tags = {str(tag).strip().lower() for tag in tags if str(tag).strip()}
        references = self._rank_entries(index.get("references", []), requested_tags)[:max_references]
        assets = self._rank_entries(index.get("assets", []), requested_tags) if include_assets else []

        chunks: list[str] = []
        for entry in references:
            path = self._entry_path(agent_name, entry)
            if not self._is_under_skills(path) or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if len(text) > self.max_reference_chars:
                text = text[: self.max_reference_chars] + "\n...[truncated]"
            chunks.append(f"# {entry.get('id', path.stem)}\n{text}")

        return LoadedSkillContext(
            agent_name=agent_name,
            selected_references=references,
            selected_assets=assets,
            context_text="\n\n".join(chunks),
        )

    def list_agent_skills(self, agent_name: str) -> dict[str, Any]:
        """Return parsed skill_index.json for debugging."""
        index_file = self.skills_root / agent_name / "skill_index.json"
        if not self._is_under_skills(index_file) or not index_file.is_file():
            return {}
        try:
            payload = json.loads(index_file.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _rank_entries(self, entries: Any, requested_tags: set[str]) -> list[dict[str, Any]]:
        if not isinstance(entries, list):
            return []
        scored: list[tuple[int, dict[str, Any]]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_tags = {str(tag).strip().lower() for tag in entry.get("tags", []) if str(tag).strip()}
            score = len(entry_tags & requested_tags)
            if score > 0 or "core" in entry_tags:
                scored.append((score, entry))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [entry for _, entry in scored]

    def _entry_path(self, agent_name: str, entry: dict[str, Any]) -> Path:
        return (self.skills_root / agent_name / str(entry.get("path", ""))).resolve()

    def _is_under_skills(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.skills_root)
            return True
        except ValueError:
            return False
