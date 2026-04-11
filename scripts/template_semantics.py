#!/usr/bin/env python3
"""Semantic helpers for fixed-template detection and cover-title hygiene."""

from __future__ import annotations

import re
from typing import Any


FIXED_TEMPLATES = {
    "01_cover.svg",
    "02_toc.svg",
    "02_chapter.svg",
    "04_ending.svg",
}

ENDING_KEYWORDS = (
    "结束页",
    "感谢聆听",
    "致谢",
    "thank you",
    "thanks",
)


def normalize_semantic_text(value: str | None) -> str:
    text = re.sub(r"[`*_]+", "", value or "")
    return re.sub(r"\s+", " ", text).strip()


def has_cjk(value: str | None) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", value or ""))


def is_slug_like(value: str | None) -> bool:
    text = normalize_semantic_text(value)
    if not text or has_cjk(text):
        return False
    compact = re.sub(r"\s+", "", text)
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{8,}", compact))


def _pick(entry: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = entry.get(key)
        if value:
            return normalize_semantic_text(str(value))
    return ""


def page_num_value(entry: dict[str, Any]) -> int | None:
    raw = _pick(entry, "page_num", "pageNum", "slide_num")
    if raw.isdigit():
        return int(raw)
    return None


def page_title(entry: dict[str, Any]) -> str:
    return _pick(entry, "页面类型", "title", "page_title", "标题")


def recommended_page_type(entry: dict[str, Any]) -> str:
    return _pick(entry, "推荐页型", "recommended_page_type", "Recommended Page Type")


def page_role(entry: dict[str, Any]) -> str:
    return _pick(entry, "页面角色", "page_role", "Page Role")


def page_intent(entry: dict[str, Any]) -> str:
    return _pick(entry, "页面意图", "page_intent", "Page Intent")


def _cover_signal(entry: dict[str, Any]) -> bool:
    text = " ".join([page_title(entry), recommended_page_type(entry)])
    return "封面" in text


def _toc_signal(entry: dict[str, Any]) -> bool:
    text = " ".join([page_title(entry), recommended_page_type(entry)])
    return "目录" in text


def _chapter_signal(entry: dict[str, Any]) -> bool:
    text = " ".join([page_title(entry), recommended_page_type(entry)])
    return "章节页" in text or text.startswith("章节 /") or text.startswith("章节页 /")


def _ending_signal(entry: dict[str, Any]) -> bool:
    text = " ".join([page_title(entry), recommended_page_type(entry)]).lower()
    return any(keyword in text for keyword in ENDING_KEYWORDS)


def infer_fixed_template(
    entry: dict[str, Any],
    page_num: int | None = None,
    total_pages: int | None = None,
) -> str:
    current_page = page_num if page_num is not None else page_num_value(entry)
    if _cover_signal(entry) and (current_page in {None, 1}):
        return "01_cover.svg"
    if _toc_signal(entry) and (current_page is None or current_page <= 3):
        return "02_toc.svg"
    if _chapter_signal(entry):
        return "02_chapter.svg"
    if _ending_signal(entry) and (total_pages is None or current_page is None or current_page >= total_pages):
        return "04_ending.svg"
    return ""


def fixed_template_matches_entry(
    template_name: str,
    entry: dict[str, Any],
    page_num: int | None = None,
    total_pages: int | None = None,
) -> bool:
    if template_name not in FIXED_TEMPLATES:
        return True

    current_page = page_num if page_num is not None else page_num_value(entry)

    if template_name == "01_cover.svg":
        return _cover_signal(entry) and (current_page in {None, 1})
    if template_name == "02_toc.svg":
        return _toc_signal(entry) and (current_page is None or current_page <= 3)
    if template_name == "02_chapter.svg":
        return _chapter_signal(entry)
    if template_name == "04_ending.svg":
        if not _ending_signal(entry):
            return False
        if total_pages is not None and current_page is not None and current_page < total_pages:
            return False
        return True
    return True

