#!/usr/bin/env python3
"""
Install this skill into ~/.codex/skills/provider-image.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def _die(message: str, code: int = 1) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(code)


def main() -> int:
    source_dir = Path(__file__).resolve().parents[1]
    target_dir = Path.home() / ".codex" / "skills" / "provider-image"
    backup_dir = target_dir.with_name(target_dir.name + ".bak")

    if not source_dir.exists():
        _die(f"Source skill directory not found: {source_dir}")

    target_dir.parent.mkdir(parents=True, exist_ok=True)

    if backup_dir.exists():
        shutil.rmtree(backup_dir, ignore_errors=True)

    if target_dir.exists():
        try:
            target_dir.replace(backup_dir)
        except Exception:
            shutil.rmtree(backup_dir, ignore_errors=True)
            shutil.copytree(
                source_dir,
                backup_dir,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
                dirs_exist_ok=True,
            )
            print(target_dir)
            print(
                "Could not replace the existing install cleanly. "
                f"A refreshed copy was written to {backup_dir}. "
                "Close any process that may lock the old install, then rename the backup into place."
            )
            return 0

    shutil.copytree(
        source_dir,
        target_dir,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
    )
    shutil.rmtree(backup_dir, ignore_errors=True)
    print(target_dir)
    print("Restart Codex to pick up the updated skill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
