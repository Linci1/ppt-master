# 长亭安服 PPT 模板 - 设计规格

> Chaitin Security Service Template for ppt-master

## I. 模板信息

| 属性 | 值 |
|------|-----|
| **模板名称** | chaitin_anfu |
| **显示名称** | 长亭安服 |
| **分类** | brand |
| **适用场景** | 安服业务汇报、解决方案展示、攻防演练报告、安全运营汇报 |
| **色调** | 白底 + 品牌绿 + 深色过渡页 |
| **背景模式** | 混合主题（封面/章节/结尾深色 + 内容页白色） |

---

## II. 视觉规范

### 配色方案

| 角色 | HEX | 用途 |
|------|-----|------|
| **Primary (品牌绿)** | `#7BBD4A` | 页面标题、装饰条、强调 |
| **Accent (亮绿)** | `#65C133` | 目录编号、编号文字 |
| **Background (白)** | `#FFFFFF` | 内容页主背景 |
| **Dark BG** | `#000000` | 封面/章节/结尾页遮罩 |
| **Text Primary** | `#1A1A1A` | 内容页主文字（深黑） |
| **Text Light** | `#FFFFFF` | 深色页主文字 |
| **Text Secondary** | `#666666` | 副标题、描述文字 |
| **Text Tertiary** | `#A6A6A6` | 页码、注释、标签 |
| **Border/Divider** | `#E0E0E0` | 分隔线、边框 |
| **Card BG (内容页)** | `#F5F7FA` | 卡片背景（浅灰） |

### 字体方案

| 用途 | 中文字体 | 英文字体 |
|------|---------|---------|
| 标题 | PingFang SC / Microsoft YaHei | +mn-lt / Arial |
| 正文 | Microsoft YaHei | Arial |
| 编号 | - | Arial / DIN Alternate |
| 注释/页码 | PingFang SC | Arial / DIN Alternate |

### 字号层级

| 用途 | 字号 | Weight |
|------|------|--------|
| 封面主标题 | 54px | Bold |
| 封面副标题 | 32px | Bold |
| 封面 Slogan | 22px | Regular |
| 章节编号 | 126px | Bold |
| 章节标题 | 48px | Bold |
| 章节副标题 | 20px | Regular |
| 目录条目 | 32px | Bold |
| 内容页标题 | 28px | Bold |
| 内容页正文 | 18-20px | Regular |
| 卡片标题 | 22-24px | SemiBold |
| 注释/标签 | 14-16px | Regular |
| 页码 | 12px | Regular |
| 结尾致谢 | 96px | Bold |
| 结尾 Slogan | 24px | Regular |

---

## III. 模板占位符

### 封面 (01_cover.svg)

| 占位符 | 说明 | 示例 |
|--------|------|------|
| `{{TITLE}}` | 主标题（居中） | 长亭科技 |
| `{{SUBTITLE}}` | 副标题（居中） | 引领智能安全运营 |
| `{{SLOGAN}}` | 品牌标语 | 知攻善防 智能安全 |

### 目录 (02_toc.svg)

| 占位符 | 说明 |
|--------|------|
| `{{ITEM_01_NUM}}` | 第一章编号（01） |
| `{{ITEM_01_TITLE}}` | 第一章标题 |
| `{{ITEM_02_NUM}}` | 第二章编号（02） |
| `{{ITEM_02_TITLE}}` | 第二章标题 |
| `{{ITEM_03_NUM}}` | 第三章编号（03） |
| `{{ITEM_03_TITLE}}` | 第三章标题 |
| `{{ITEM_04_SECTION}}` | 可选第四章区块（留空则隐藏） |

### 章节页 (02_chapter.svg)

| 占位符 | 说明 |
|--------|------|
| `{{CHAPTER_NUM}}` | 章节编号（01-04） |
| `{{CHAPTER_TITLE}}` | 章节标题 |
| `{{CHAPTER_SUBTITLE}}` | 章节副标题/描述（可选） |

### 内容页 (03_content.svg)

