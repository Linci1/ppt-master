# SVG 图表模板库（33 类）

该目录提供 `ppt-master` 内置的标准 SVG 图表模板，可作为图表页选型与结构参考。

- **完整索引**：`charts/README.md`（适合人工浏览）
- **JSON 索引**：`charts/charts_index.json`（适合 AI / 程序读取，推荐优先使用）

> **推荐读取方式**：生成图表页前，优先读取 `charts_index.json` 做候选筛选；如需快速人工对比，可阅读本说明文件。

## 快速选择

| 我想表达... | 推荐模板 | 文件名 |
|-------------|----------|--------|
| 关键数值指标 | KPI 卡片 | `kpi_cards.svg` |
| 类别对比 | 柱状图 | `bar_chart.svg` |
| 长标签排名 | 横向柱状图 | `horizontal_bar_chart.svg` |
| 多序列对比 | 分组柱状图 | `grouped_bar_chart.svg` |
| 时间趋势 | 折线图 | `line_chart.svg` |
| 累计趋势 | 面积图 | `area_chart.svg` |
| 比例构成 | 饼图 / 环形图 | `pie_chart.svg` / `donut_chart.svg` |
| 目标完成率 | 进度条 / 仪表盘 | `progress_bar_chart.svg` / `gauge_chart.svg` |
| 漏斗转化 | 漏斗图 | `funnel_chart.svg` |
| 项目排期 | 甘特图 | `gantt_chart.svg` |
| 里程碑事件 | 时间线 | `timeline.svg` |
| 多维评估 | 雷达图 | `radar_chart.svg` |
| 双向对比 | 蝴蝶图 | `butterfly_chart.svg` |
| 增量拆解 | 瀑布图 | `waterfall_chart.svg` |
| 流向关系 | 桑基图 | `sankey_chart.svg` |
| 战略分析 | SWOT / 波特五力 | `swot_analysis.svg` / `porter_five_forces.svg` |
| 象限分析 | 2x2 矩阵 | `matrix_2x2.svg` |

## 图表分类索引

### 一、对比类

| 文件名 | 用途 | 适用场景 |
|--------|------|----------|
| `bar_chart.svg` | 纵向柱状对比（3-8 根） | 销售对比、区域排名 |
| `horizontal_bar_chart.svg` | 横向柱状排名（5-12 项） | 品牌排名、满意度评分 |
| `grouped_bar_chart.svg` | 多序列分组对比 | 产品线季度对比、同比/环比 |
| `stacked_bar_chart.svg` | 堆叠构成对比 | 收入构成、市场份额变化 |
| `butterfly_chart.svg` | 双向对比 | 人口金字塔、A/B 对比、收支对照 |
| `bullet_chart.svg` | 目标 vs 实际 | KPI 达成、绩效评估 |
| `dumbbell_chart.svg` | 多维评分对比 | 竞品分析、综合指数 |
| `waterfall_chart.svg` | 增量拆解 | 利润分解、预算偏差 |

### 二、趋势类

| 文件名 | 用途 | 适用场景 |
|--------|------|----------|
| `line_chart.svg` | 折线趋势（支持多线） | 时间序列、增长趋势 |
| `area_chart.svg` | 面积累计趋势 | 流量变化、用户增长 |
| `stacked_area_chart.svg` | 多序列堆叠趋势 | 收入来源、流量来源变化 |
| `dual_axis_line_chart.svg` | 双 Y 轴异单位对比 | 销售额 vs 利润率、流量 vs 转化率 |

### 三、比例类

| 文件名 | 用途 | 适用场景 |
|--------|------|----------|
| `pie_chart.svg` | 基础比例（3-6 扇区） | 市场份额、预算分配 |
| `donut_chart.svg` | 环形比例（带中心数据） | 结构占比、分类构成 |
| `treemap_chart.svg` | 层级面积比例 | 预算分布、市场份额结构 |

### 四、指标类

| 文件名 | 用途 | 适用场景 |
|--------|------|----------|
| `kpi_cards.svg` | 关键指标卡片（2x2 / 1x4） | 财务总览、数据看板 |
| `gauge_chart.svg` | 仪表盘完成率 | KPI 完成、绩效监控 |
| `progress_bar_chart.svg` | 多项进度条 | OKR 进度、项目完成情况 |

### 五、分析类

| 文件名 | 用途 | 适用场景 |
|--------|------|----------|
| `radar_chart.svg` | 多维评估（4-8 维） | 能力评估、竞品对比 |
| `scatter_chart.svg` | 相关性 / 分布 | 投入产出分析、价格需求分析 |
| `funnel_chart.svg` | 漏斗转化（3-5 阶段） | 销售漏斗、用户转化 |
| `matrix_2x2.svg` | 四象限分析 | BCG 矩阵、优先级分析 |
| `bubble_chart.svg` | 三维气泡图（X/Y/Size） | 市场规模 vs 增速 vs 份额 |
| `heatmap_chart.svg` | 热力矩阵 | 用户活跃时段、相关矩阵 |
| `pareto_chart.svg` | 二八分析 | 质量归因、销售贡献 |
| `box_plot_chart.svg` | 箱线分布 | 薪酬分布、质量控制 |

### 六、项目管理 / 关系类

| 文件名 | 用途 | 适用场景 |
|--------|------|----------|
| `gantt_chart.svg` | 甘特排期（6-12 项任务） | 项目管理、产品路线图 |
| `timeline.svg` | 时间线节点（3-8 个） | 里程碑、历史演进 |
| `process_flow.svg` | 流程步骤图 | 业务流程、操作指引 |
| `org_chart.svg` | 组织结构图（2-4 层） | 公司结构、汇报关系 |
| `sankey_chart.svg` | 三层流向图 | 预算流向、用户转化路径 |

### 七、战略框架类

| 文件名 | 用途 | 适用场景 |
|--------|------|----------|
| `swot_analysis.svg` | SWOT 四象限分析 | 战略规划、竞争分析 |
| `porter_five_forces.svg` | 波特五力模型 | 行业分析、市场进入评估 |
