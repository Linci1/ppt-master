# SVG 图标库

该目录提供 `ppt-master` 可直接使用的 SVG 图标资源，可嵌入生成的 SVG 页面中。

> **图标来源**：[SVG Repo](https://www.svgrepo.com/)（开源免费 SVG 图标库）

- **完整索引**：`FULL_INDEX.md`（按需浏览）
- **JSON 索引**：`icons_index.json`（适合程序检索）

---

## 使用方式

### 方法一：占位符引用 + 后处理嵌入（推荐）

在生成阶段先写入简单占位符：

```xml
<use data-icon="rocket" x="100" y="200" width="48" height="48" fill="#0076A8"/>
<use data-icon="chart-bar" x="200" y="200" width="48" height="48" fill="#FF6B35"/>
```

**常用属性**：

- `data-icon`：图标名（对应文件名，不含 `.svg`）
- `x`, `y`：位置
- `width`, `height`：尺寸（基础尺寸 16px；48 代表约 3 倍）
- `fill`：颜色

生成后再运行批量嵌入工具：

```bash
python3 scripts/embed_icons.py svg_output/*.svg
```

### 方法二：直接复制嵌入

```xml
<g transform="translate(100, 200) scale(3)" fill="#0076A8">
  <!-- 从 rocket.svg 复制 path 内容 -->
  <path d="M10 16L12 14V10L13.6569 8.34314..."/>
</g>
```

**常见缩放**：`scale(2)` = 32px，`scale(3)` = 48px，`scale(4)` = 64px

---

## 常用图标速查

| 分类 | 图标 |
|------|------|
| 数据与图表 | `chart-bar` `chart-line` `chart-pie` `arrow-trend-up` `database` |
| 状态与反馈 | `circle-checkmark` `circle-x` `triangle-exclamation` `circle-info` |
| 用户与组织 | `user` `users` `building` `group` |
| 导航与箭头 | `arrow-up` `arrow-down` `arrow-left` `arrow-right` |
| 商务与金融 | `dollar` `wallet` `briefcase` `shopping-cart` |
| 工具与动作 | `cog` `pencil` `magnifying-glass` `trash` |
| 时间与排期 | `clock` `calendar` `stopwatch` |
| 文件与文档 | `file` `folder` `clipboard` `copy` |
| 目标与安全 | `target` `flag` `shield` `lock-closed` |
| 创意与灵感 | `lightbulb` `rocket` `sparkles` `star` |

---

## 设计规格

| 参数 | 值 |
|------|----|
| viewBox | `0 0 16 16` |
| 基础尺寸 | 16 x 16 px |
| 风格 | Solid（实心填充） |

---

**图标数量**：640+  
**完整列表**：`FULL_INDEX.md`
