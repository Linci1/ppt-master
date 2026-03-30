# 长亭品牌 PPT 模板 - 设计规格

> Chaitin Brand Template for ppt-master

## I. 模板信息

| 属性 | 值 |
|------|-----|
| **模板名称** | chaitin |
| **显示名称** | 长亭品牌 |
| **分类** | brand |
| **适用场景** | 企业内训、产品发布、技术分享 |
| **色调** | 科技黑 + 品牌绿 + 青色 |
| **背景模式** | 深色主题 |

---

## II. 视觉规范

### 配色方案

| 角色 | HEX | 用途 |
|------|-----|------|
| **Primary** | `#6BFF85` | 主标题、高亮、编号、装饰条 |
| **Accent** | `#22D3EE` | 辅助强调、渐变过渡 |
| **Secondary** | `#A7F35A` | 标签、次要强调 |
| **Background** | `#05070A` | 主背景（深黑） |
| **Card BG** | `#0D1117` | 卡片背景（深灰） |
| **Text Primary** | `#F5F7FA` | 主文字 |
| **Text Secondary** | `#B4BDC9` | 次要文字 |
| **Text Tertiary** | `#7A8596` | 页码、注释 |
| **Border** | `#213042` | 分隔线、边框 |

### 字体方案

| 用途 | 中文字体 | 英文字体 |
|------|---------|---------|
| 标题 | PingFang SC Semibold | DIN Alternate |
| 正文 | PingFang SC Regular | Arial |
| 注释/页码 | PingFang SC | DIN Alternate |

### 字号层级

| 用途 | 字号 |
|------|------|
| 封面大标题 | 52px |
| 章节编号 | 160px |
| 章节标题 | 42px |
| 页面标题 | 34px |
| 卡片标题 | 24-26px |
| 正文内容 | 18-20px |
| 副标题/注释 | 14-16px |
| 页码 | 14px |

---

## III. 模板占位符

### 封面 (01_cover.svg)

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{{TITLE}}` | 主标题 | 生态伙伴技术培训启动会 |
| `{{SUBTITLE}}` | 副标题 | 暨 3 月首期培训 |
| `{{ENGLISH_SUBTITLE}}` | 英文副标题 | PARTNER TECH ENABLEMENT KICKOFF |
| `{{ORG_INFO}}` | 组织信息 | 长亭生态伙伴培训项目 |
| `{{DATE}}` | 日期 | 2026.03 |

### 目录 (02_toc.svg)

| 占位符 | 说明 |
|--------|------|
| `{{TITLE}}` | 页面标题（默认 "Contents"） |
| `{{ITEM_01_TITLE}}` | 第一章标题 |
| `{{ITEM_01_SUBTITLE}}` | 第一章副标题 |
| `{{ITEM_02_TITLE}}` | 第二章标题 |
| `{{ITEM_02_SUBTITLE}}` | 第二章副标题 |
| `{{ITEM_03_TITLE}}` | 第三章标题 |
| `{{ITEM_03_SUBTITLE}}` | 第三章副标题 |
| `{{ITEM_04_TITLE}}` | 第四章标题 |
| `{{ITEM_04_SUBTITLE}}` | 第四章副标题 |

### 章节页 (03_chapter.svg)

| 占位符 | 说明 |
|--------|------|
| `{{CHAPTER_NUM}}` | 章节编号（01-04） |
| `{{CHAPTER_LABEL}}` | 章节标签（PART ONE/TWO/THREE/FOUR） |
| `{{CHAPTER_TITLE}}` | 章节中文标题 |
| `{{CHAPTER_SUBTITLE}}` | 章节副标题/描述 |

### 内容页 (03_content.svg)

| 占位符 | 说明 |
|--------|------|
| `{{PAGE_TITLE}}` | 页面标题 |
| `{{PAGE_SUBTITLE}}` | 页面副标题（可选） |
| `{{CONTENT_AREA}}` | **Executor 自由渲染区域** |
| `{{PAGE_NUM}}` | 页码 |

### 结尾页 (04_ending.svg)

| 占位符 | 说明 |
|--------|------|
| `{{THANK_YOU}}` | 致谢语（默认"谢谢"） |
| `{{ENGLISH_TEXT}}` | 英文致谢（THANKS FOR YOUR ATTENTION） |
| `{{PROJECT_NAME}}` | 项目名称 |
| `{{PROJECT_SUBTITLE}}` | 项目副标题 |
| `{{DATE}}` | 日期 |

---

## IV. 品牌固定元素

所有页面**必须**包含以下品牌元素：

1. **Chaitin Logo**：左下角，固定尺寸 120x32
2. **底部绿色渐变装饰条**：高度 3px，绿色渐变
3. **页码**：右下角，14px DIN Alternate

---

## V. 布局规范

### 封面
- 模板背景图 + 30% 透明深色遮罩
- 左侧 8px 绿色渐变竖条
- 标题居中偏上

### 目录
- 深色背景（无图）
- 顶部绿色渐变条
- 2x2 网格布局

### 章节页
- 模板章节背景图 + 80% 透明深色遮罩
- 左侧大号章节编号（160px）
- 绿色渐变装饰条

### 内容页
- 深色背景（纯色 #05070A）
- 顶部绿色渐变装饰条
- `{{CONTENT_AREA}}` 区域由 Executor 自由渲染

### 结尾页
- 模板结尾背景图 + 60% 透明深色遮罩
- 居中"谢谢"大字
- 渐变分隔线

---

## VI. 模板文件结构

```
chaitin/
├── design_spec.md       # 本文件
├── 01_cover.svg        # 封面模板
├── 02_toc.svg         # 目录模板
├── 03_chapter.svg     # 章节标题模板
├── 03_content.svg     # 内容页模板
├── 04_ending.svg      # 结尾模板
└── assets/
    ├── bg_cover.jpeg        # 封面背景
    ├── bg_chapter.jpeg      # 章节背景
    ├── bg_ending.jpeg       # 结尾背景
    ├── bg_content_dark.png  # 内容页深色背景
    └── chaitin_logo.png    # 品牌 Logo
```

---

## VII. 使用说明

1. **模板选择**：用户选择"长亭品牌"作为模板
2. **内容填充**：Executor 读取内容，按照占位符填入
3. **内容页渲染**：Executor 在 `{{CONTENT_AREA}}` 区域自由渲染 SVG 内容
4. **自动添加品牌元素**：Logo、装饰条、页码自动添加

---

*最后更新：2026-03-30*
