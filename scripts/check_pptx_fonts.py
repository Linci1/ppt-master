#!/usr/bin/env python3
from __future__ import annotations

"""检查导出后的 PPTX 是否存在中文字体碎裂或替换风险。

用法：
    python3 scripts/check_pptx_fonts.py <pptx_path>
    python3 scripts/check_pptx_fonts.py <project_path>
"""

import html
import re
import sys
from collections import Counter
from pathlib import Path
from zipfile import BadZipFile, ZipFile, is_zipfile


SLIDE_RE = re.compile(r"ppt/slides/slide\d+\.xml$")
RUN_RE = re.compile(
    r'<a:rPr[^>]*>.*?<a:latin typeface="([^"]*)"/>.*?<a:ea typeface="([^"]*)"/>.*?</a:rPr>\s*<a:t>(.*?)</a:t>',
    re.S,
)

FONT_ALIASES = {
    "microsoft yahei": "microsoft yahei",
    "微软雅黑": "microsoft yahei",
    "arial": "arial",
    "arialmt": "arial",
}

APPROVED_CJK_FONTS = {"microsoft yahei"}
APPROVED_LATIN_FONTS = {"arial", "microsoft yahei"}


def is_cjk(text: str) -> bool:
    for ch in text:
        cp = ord(ch)
        if (
            0x4E00 <= cp <= 0x9FFF
            or 0x3400 <= cp <= 0x4DBF
            or 0x2E80 <= cp <= 0x2EFF
            or 0x3000 <= cp <= 0x303F
            or 0xFF00 <= cp <= 0xFFEF
            or 0xF900 <= cp <= 0xFAFF
        ):
            return True
    return False


def resolve_pptx(target: Path) -> Path:
    if target.is_file():
        return target

    candidates = sorted(
        [
            p
            for p in target.glob("*.pptx")
            if not p.name.startswith(".~")
            if not p.name.endswith("_svg.pptx")
        ],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"在 {target} 下未找到原生 PPTX 文件")

    for candidate in candidates:
        if is_zipfile(candidate):
            return candidate

    raise FileNotFoundError(f"在 {target} 下未找到可读取的原生 PPTX 文件")


def normalize_font_name(name: str) -> str:
    compact = re.sub(r"\s+", " ", name.strip()).lower()
    return FONT_ALIASES.get(compact, compact)


def inspect_pptx(pptx_path: Path) -> tuple[list[str], Counter]:
    warnings: list[str] = []
    cjk_fonts: Counter = Counter()

    try:
        with ZipFile(pptx_path) as zf:
            for name in sorted(n for n in zf.namelist() if SLIDE_RE.match(n)):
                xml = zf.read(name).decode("utf-8", "ignore")
                for latin, ea, text in RUN_RE.findall(xml):
                    plain = html.unescape(text).strip()
                    if not plain or not is_cjk(plain):
                        continue
                    latin_norm = normalize_font_name(latin)
                    ea_norm = normalize_font_name(ea)
                    cjk_fonts[(latin_norm, ea_norm)] += 1
                    if ea_norm not in APPROVED_CJK_FONTS:
                        warnings.append(
                            f"{Path(name).name}: CJK run uses unexpected ea font={ea} text={plain[:40]}"
                        )
                    elif latin_norm not in APPROVED_LATIN_FONTS:
                        warnings.append(
                            f"{Path(name).name}: mixed CJK run uses latin={latin} ea={ea} text={plain[:40]}"
                        )
    except BadZipFile as exc:
        raise ValueError(f"PPTX 无法读取：{pptx_path}") from exc

    if len(cjk_fonts) > 2:
        warnings.append(
            "当前 PPT 使用了超过两组 CJK 字体对，请检查是否发生了字体替换。"
        )

    return warnings, cjk_fonts


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/check_pptx_fonts.py <pptx_path_or_project_path>", file=sys.stderr)
        return 2

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"路径不存在：{target}", file=sys.stderr)
        return 2

    try:
        pptx_path = resolve_pptx(target)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    try:
        warnings, counts = inspect_pptx(pptx_path)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"PPTX：{pptx_path}")
    if counts:
        print(f"CJK 字体对：{dict(counts)}")
    else:
        print("CJK 字体对：未检测到")

    if warnings:
        for warning in warnings:
            print(f"[WARN] {warning}")
        return 1

    print("OK：未检测到中文字体碎裂警告。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