| 占位符 | 说明 |
|--------|------|
| `{{PAGE_TITLE}}` | 页面标题（品牌绿） |
| `{{CONTENT_AREA}}` | **Executor 自由渲染区域** |
| `{{PAGE_NUM}}` | 页码 |

内容页为 brand-locked flex-body：
- **brand_locked**: 顶部绿条、左上标题、右上Logo、底部分隔线、页码 — 不可修改
- **body_safe_region**: x=34, y=90, w=1212, h=580 — Executor 可自由渲染
- **allowed_native_page_types**: ppt-master 所有原生页型（KPI卡片、流程图、表格、时间线等）
- **forbidden_actions**: 修改品牌锁定元素、删除Logo、改变标题颜色

### 结尾页 (04_ending.svg)

| 占位符 | 说明 |
|--------|------|
| `{{THANK_YOU}}` | 致谢语（默认 "Thanks"） |
| `{{SLOGAN}}` | 品牌标语（默认 "知攻善防 智能安全"） |

---

## IV. 品牌固定元素

### 深色页（封面/章节/结尾）
1. **深色科技背景图**: `bg_dark_tech.jpeg` — 三种页面共用同一张背景
2. **浅色 Logo**: `chaitin_logo_light.png` — 封面右下角 / 结尾页右上角
3. **绿色装饰线**: `#7BBD4A` — 章节页标题下方 / 结尾页居中

### 内容页
1. **顶部绿色装饰条**: 高度 4px，品牌绿 `#7BBD4A`
2. **页面标题**: 左上角，品牌绿 `#7BBD4A`，28px Bold
3. **深色 Logo**: `chaitin_logo_dark.png` — 右上角，113x31
4. **底部绿色装饰条**: 高度 4px
5. **页码**: 右下角，12px，灰色 `#A6A6A6`

---

## V. 布局规范

### 封面
- 深色科技背景图 + 45% 黑色遮罩
- 标题组垂直居中偏上（y=280/340/400）
- 浅色 Logo 右下角

### 目录
- 白色背景
- 顶部/底部绿色装饰条
- 条目居中纵列排列（x≈448-520, 间距≈112px）

### 章节页
- 深色科技背景图 + 50% 黑色遮罩
- 左侧超大编号（126px）
- 右侧章节标题（48px）
- 标题下方绿色短装饰线

### 内容页
- 白色背景
- 顶部/底部绿色装饰条（4px）
- 左上绿色标题 + 右上Logo
- body_safe_region: x=34 y=90 w=1212 h=580
- Executor 在安全区域内自由渲染

### 结尾页
- 深色科技背景图 + 45% 黑色遮罩
- 居中 "Thanks" 大字（96px）
- Slogan + 绿色装饰线
- 浅色 Logo 右上角

---

## VI. 模板文件结构

```
chaitin_anfu/
├── design_spec.md           # 本文件
├── 01_cover.svg            # 封面模板
├── 02_toc.svg              # 目录模板
├── 02_chapter.svg          # 章节标题模板
├── 03_content.svg          # 内容页模板（brand-locked flex-body）
├── 04_ending.svg           # 结尾模板
├── bg_dark_tech.jpeg       # 深色科技背景图（封面/章节/结尾共用）
├── chaitin_logo_dark.png   # 深色 Logo（用于白色内容页）
└── chaitin_logo_light.png  # 浅色 Logo（用于深色页面）
```

---

## VII. 与 chaitin 模板的区别

| 维度 | chaitin | chaitin_anfu |
|------|---------|-------------|
| 背景模式 | 全深色 | 混合（深色过渡页 + 白色内容页） |
| 主色 | `#6BFF85` 荧光绿 | `#7BBD4A` 品牌绿 |
| 内容页 | 深黑 `#05070A` | 白色 `#FFFFFF` |
| 封面布局 | 左对齐 | 居中 |
| 目录布局 | 2x2 网格 | 居中纵列 |
| 章节页 | 左对齐编号+标题 | 左编号右标题 |
| Logo 位置 | 左下角 | 内容页右上 / 封面右下 / 结尾右上 |
| 背景图 | 三张不同 | 一张共用 |

---

*最后更新：2026-04-20*
