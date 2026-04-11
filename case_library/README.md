# 案例库

> 用途：存放历史优秀 PPT 素材案例及其结构化蒸馏结果。

## 设计原则

- 原始案例先入库，再蒸馏，再决定是否合并进模板或行业包
- 不把单个案例直接写死进模板
- 用 `case pattern / domain rule / template rule` 三层分类避免规则污染

## 目录约定

```text
case_library/
├── index.json
└── <domain>/
    └── <case_name>/
        ├── source_files/
        ├── analysis.json
        ├── case_meta.md
        ├── deck_outline.md
        ├── page_patterns.md
        ├── diagram_patterns.md
        ├── writing_logic.md
        ├── soft_issue_risks.md
        └── merge_suggestions.md
```

## 使用方式

1. 用 `scripts/ingest_reference_ppt.py` 建案例目录
2. 用 `scripts/distill_case_patterns.py` 提取跨案例共性
3. 人工确认后，再决定是否写回模板或行业包
