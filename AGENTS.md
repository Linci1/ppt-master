# AGENTS.md

这是面向通用 AI 代理的仓库级入口说明。凡是在本仓库内执行 PPT 相关任务，**必须先读取** `/Users/ciondlin/skills/ppt-master/SKILL.md`，再决定如何进入正式链路。

## 项目概览

`ppt-master` 不再只是“文档转 PPT 工具”，而是一个带总控前置层的 PPT Agent 系统：

- 先判断任务属于 `learn / plan / produce / execute / run / improve` 哪一种
- 再进入需求澄清、案例吸收、正式生成或复盘沉淀
- 正式生成阶段仍严格遵循 `Strategist -> Image_Generator -> Executor -> QA -> Export`

核心链路：

```text
历史案例 -> learn 入库 -> 案例蒸馏
新建 PPT -> /plan 澄清 -> 规划产物 -> produce -> execute -> run -> Strategist / Executor -> QA -> Export
已有项目 -> improve 复盘 -> 学习回写建议
```

当前推荐把它理解成三层：

- 规划层：`new / plan / produce`
- 执行准备层：`execute / run`
- 正式出稿层：`Strategist / Executor / QA / Export`

对用户而言，最关键的明确指令节点有 4 个：

1. 立项时给出行业、场景、受众、目标、展示重点
2. `/plan` 追问后补齐缺失信息
3. 模板推荐出来后确认模板、页数、复杂页比例、品牌要求
4. 成品复盘时把问题反馈给 `improve`

除这几个节点外，`produce -> execute -> run` 在条件满足时应尽量连续自动推进，不要要求用户机械地一轮轮重复“继续”。

## 强制执行要求

- 在正式进入 PPT 主链路前，先读 `/Users/ciondlin/skills/ppt-master/workflows/ppt-agent.md`
- 只要是“新做一份 PPT”，默认先进入 `/plan`，不要直接跳到 SVG 生成
- 正式生成阶段必须严格串行，禁止跨阶段打包执行
- Executor 阶段的 SVG 必须由当前主代理连续生成，禁止拆给子代理逐页并行生成
- 若模板有固定骨架、品牌元素或 `qa_profile.md`，这些保护区规则必须被强制执行

## 推荐命令

### 统一 Agent 入口

```bash
python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py new <project_name> --industry <industry> --scenario <scenario> --audience <audience> --goal <goal> --format ppt169 --source <file_or_url>
python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py plan <project_path> --industry <industry> --scenario <scenario> --audience <audience> --goal <goal> --source <file_or_url>
python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py produce <project_path>
python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py execute <project_path>
python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py run <project_path>
python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py learn <pptx_file> --domain <domain> --copy-source --distill
python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py improve <project_path> --findings <findings_file>
python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py improve <project_path>
python3 /Users/ciondlin/skills/ppt-master/scripts/ppt_agent.py status <project_path>
```

### 底层项目管理

```bash
python3 /Users/ciondlin/skills/ppt-master/scripts/project_manager.py init <project_name> --format ppt169
python3 /Users/ciondlin/skills/ppt-master/scripts/project_manager.py import-sources <project_path> <source_files_or_URLs...> --move
python3 /Users/ciondlin/skills/ppt-master/scripts/project_manager.py bootstrap-agent <project_path> --industry <industry> --scenario <scenario> --audience <audience> --goal <goal>
python3 /Users/ciondlin/skills/ppt-master/scripts/project_manager.py validate <project_path>
python3 /Users/ciondlin/skills/ppt-master/scripts/project_manager.py info <project_path>
```

### 后处理主链路

```bash
python3 /Users/ciondlin/skills/ppt-master/scripts/total_md_split.py <project_path>
python3 /Users/ciondlin/skills/ppt-master/scripts/finalize_svg.py <project_path>
python3 /Users/ciondlin/skills/ppt-master/scripts/svg_to_pptx.py <project_path> -s final
```

## 目录职责

- `/Users/ciondlin/skills/ppt-master/SKILL.md`：核心流程规则源
- `/Users/ciondlin/skills/ppt-master/workflows/ppt-agent.md`：总控模式说明
- `/Users/ciondlin/skills/ppt-master/scripts/`：脚本入口
- `/Users/ciondlin/skills/ppt-master/references/`：提问模板、角色说明、规范参考
- `/Users/ciondlin/skills/ppt-master/case_library/`：历史 PPT 案例库
- `/Users/ciondlin/skills/ppt-master/domain_packs/`：行业表达、复杂页逻辑、QA 规则
- `/Users/ciondlin/skills/ppt-master/templates/`：模板、图表、图标等资产

## 技术边界

- 本仓库是 workflow / skill 仓库，不要默认套用常规软件项目的脚手架约定
- 不要默认要求 `.worktrees/`、测试工程、分支流水线等结构，除非用户明确提出
- 如果通用编程型规则与本仓库的 PPT 工作流冲突，优先遵循 `SKILL.md` 与本文件
- 当前系统已具备 Agent 骨架，但正式 SVG 执行进度与软性内容 QA 仍不是百分百自动闭环；不要误报为“全自动一键成品”

## SVG 兼容约束

禁用特性：

`clipPath`、`mask`、`<style>`、`class`、外部 CSS、`<foreignObject>`、`textPath`、`@font-face`、`<animate*>`、`<script>`、`marker-end`、`<iframe>`、`<symbol>+<use>`

兼容替代：

- `rgba()` -> `fill-opacity` / `stroke-opacity`
- `<g opacity>` -> 把透明度下沉到子元素
- `<image opacity>` -> 改用覆盖蒙层
- `marker-end` 箭头 -> 用 `<polygon>` 手工绘制箭头

## 导出提醒

- 不要用 `cp` 代替 `finalize_svg.py`
- 不要直接从 `svg_output/` 导出，必须从 `svg_final/` 导出
- 不要把多个后处理步骤塞进一条命令里连续执行
