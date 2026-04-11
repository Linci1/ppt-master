# 行业包

> 用途：把“行业表达逻辑、术语规范、页型偏好、复杂图形规则、QA 规则”从模板中拆出来，形成可复用的行业能力层。

## 为什么要有行业包

- 模板负责品牌骨架与视觉稳定性
- 行业包负责内容怎么讲、复杂页怎么建模、术语怎么用
- 新案例吸收后，很多规律应先进入行业包，而不是直接改模板

## 推荐结构

```text
domain_packs/
└── <domain>/
    ├── domain_profile.md
    ├── story_patterns.md
    ├── page_logic.md
    ├── diagram_logic.md
    ├── terminology_rules.md
    ├── qa_rules.md
    └── rewrite_rules.md
```
