# ppt-master 使用指南

> AI-driven PPT 生成工具，支持将文档转换为高质量演示文稿

---

## 安装

### 1. 解压
```bash
cd ~/Downloads
tar -xzvf ppt-master.tar.gz
mv ppt-master-pkg ppt-master   # 重命名为你喜欢的名字
```

### 2. 找一个目录放进去
```bash
# 方式 A：放到常用工具目录
mv ppt-master ~/tools/ppt-master

# 方式 B：放到项目目录
mv ppt-master ~/myprojects/ppt-master

# 方式 C：放到 Claude skills 目录（如果你用 Claude Code）
mv ppt-master ~/.claude/skills/ppt-master
```

### 3. 安装 Python 依赖
```bash
# 进入目录
cd ~/tools/ppt-master   # 改成你的实际路径

# 安装依赖
pip install -r requirements.txt
```

### 4. (可选) 安装 pandoc（用于转换 Word/HTML 等文档）
```bash
# macOS
brew install pandoc

# Ubuntu
sudo apt install pandoc

# Windows
# https://pandoc.org/installing.html
```

---

## 快速开始

### 方式一：Claude Code 中使用
```
/learn ppt-master
/ppt-master
```

### 方式二：命令行使用
```bash
# 初始化项目
python3 {你的路径}/ppt-master/scripts/project_manager.py init my_ppt --format ppt169

# 导入源文件（Word/PDF 等）
python3 {你的路径}/ppt-master/scripts/project_manager.py import-sources my_project 文档.docx --move

# ...后续在 Claude Code 中完成设计和生成
```

---

## 目录结构

```
ppt-master/
├── SKILL.md           # 完整技能文档（Claude Code 使用）
├── requirements.txt   # Python 依赖
├── scripts/           # 核心脚本
│   ├── project_manager.py   # 项目管理
│   ├── doc_to_md.py         # Word → Markdown
│   ├── pdf_to_md.py          # PDF → Markdown
│   ├── svg_to_pptx.py        # SVG → PPTX
│   ├── finalize_svg.py       # SVG 后处理
│   └── ...
├── templates/         # 模板库
│   ├── layouts/       # 页面布局（含长亭通用墨绿色、长亭安服）
│   ├── charts/        # 图表模板
│   └── icons/         # 图标库
├── references/       # 角色定义文档
├── workflows/        # 工作流文档
└── examples/         # 示例
    ├── eco_partner_chaitin_example/  # 生态伙伴培训
    └── pep_fault_spec_example/       # PEP故障规范
```

---

## 模板说明

### 长亭通用墨绿色
位于 `templates/layouts/chaitin/`

| 文件 | 说明 |
|------|------|
| `01_cover.svg` | 封面 |
| `02_toc.svg` | 目录 |
| `03_chapter.svg` | 章节页 |
| `03_content.svg` | 内容页（可自由渲染） |
| `04_ending.svg` | 结尾 |
| `assets/` | 背景图、Logo |
| `design_spec.md` | 设计规格 |

**配色**：科技绿 `#6BFF85` + 青色 `#22D3EE` + 深黑背景 `#05070A`

---

## 依赖

| 依赖 | 用途 |
|------|------|
| python-pptx | PPTX 读写 |
| svglib + reportlab | SVG 处理 |
| PyMuPDF | PDF 解析 |
| Pillow | 图片处理 |
| requests + beautifulsoup4 | 网页解析 |
| google-genai / openai | AI 图片生成（可选） |

---

## 常见问题

**Q: 找不到脚本？**
A: 检查 `scripts/` 目录是否完整，确保 `project_manager.py` 存在。

**Q: 图片无法显示？**
A: 运行 `finalize_svg.py`，它会自动嵌入图片。

**Q: 字体显示异常？**
A: Linux/Windows 需安装 `PingFang SC` 或 `Microsoft YaHei`。

**Q: Word 文档无法转换？**
A: 安装 pandoc：`brew install pandoc`（macOS）

---

## 技术支持

有问题请联系长亭科技生态运营团队。
