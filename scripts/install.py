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

    if not source_dir.exists():
        _die(f"Source skill directory not found: {source_dir}")

    target_dir.parent.mkdir(parents=True, exist_ok=True)

    if target_dir.exists():
        shutil.rmtree(target_dir)

    shutil.copytree(source_dir, target_dir)
    print(target_dir)
    print("Restart Codex to pick up the updated skill.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
