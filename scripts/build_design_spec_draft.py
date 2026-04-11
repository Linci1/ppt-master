#!/usr/bin/env python3
"""Generate project-level design_spec draft from current production analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

try:
    from build_production_packet import analyze_project, generate_design_spec_draft_text
except ImportError:
    import sys

    TOOLS_DIR = Path(__file__).resolve().parent
    if str(TOOLS_DIR) not in sys.path:
        sys.path.insert(0, str(TOOLS_DIR))
    from build_production_packet import analyze_project, generate_design_spec_draft_text  # type: ignore


def main() -> None:
    parser = argparse.ArgumentParser(description="为项目生成 design_spec 初稿。")
    parser.add_argument("project_path", help="项目路径")
    parser.add_argument("-o", "--output", help="输出路径；默认写入 <project>/notes/design_spec_draft.md")
    args = parser.parse_args()

    project_dir = Path(args.project_path).expanduser().resolve()
    analysis = analyze_project(project_dir)
    output = Path(args.output).expanduser().resolve() if args.output else project_dir / "notes" / "design_spec_draft.md"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generate_design_spec_draft_text(analysis) + "\n", encoding="utf-8")
    print(f"Wrote: {output}")


if __name__ == "__main__":
    main()
