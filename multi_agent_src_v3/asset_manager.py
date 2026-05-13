from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass
class MaterializedAsset:
    asset_id: str
    source_path: str
    working_copy_path: str
    sidecar_path: str | None
    source_hash: str | None


class AssetManager:
    """Copy read-only skill or standard-library assets into a task workspace."""

    def __init__(self, read_only_roots: list[Path]) -> None:
        self.read_only_roots = [root.resolve() for root in read_only_roots]

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
        source_path = self._find_asset(asset_id)
        workspace = workspace_root.resolve()
        target_dir = workspace / "materialized_assets" / self._safe_name(instance_id)
        target_dir.mkdir(parents=True, exist_ok=True)

        if source_path.is_dir():
            working_copy_path = target_dir / source_path.name
            if working_copy_path.exists():
                shutil.rmtree(working_copy_path)
            shutil.copytree(source_path, working_copy_path)
            source_hash = None
        else:
            working_copy_path = target_dir / source_path.name
            shutil.copy2(source_path, working_copy_path)
            source_hash = self._sha256(source_path)

        sidecar = working_copy_path.with_suffix(working_copy_path.suffix + ".sidecar.json")
        return MaterializedAsset(
            asset_id=asset_id,
            source_path=str(source_path),
            working_copy_path=str(working_copy_path),
            sidecar_path=str(sidecar) if sidecar.exists() else None,
            source_hash=source_hash,
        )

    def _find_asset(self, asset_id: str) -> Path:
        requested = Path(asset_id)
        if requested.is_absolute() and self._is_under_read_only_root(requested) and requested.exists():
            return requested.resolve()

        safe_id = self._safe_name(asset_id)
        for root in self.read_only_roots:
            for candidate in root.rglob("*"):
                if candidate.name == asset_id or candidate.stem == safe_id or candidate.name == safe_id:
                    return candidate.resolve()
        raise FileNotFoundError(f"Asset not found in read-only roots: {asset_id}")

    def _is_under_read_only_root(self, path: Path) -> bool:
        resolved = path.resolve()
        for root in self.read_only_roots:
            try:
                resolved.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def _safe_name(self, value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in str(value)).strip("_") or "asset"

    def _sha256(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as file:
            for chunk in iter(lambda: file.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
