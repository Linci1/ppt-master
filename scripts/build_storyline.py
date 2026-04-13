#!/usr/bin/env python3
"""Build storyline and page outline from project brief and source materials."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

PLACEHOLDER_PATTERNS = ("待确认", "待补齐", "待补充", "待选择")
SECURITY_KEYWORDS = ("安服", "攻防", "hw", "红队", "渗透", "security_service", "长亭")


@dataclass
class PagePlan:
    section: str
    page_type: str
    page_role: str
    page_intent: str
    proof_goal: str
    core_judgment: str
    evidence: str
    recommended_page_type: str
    is_complex: bool
    note: str = ""


@dataclass
class PageCandidate:
    plan: PagePlan
    mandatory: bool = True
    enabled: bool = True
    optional_rank: int = 99


def extract_brief_field(text: str, label: str) -> str:
    match = re.search(rf"(?m)^- {re.escape(label)}：(.+)$", text)
    return match.group(1).strip() if match else ""


def normalize_text(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value or "")
    return cleaned.strip()


def contains_placeholder(value: str) -> bool:
    return any(token in (value or "") for token in PLACEHOLDER_PATTERNS)


def parse_page_range(value: str) -> tuple[int | None, int | None]:
    text = normalize_text(value)
    if not text or contains_placeholder(text):
        return None, None

    match = re.search(r"(\d+)\s*[-~～至到—]+\s*(\d+)", text)
    if match:
        low = int(match.group(1))
        high = int(match.group(2))
        return (low, high) if low <= high else (high, low)

    match = re.search(r"不少于\s*(\d+)", text)
    if match:
        low = int(match.group(1))
        return low, low + 4

    match = re.search(r"不超过\s*(\d+)", text)
    if match:
        high = int(match.group(1))
        return max(6, high - 4), high

    match = re.search(r"约\s*(\d+)", text) or re.search(r"(\d+)", text)
    if match:
        number = int(match.group(1))
        return number, number

    return None, None


def choose_target_page_count(page_range_text: str, is_security_service: bool) -> int:
    low, high = parse_page_range(page_range_text)
    if low is None or high is None:
        return 26 if is_security_service else 12
    if low == high:
        return low
    midpoint = round((low + high) / 2)
    if is_security_service:
        return min(high, midpoint + 1)
    return midpoint


def load_source_text(project_dir: Path) -> str:
    source_dir = project_dir / "sources"
    if not source_dir.exists():
        return ""
    parts: list[str] = []
    for path in sorted(source_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        parts.append(f"\n<!-- source: {path.name} -->\n{text}\n")
    return "\n".join(parts)


def parse_headings(markdown: str) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    for match in re.finditer(r"(?m)^(#{1,3})\s+(.+?)\s*$", markdown):
        level = len(match.group(1))
        title = normalize_text(match.group(2))
        headings.append((level, title))
    return headings


def unique_items(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        cleaned = normalize_text(item)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result


def find_heading_children(
    headings: list[tuple[int, str]],
    parent_keywords: tuple[str, ...],
    *,
    child_level: int | None = None,
) -> list[str]:
    start_index = -1
    parent_level = 0
    for index, (level, title) in enumerate(headings):
        if all(keyword in title for keyword in parent_keywords):
            start_index = index
            parent_level = level
            break

    if start_index < 0:
        return []

    children: list[str] = []
    for level, title in headings[start_index + 1 :]:
        if level <= parent_level:
            break
        if child_level is None or level == child_level:
            children.append(title)
    return unique_items(children)


def titles_by_keywords(
    headings: list[tuple[int, str]],
    keywords: tuple[str, ...],
    *,
    level: int | None = None,
) -> list[str]:
    results: list[str] = []
    for current_level, title in headings:
        if level is not None and current_level != level:
            continue
        if any(keyword in title for keyword in keywords):
            results.append(title)
    return unique_items(results)


def filter_items_by_keywords(items: list[str], keywords: tuple[str, ...]) -> list[str]:
    return unique_items([item for item in items if any(keyword in item for keyword in keywords)])


def summarize_titles(titles: list[str], fallback: str, limit: int = 3) -> str:
    items = [normalize_text(item) for item in titles if normalize_text(item)]
    if not items:
        return fallback
    selected = items[:limit]
    suffix = " 等" if len(items) > limit else ""
    return "；".join(selected) + suffix


def pick_first_matching(titles: list[str], keywords: tuple[str, ...], fallback: str) -> str:
    for title in titles:
        if all(keyword in title for keyword in keywords):
            return title
    for title in titles:
        if any(keyword in title for keyword in keywords):
            return title
    return fallback


def collect_source_profile(project_dir: Path) -> dict[str, object]:
    markdown = load_source_text(project_dir)
    headings = parse_headings(markdown)

    summary_titles = titles_by_keywords(headings, ("整体回顾", "成果总结", "获取重要成果"))
    attack_titles = titles_by_keywords(headings, ("攻击路径", "攻击概述", "突破"))
    issue_titles = find_heading_children(headings, ("问题分析",), child_level=3)
    remediation_titles = find_heading_children(headings, ("整改建议",), child_level=3)
    external_cases = find_heading_children(headings, ("附录", "互联网侧安全威胁详情"), child_level=2)
    internal_cases = find_heading_children(headings, ("附录", "互联网突破内网安全威胁详情"), child_level=2)
    phishing_cases = find_heading_children(headings, ("附录", "社工钓鱼详情"), child_level=2)
    cleanup_titles = titles_by_keywords(headings, ("创建账号与遗留文件信息清理",))

    return {
        "markdown": markdown,
        "headings": headings,
        "summary_titles": summary_titles,
        "attack_titles": attack_titles,
        "issue_titles": issue_titles,
        "remediation_titles": remediation_titles,
        "external_cases": external_cases,
        "internal_cases": internal_cases,
        "phishing_cases": phishing_cases,
        "cleanup_titles": cleanup_titles,
        "has_phishing": bool(phishing_cases or titles_by_keywords(headings, ("钓鱼", "社工"))),
        "has_cleanup": bool(cleanup_titles),
        "image_count": len(re.findall(r"(?m)^!\[", markdown)),
    }


def detect_sections(text: str) -> list[str]:
    lower = text.lower()
    if any(keyword in lower for keyword in ["安服", "hw", "攻防", "security", "安全运营"]):
        return ["背景与目标", "风险结构总览", "关键案例 / 攻击链", "治理与闭环", "能力背书", "结束页"]
    if any(keyword in lower for keyword in ["金融", "bank", "finance"]):
        return ["背景", "问题定义", "方案结构", "价值证明", "实施路径", "结束页"]
    return ["背景", "核心观点", "重点拆解", "案例 / 数据", "建议 / 收束", "结束页"]


def build_security_service_candidates(brief_text: str, profile: dict[str, object]) -> list[PageCandidate]:
    goal = extract_brief_field(brief_text, "核心目标") or "让客户快速理解结果、接受风险判断并推进整改。"
    audience = extract_brief_field(brief_text, "主要受众") or "客户管理层与技术团队"
    desired_judgment = extract_brief_field(brief_text, "期待对方形成的判断") or "本次攻防结果可信，关键风险结论成立。"
    desired_action = extract_brief_field(brief_text, "期待对方采取的动作") or "按优先级推进整改闭环。"
    audience_focus = extract_brief_field(brief_text, "受众更关心") or "管理层看结果与优先级，技术团队看链路与证据。"
    brand_mandatories = extract_brief_field(brief_text, "必须固定的品牌元素") or "保留长亭安服模板固定元素与 Logo。"

    summary_titles = profile["summary_titles"]  # type: ignore[index]
    attack_titles = profile["attack_titles"]  # type: ignore[index]
    issue_titles = profile["issue_titles"]  # type: ignore[index]
    remediation_titles = profile["remediation_titles"]  # type: ignore[index]
    external_cases = profile["external_cases"]  # type: ignore[index]
    internal_cases = profile["internal_cases"]  # type: ignore[index]
    phishing_cases = profile["phishing_cases"]  # type: ignore[index]
    cleanup_titles = profile["cleanup_titles"]  # type: ignore[index]
    image_count = int(profile["image_count"])  # type: ignore[index]
    has_phishing = bool(profile["has_phishing"])
    has_cleanup = bool(profile["has_cleanup"])

    summary_evidence = summarize_titles(summary_titles, "整体回顾及成果总结；获取重要成果")
    attack_evidence = summarize_titles(attack_titles, "整体攻击路径分析；互联网侧攻击路径概述；内网侧攻击路径概述")
    issue_evidence = summarize_titles(issue_titles, "互联网侧系统安全检测与防护待加强；内网系统异常登陆行为审计问题；内网服务器存在通用口令问题")
    remediation_evidence = summarize_titles(remediation_titles, "定期开展互联网侧安全检测；及时修补系统漏洞；强化账号密码管理")
    external_evidence = summarize_titles(external_cases, "互联网侧高危漏洞与未授权访问案例")
    internal_evidence = summarize_titles(internal_cases, "互联网突破内网与后台权限类案例")
    phishing_evidence = summarize_titles(phishing_cases, "采招人员钓鱼；客服平台人员钓鱼；HR 人员钓鱼")
    cleanup_evidence = summarize_titles(cleanup_titles, "创建账号与遗留文件信息清理")
    evidence_assets = f"{image_count} 张原始截图/图片素材" if image_count else "文档中的原始截图、日志与案例描述"

    internet_issue_title = pick_first_matching(
        issue_titles,
        ("互联网侧",),
        "互联网侧系统安全检测与防护待加强",
    )
    internal_issue_title = pick_first_matching(
        issue_titles,
        ("内网", "审计"),
        "内网系统异常登陆行为审计与高危端口限源问题",
    )
    credential_issue_title = pick_first_matching(
        issue_titles,
        ("通用口令",),
        "内网服务器存在通用口令和通用密码问题",
    )
    awareness_issue_title = pick_first_matching(
        issue_titles,
        ("安全意识",),
        "部分员工安全意识有待提高",
    )

    return [
        PageCandidate(
            PagePlan(
                section="背景与总体判断",
                page_type="封面",
                page_role="概览页",
                page_intent="用正式品牌开场，明确这是面向管理层与技术团队的安服总结汇报。",
                proof_goal="建立项目主题、客户对象和汇报场景的正式认知。",
                core_judgment="本次汇报将围绕攻防结果、关键风险与整改闭环展开。",
                evidence="项目名称、客户名称、场景与品牌要求",
                recommended_page_type="封面页",
                is_complex=False,
                note=f"必须保留模板固定骨架；{brand_mandatories}",
            )
        ),
        PageCandidate(
            PagePlan(
                section="背景与总体判断",
                page_type="目录",
                page_role="概览页",
                page_intent="让听众先看到全套汇报的结果-证据-整改-价值节奏。",
                proof_goal="降低混合受众的阅读成本，先建立导航结构。",
                core_judgment="本套 PPT 将先讲结果与风险，再展开链路、问题和整改闭环。",
                evidence="章节规划：总体判断、攻击路径、问题分析、治理闭环、能力价值",
                recommended_page_type="目录页",
                is_complex=False,
                note="目录页需要清楚体现章节分组，不要把附录塞进主目录主线。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="背景与总体判断",
                page_type="章节页 / 项目背景与总体判断",
                page_role="推进页",
                page_intent="作为开篇分隔页，提示听众接下来先看总体结论。",
                proof_goal="把注意力从封面过渡到结果判断。",
                core_judgment="先接受结果判断，再进入链路和证据会更容易形成一致结论。",
                evidence="章节 1：背景与总体判断",
                recommended_page_type="章节页",
                is_complex=False,
                note="章节页保持轻量，不承载过多正文。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="背景与总体判断",
                page_type="项目范围 / 整体回顾",
                page_role="概览页",
                page_intent="交代本轮演练对象、范围与整体回顾，让听众先站在全局看结果。",
                proof_goal="建立“本轮结论来自真实攻防结果”的基础信任。",
                core_judgment="本轮演练的范围、对象与周期已经足以支撑后续成果与风险判断具备真实场景代表性。",
                evidence=summary_evidence,
                recommended_page_type="概览页",
                is_complex=False,
                note=f"突出范围、时间与对象；受众关注点：{audience_focus}",
            )
        ),
        PageCandidate(
            PagePlan(
                section="背景与总体判断",
                page_type="重要成果 / 关键结果",
                page_role="证明页",
                page_intent="把本轮已经拿到的关键结果先摆出来，形成第一层证明。",
                proof_goal="让管理层迅速知道此次演练触达了哪些高价值结果。",
                core_judgment="外网突破、内网横向和人员受骗等结果已经构成可信的高风险判断。",
                evidence=f"{summary_evidence}；{attack_evidence}",
                recommended_page_type="证据页",
                is_complex=False,
                note="优先写结果，不要把这一页写成过程流水账。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="背景与总体判断",
                page_type="管理层结果判断 / 风险结论",
                page_role="概览页",
                page_intent="把关键结果翻译成管理层更容易接受的风险判断与业务含义。",
                proof_goal="让管理层接受结论成立，并愿意继续看证据与整改优先级。",
                core_judgment=desired_judgment,
                evidence=f"{summary_evidence}；展示重点：{extract_brief_field(brief_text, '必须保留的信息') or '关键攻击路径、关键证据、风险结论'}",
                recommended_page_type="风险总览页",
                is_complex=True,
                note="适合作为管理摘要页，用结果、影响和优先级三段式组织。",
            ),
            mandatory=False,
            enabled=True,
            optional_rank=5,
        ),
        PageCandidate(
            PagePlan(
                section="背景与总体判断",
                page_type="风险总览 / 风险暴露面矩阵",
                page_role="概览页",
                page_intent="把本次暴露面按外网、内网、人员与治理层面做结构化总览。",
                proof_goal="证明风险不是平均分布，而是集中在少数高放大链路上。",
                core_judgment="当前风险暴露面具有链路化放大特征，应按结果影响而不是按条目数量排序。",
                evidence=f"{summary_evidence}；{issue_evidence}",
                recommended_page_type="风险总览页",
                is_complex=True,
                note="优先使用矩阵或风险分层表达，服务后续攻击链与整改页。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="攻击路径与证据证明",
                page_type="章节页 / 攻击路径与证据证明",
                page_role="推进页",
                page_intent="进入攻击链与证据部分，提醒听众接下来看的不是漏洞清单，而是结果形成路径。",
                proof_goal="从总体判断平滑过渡到链路证明。",
                core_judgment="只有把攻击路径与证据连起来，风险结论才足够稳固。",
                evidence="章节 2：攻击路径与证据证明",
                recommended_page_type="章节页",
                is_complex=False,
                note="章节页保持简洁，强化段落切换。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="攻击路径与证据证明",
                page_type="攻击链总览 / 整体攻击路径分析",
                page_role="推进页",
                page_intent="总览攻击主链，说明外网入口、横向扩散与结果触达之间的关系。",
                proof_goal="证明问题是链路化、可重复放大的，而不是孤立事件。",
                core_judgment="多条入口最终汇聚到相似的控制结果，说明风险具备结构性和可复制性。",
                evidence=attack_evidence,
                recommended_page_type="攻击链页",
                is_complex=True,
                note="主链必须完整，证据只挂关键节点，不要把所有细节塞进一页。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="攻击路径与证据证明",
                page_type="攻击链展开 / 互联网侧攻击路径",
                page_role="推进页",
                page_intent="拆开互联网侧主路径，说明外部暴露面如何成为真实入口。",
                proof_goal="证明互联网侧不是单点高危，而是可直接转化为突破能力的主入口。",
                core_judgment="互联网侧暴露面与高危漏洞组合，使攻击者具备稳定的初始进入能力。",
                evidence=f"{summarize_titles(filter_items_by_keywords(attack_titles, ('互联网侧',)), '互联网侧攻击路径概述')}；{external_evidence}",
                recommended_page_type="攻击链页",
                is_complex=True,
                note="应突出入口、利用动作、权限结果与关键证据。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="攻击路径与证据证明",
                page_type="攻击链展开 / 内网侧攻击路径",
                page_role="推进页",
                page_intent="说明内网内的横向移动、后台权限获取和关键资产触达过程。",
                proof_goal="证明内网侧存在放大条件，导致风险可从入口扩张到核心环境。",
                core_judgment="一旦形成内网初始落点，凭证复用、管理面暴露和审计薄弱会把局部突破放大为核心环境风险。",
                evidence=f"{summarize_titles(filter_items_by_keywords(attack_titles, ('内网侧',)), '内网侧攻击路径概述')}；{internal_evidence}",
                recommended_page_type="攻击链页",
                is_complex=True,
                note="节点文案应写成对象 + 动作，避免只写工具名或漏洞名。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="攻击路径与证据证明",
                page_type="案例链 / 社工钓鱼路径",
                page_role="证明页",
                page_intent="补充人员侧攻击路径，让听众知道风险不仅来自系统，也来自人员暴露面。",
                proof_goal="证明人员安全意识薄弱会放大整体攻击成功率。",
                core_judgment="社工钓鱼路径与系统侧路径相互补充，说明整体防线存在多点松动。",
                evidence=phishing_evidence,
                recommended_page_type="结果导向案例页",
                is_complex=True,
                note="适合做多案例并列或泳道对照，避免单个案例占满整页。",
            ),
            mandatory=False,
            enabled=has_phishing,
            optional_rank=1,
        ),
        PageCandidate(
            PagePlan(
                section="攻击路径与证据证明",
                page_type="证据证明 / 关键证据总览",
                page_role="证明页",
                page_intent="把截图、日志、控制结果等关键证据集中挂载，给结论提供硬支撑。",
                proof_goal="证明前述攻击链不是推测，而是有真实取证结果支持。",
                core_judgment="证据已经足够支撑关键路径与结果判断，无需再停留在假设层。",
                evidence=f"{evidence_assets}；{external_evidence}；{internal_evidence}",
                recommended_page_type="证据页",
                is_complex=True,
                note="证据必须回答“它证明了哪一步已真实发生”。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="攻击路径与证据证明",
                page_type="结果导向案例 / 攻击结果归因",
                page_role="证明页",
                page_intent="把链路结果与风险影响对应起来，说明这些结果为何值得管理层立即重视。",
                proof_goal="把技术链路翻译成结果影响和治理优先级。",
                core_judgment="关键结果并非技术偶发，而是控制薄弱叠加后的必然输出。",
                evidence=f"{external_evidence}；{internal_evidence}；{phishing_evidence}",
                recommended_page_type="结果导向案例页",
                is_complex=True,
                note="适合做结果 headline + 关键原因 + 证据挂载。",
            ),
            mandatory=False,
            enabled=bool(external_cases or internal_cases or phishing_cases),
            optional_rank=4,
        ),
        PageCandidate(
            PagePlan(
                section="问题分析与风险拆解",
                page_type="章节页 / 问题分析与风险拆解",
                page_role="推进页",
                page_intent="从攻击结果回落到根因问题，提示接下来进入问题拆解阶段。",
                proof_goal="把链路证明自然承接到问题分析，而不是突然切换到漏洞清单。",
                core_judgment="结果背后对应的是少数高频重复出现的结构性问题。",
                evidence="章节 3：问题分析与风险拆解",
                recommended_page_type="章节页",
                is_complex=False,
                note="章节页用于切换视角，不承载过多条目。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="问题分析与风险拆解",
                page_type="问题分析总览 / 风险结构总览",
                page_role="推进页",
                page_intent="把问题从离散漏洞归并为可治理的风险域和根因域。",
                proof_goal="证明真正需要治理的是控制薄弱域，而非零散问题列表。",
                core_judgment="互联网暴露、内网审计不足、凭证治理薄弱和人员意识不足共同构成主要根因。",
                evidence=issue_evidence,
                recommended_page_type="风险总览页",
                is_complex=True,
                note="优先按风险域聚类，不要一条条复述附录漏洞。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="问题分析与风险拆解",
                page_type=f"关键问题拆解 / {internet_issue_title}",
                page_role="推进页",
                page_intent="聚焦互联网侧暴露面和防护薄弱点，说明入口为什么持续可用。",
                proof_goal="证明外部暴露面治理不足是首层高优先级问题。",
                core_judgment="互联网侧入口缺少持续检测与及时修补，使高危入口持续存在。",
                evidence=internet_issue_title,
                recommended_page_type="问题拆解页",
                is_complex=False,
                note="聚焦入口、暴露面和首轮利用条件，控制文案密度。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="问题分析与风险拆解",
                page_type=f"关键问题拆解 / {internal_issue_title}",
                page_role="推进页",
                page_intent="解释内网审计不足与高危端口暴露如何放大横向移动风险。",
                proof_goal="证明内网控制薄弱是结果被放大的关键条件。",
                core_judgment="缺少异常登录审计与高危端口限源，使攻击者更容易保持驻留并扩大控制范围。",
                evidence=summarize_titles(
                    [title for title in issue_titles if "内网" in title],
                    internal_issue_title,
                ),
                recommended_page_type="问题拆解页",
                is_complex=False,
                note="避免把这一页做成多列表格，保留 2-3 个关键判断即可。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="问题分析与风险拆解",
                page_type=f"关键问题拆解 / {credential_issue_title}",
                page_role="推进页",
                page_intent="聚焦账号口令、权限复用与管理面控制不足的问题。",
                proof_goal="证明凭证治理薄弱是多条路径得以复用的核心原因。",
                core_judgment="通用口令、弱口令和权限复用让攻击结果从单次突破演变为多点扩散。",
                evidence=credential_issue_title,
                recommended_page_type="问题拆解页",
                is_complex=False,
                note="适合用“现状-风险-动作”三段式写法。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="问题分析与风险拆解",
                page_type=f"关键问题拆解 / {awareness_issue_title}",
                page_role="推进页",
                page_intent="补足人员安全意识与社工风险这一类软性问题。",
                proof_goal="证明人员侧问题也会显著放大整体攻击成功率。",
                core_judgment="如果不提升人员识别与响应能力，系统侧治理效果会被持续稀释。",
                evidence=f"{awareness_issue_title}；{phishing_evidence}",
                recommended_page_type="问题拆解页",
                is_complex=False,
                note="文案需要贴近业务岗位，不要只写抽象意识提升。",
            ),
            mandatory=False,
            enabled=has_phishing or awareness_issue_title != "部分员工安全意识有待提高",
            optional_rank=2,
        ),
        PageCandidate(
            PagePlan(
                section="整改优先级与治理闭环",
                page_type="章节页 / 整改优先级与治理闭环",
                page_role="推进页",
                page_intent="把问题拆解自然过渡到整改排序和治理方法。",
                proof_goal="让听众做好从“看问题”转向“看动作”的心理切换。",
                core_judgment="只有给出优先级、路线图和复测闭环，汇报才真正可执行。",
                evidence="章节 4：整改优先级与治理闭环",
                recommended_page_type="章节页",
                is_complex=False,
                note="章节页保持简洁，起到节奏切换作用。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="整改优先级与治理闭环",
                page_type="治理矩阵 / 整改优先级排序",
                page_role="推进页",
                page_intent="把问题映射成 P1/P2/P3 或阶段性优先级，明确先做什么。",
                proof_goal="证明整改顺序必须围绕结果链路和放大条件，而不是平均推进。",
                core_judgment="优先封堵互联网入口、凭证风险和内网放大条件，能最快压降整体风险。",
                evidence=remediation_evidence,
                recommended_page_type="治理矩阵页",
                is_complex=True,
                note="矩阵必须体现优先级、动作与验收，不要只做问题-建议对照表。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="整改优先级与治理闭环",
                page_type="整改路线图 / 分阶段推进计划",
                page_role="推进页",
                page_intent="把整改动作分成短期止血、中期治理、长期机制建设三个层次。",
                proof_goal="让客户知道整改不是一句“建议修复”，而是可落地的推进路径。",
                core_judgment="先压降高风险入口，再补齐监测审计与制度能力，才能形成稳态治理。",
                evidence=remediation_evidence,
                recommended_page_type="时间线页",
                is_complex=False,
                note="可用时间线或阶段卡片，不要塞过多细节条目。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="整改优先级与治理闭环",
                page_type="运营闭环 / 整改复测机制",
                page_role="收束页",
                page_intent="说明整改之后如何复测、跟踪和闭环，避免问题反复出现。",
                proof_goal="证明长亭不仅能发现问题，也能帮助客户把问题闭环。",
                core_judgment="治理必须包含责任、动作、复测和回看机制，才能避免风险重复暴露。",
                evidence=f"{remediation_evidence}；{desired_action}",
                recommended_page_type="运营闭环页",
                is_complex=True,
                note="适合做闭环流程或泳道图，体现责任人与验证节点。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="整改优先级与治理闭环",
                page_type="整改收尾 / 创建账号与遗留文件信息清理",
                page_role="推进页",
                page_intent="补充清理类动作，说明演练结束后的收尾要求和风险遗留处理。",
                proof_goal="避免客户误以为整改只包含漏洞修复，不包含环境清理与权限收口。",
                core_judgment="账号、文件和遗留痕迹不清理，会让整改效果打折并留下后续风险。",
                evidence=cleanup_evidence,
                recommended_page_type="问题拆解页",
                is_complex=False,
                note="适合做清单化动作页，突出责任归属和完成标准。",
            ),
            mandatory=False,
            enabled=has_cleanup,
            optional_rank=3,
        ),
        PageCandidate(
            PagePlan(
                section="关键案例与能力价值",
                page_type="章节页 / 关键案例与能力价值",
                page_role="推进页",
                page_intent="进入附录案例与能力价值部分，提醒听众这是补充证明和收束部分。",
                proof_goal="让案例页服务主线，而不是把附录重新做成主叙事。",
                core_judgment="典型案例用于强化结论，而非替代主叙事。",
                evidence="章节 5：关键案例与能力价值",
                recommended_page_type="章节页",
                is_complex=False,
                note="章节页只做转场，不叠加正文。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="关键案例与能力价值",
                page_type="结果导向案例 / 互联网侧典型案例摘要",
                page_role="证明页",
                page_intent="选取互联网侧代表性案例，说明入口型问题如何直接形成结果。",
                proof_goal="让听众对外网暴露面的风险形成更具体、更可信的认识。",
                core_judgment="互联网侧高危入口一旦失守，后续利用与放大门槛明显偏低。",
                evidence=external_evidence,
                recommended_page_type="结果导向案例页",
                is_complex=True,
                note="只选 2-3 个代表案例，服务主结论，不要做附录拼盘。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="关键案例与能力价值",
                page_type="结果导向案例 / 内网突破典型案例摘要",
                page_role="证明页",
                page_intent="用内网突破类代表案例强化“入口 -> 放大 -> 结果”的主结论。",
                proof_goal="证明内网问题不是单点配置失误，而是能形成持续放大的主链。",
                core_judgment="后台权限、未授权访问和凭证问题叠加，足以形成高影响结果。",
                evidence=internal_evidence,
                recommended_page_type="结果导向案例页",
                is_complex=True,
                note="建议做结果 headline + 链路 + 证据挂载，避免纯文字罗列。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="关键案例与能力价值",
                page_type="能力总览 / 长亭安服价值",
                page_role="收束页",
                page_intent="把前文的问题发现、链路分析和整改闭环能力归并成长亭安服价值。",
                proof_goal="让客户认可长亭不仅能发现问题，也能提供治理方法与长期价值。",
                core_judgment=f"长亭安服的价值在于把复杂风险翻译成可验证、可排序、可闭环的治理动作。{goal}",
                evidence=f"主线目标：{goal}；整改动作：{desired_action}；受众：{audience}",
                recommended_page_type="背书页",
                is_complex=False,
                note="这一页是价值收束页，不是公司介绍页。",
            )
        ),
        PageCandidate(
            PagePlan(
                section="关键案例与能力价值",
                page_type="后续合作建议 / 下一步计划",
                page_role="收束页",
                page_intent="把整改、复测和后续协同动作落到下一阶段计划。",
                proof_goal="让客户明确会后应该怎么推动整改和继续合作。",
                core_judgment=desired_action,
                evidence=f"整改路线图；运营闭环；能力价值；目标受众：{audience}",
                recommended_page_type="背书页",
                is_complex=False,
                note="控制在 3 个可执行动作以内，避免写成泛泛销售页。",
            ),
            mandatory=False,
            enabled=True,
            optional_rank=6,
        ),
        PageCandidate(
            PagePlan(
                section="关键案例与能力价值",
                page_type="结束页",
                page_role="收束页",
                page_intent="正式结束汇报，留出答疑和收束空间。",
                proof_goal="把整套汇报收束到结论、动作与品牌印象上。",
                core_judgment="本次攻防结果可信，整改路径清晰，长亭具备支撑后续治理闭环的能力。",
                evidence="总体结论、整改动作、品牌背书",
                recommended_page_type="结束页",
                is_complex=False,
                note="结束页保持干净，确保品牌元素完整且不被正文遮挡。",
            )
        ),
    ]


def select_candidates(candidates: list[PageCandidate], target_pages: int) -> list[PagePlan]:
    mandatory_items = [item for item in candidates if item.mandatory and item.enabled]
    mandatory_count = len(mandatory_items)
    if target_pages <= 0:
        return [item.plan for item in mandatory_items]
    if target_pages < mandatory_count:
        trimmed = mandatory_items[: max(1, target_pages - 1)]
        ending = mandatory_items[-1]
        if trimmed and trimmed[-1] is ending:
            return [item.plan for item in trimmed]
        return [item.plan for item in trimmed + [ending]]

    optional_enabled = [item for item in candidates if not item.mandatory and item.enabled]
    extra_needed = max(0, min(len(optional_enabled), target_pages - mandatory_count))
    selected_optional = {
        id(item)
        for item in sorted(optional_enabled, key=lambda item: item.optional_rank)[:extra_needed]
    }

    plans: list[PagePlan] = []
    for item in candidates:
        if not item.enabled:
            continue
        if item.mandatory or id(item) in selected_optional:
            plans.append(item.plan)
    return plans


def build_security_service_pages(brief_text: str, target_pages: int, profile: dict[str, object]) -> list[PagePlan]:
    candidates = build_security_service_candidates(brief_text, profile)
    return select_candidates(candidates, target_pages)


def build_generic_pages(brief_text: str, target_pages: int) -> list[PagePlan]:
    goal = extract_brief_field(brief_text, "核心目标") or "围绕核心观点完成一次结构清晰的汇报。"
    audience = extract_brief_field(brief_text, "主要受众") or "目标受众"
    sections = detect_sections(brief_text)

    pages: list[PagePlan] = [
        PagePlan(
            section="总览",
            page_type="封面",
            page_role="概览页",
            page_intent="建立正式开场与主题认知。",
            proof_goal="让听众明确汇报对象、主题和场景。",
            core_judgment="本套汇报将围绕目标、重点拆解和建议收束展开。",
            evidence="项目名称、场景、受众",
            recommended_page_type="封面页",
            is_complex=False,
            note="封面保持简洁。",
        ),
        PagePlan(
            section="总览",
            page_type="目录",
            page_role="概览页",
            page_intent="建立阅读导航。",
            proof_goal="降低阅读成本。",
            core_judgment="整套内容会按章节逐步推进到建议与收束。",
            evidence="章节目录",
            recommended_page_type="目录页",
            is_complex=False,
            note="目录与后续结构保持一致。",
        ),
    ]

    for index, section in enumerate(sections, start=1):
        pages.append(
            PagePlan(
                section=section,
                page_type=f"章节页 / {section}",
                page_role="推进页",
                page_intent=f"进入章节“{section}”并提示内容切换。",
                proof_goal="让听众知道这一段要解决什么问题。",
                core_judgment=f"章节“{section}”将服务整体目标：{goal}",
                evidence=f"章节 {index}：{section}",
                recommended_page_type="章节页",
                is_complex=False,
                note="章节页保持轻量。",
            )
        )
        pages.append(
            PagePlan(
                section=section,
                page_type=f"{section} / 核心内容页",
                page_role="推进页",
                page_intent=f"展开章节“{section}”的核心观点与支撑信息。",
                proof_goal=f"证明章节“{section}”对总目标和受众 {audience} 的价值。",
                core_judgment=f"章节“{section}”应直接服务目标：{goal}",
                evidence=f"{section} 的关键事实、数据或案例",
                recommended_page_type="内容页",
                is_complex=False,
                note="先结论后解释，避免空泛概述。",
            )
        )

    pages.append(
        PagePlan(
            section="收束",
            page_type="结束页",
            page_role="收束页",
            page_intent="收束全套内容。",
            proof_goal="让听众带着明确结论和下一步动作离开。",
            core_judgment="本次汇报围绕目标完成了问题、证据与建议的闭环表达。",
            evidence="核心结论与下一步动作",
            recommended_page_type="结束页",
            is_complex=False,
            note="结束页保持干净。",
        )
    )

    if len(pages) <= target_pages:
        return pages

    return pages[: max(4, target_pages - 1)] + [pages[-1]]


def build_pages(brief_text: str, project_dir: Path) -> list[PagePlan]:
    detected_domain = extract_brief_field(brief_text, "识别领域")
    template_hint = extract_brief_field(brief_text, "模板倾向建议")
    recommended_domain_pack = extract_brief_field(brief_text, "推荐行业包")
    template_name = extract_brief_field(brief_text, "指定模板")
    page_range_text = extract_brief_field(brief_text, "页数范围")

    detection_text = " ".join(
        [brief_text, detected_domain, template_hint, recommended_domain_pack, template_name]
    ).lower()
    is_security_service = any(keyword in detection_text for keyword in SECURITY_KEYWORDS)
    target_pages = choose_target_page_count(page_range_text, is_security_service)

    if is_security_service:
        source_profile = collect_source_profile(project_dir)
        return build_security_service_pages(brief_text, target_pages, source_profile)
    return build_generic_pages(brief_text, target_pages)


def render_storyline(
    pages: list[PagePlan],
    brief_text: str,
    detected_domain: str,
    template_hint: str,
    recommended_domain_pack: str,
) -> str:
    audience = extract_brief_field(brief_text, "主要受众") or "待确认"
    goal = extract_brief_field(brief_text, "核心目标") or "待确认"
    desired_judgment = extract_brief_field(brief_text, "期待对方形成的判断") or goal
    desired_action = extract_brief_field(brief_text, "期待对方采取的动作") or "推动会后动作"
    audience_focus = extract_brief_field(brief_text, "受众更关心") or "管理判断与支撑证据"
    brand_mandatories = extract_brief_field(brief_text, "必须固定的品牌元素") or "保持模板固定品牌元素"

    section_order: list[str] = []
    for page in pages:
        if page.section not in section_order:
            section_order.append(page.section)

    lines = [
        "# Storyline",
        "",
        "## 一、总叙事判断",
        f"- 识别领域：{detected_domain or '通用'}",
        f"- 模板倾向建议：{template_hint or '按项目实际模板执行'}",
        f"- 推荐行业包：{recommended_domain_pack or '无'}",
        f"- 一句话主线：先让听众接受「{desired_judgment}」，再用攻击链、证据与整改闭环支撑，并推动「{desired_action}」。",
        f"- 这套 PPT 最终要证明：{goal}",
        f"- 主要受众阅读路径：{audience}；阅读重点：{audience_focus}",
        "",
        "## 二、章节规划",
    ]

    for index, section in enumerate(section_order, start=1):
        section_pages = [i + 1 for i, page in enumerate(pages) if page.section == section]
        section_items = [page for page in pages if page.section == section]
        role_summary = " / ".join(unique_items([page.recommended_page_type for page in section_items]))
        goal_summary = summarize_titles([page.proof_goal for page in section_items], "承接主线并推进证明", limit=2)
        question_summary = summarize_titles([page.core_judgment for page in section_items], "回答本章核心判断", limit=2)
        lines.extend(
            [
                f"### 章节 {index}：{section}（第 {section_pages[0]}-{section_pages[-1]} 页）",
                f"- 章节目标：{goal_summary}",
                f"- 要解决的问题：{question_summary}",
                f"- 主要页型：{role_summary}",
                "",
            ]
        )

    proof_pages = [f"第 {index} 页《{page.page_type}》" for index, page in enumerate(pages, start=1) if page.page_role == "证明页"]
    closure_pages = [f"第 {index} 页《{page.page_type}》" for index, page in enumerate(pages, start=1) if page.page_role == "收束页"]
    complex_pages = [f"第 {index} 页《{page.page_type}》" for index, page in enumerate(pages, start=1) if page.is_complex]
    simple_pages = [
        f"第 {index} 页《{page.page_type}》"
        for index, page in enumerate(pages, start=1)
        if not page.is_complex and page.recommended_page_type in {"封面页", "目录页", "章节页", "结束页"}
    ]

    lines.extend(
        [
            "## 三、跨页推进",
            f"- 从哪一页开始建立认知：第 4 页《{pages[3].page_type}》" if len(pages) >= 4 else "- 从哪一页开始建立认知：第 1 页",
            f"- 哪几页承担证明：{ '、'.join(proof_pages) if proof_pages else '无单独证明页，需在正文页完成证明'}",
            f"- 哪几页承担收束：{ '、'.join(closure_pages) if closure_pages else '最后一页承担收束'}",
            "- 哪几页必须避免重复：问题拆解页不要重复附录逐条漏洞；案例页只保留代表性案例；章节页不承载正文。",
            "",
            "## 四、复杂页规划",
            f"- 必做复杂页：{ '、'.join(complex_pages) if complex_pages else '无'}",
            "- 可选复杂页：若页数允许，可增加管理摘要页、人员风险页或收尾治理页，但仍要服务主线。",
            f"- 必须保持简单的页：{ '、'.join(simple_pages) if simple_pages else '封面、目录、章节页、结束页'}",
            "",
            "## 五、风险提醒",
            "- 逻辑风险：不要把附录漏洞数量误当成主线页数，必须先讲结果和结构性风险，再展开个案。",
            "- 排版风险：复杂页靠结构增密，不靠缩字号；证据图、Logo、页码和装饰条不能互相打架。",
            f"- 品牌风险：{brand_mandatories}",
            "",
        ]
    )
    return "\n".join(lines)


def render_outline(pages: list[PagePlan]) -> str:
    lines = ["# Page Outline", ""]
    for index, page in enumerate(pages, start=1):
        lines.extend(
            [
                f"## 第 {index} 页",
                f"- 页面类型：{page.page_type}",
                f"- 页面角色：{page.page_role}",
                f"- 页面意图：{page.page_intent}",
                f"- 证明目标：{page.proof_goal}",
                f"- 核心判断：{page.core_judgment}",
                f"- 支撑证据：{page.evidence}",
                f"- 推荐页型：{page.recommended_page_type}",
                f"- 是否复杂页：{'是' if page.is_complex else '否'}",
                f"- 备注：{page.note or '按章节节奏推进，避免信息重复。'}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build storyline.md and page_outline.md from project brief.")
    parser.add_argument("brief", help="Path to project_brief.md")
    parser.add_argument("--storyline-output", required=True)
    parser.add_argument("--outline-output", required=True)
    args = parser.parse_args()

    brief_path = Path(args.brief).expanduser().resolve()
    brief_text = brief_path.read_text(encoding="utf-8")
    detected_domain = extract_brief_field(brief_text, "识别领域")
    template_hint = extract_brief_field(brief_text, "模板倾向建议")
    recommended_domain_pack = extract_brief_field(brief_text, "推荐行业包")

    pages = build_pages(brief_text, brief_path.parent)
    storyline_text = render_storyline(
        pages,
        brief_text,
        detected_domain,
        template_hint,
        recommended_domain_pack,
    )
    outline_text = render_outline(pages)

    story_out = Path(args.storyline_output).expanduser().resolve()
    outline_out = Path(args.outline_output).expanduser().resolve()
    story_out.parent.mkdir(parents=True, exist_ok=True)
    outline_out.parent.mkdir(parents=True, exist_ok=True)
    story_out.write_text(storyline_text, encoding="utf-8")
    outline_out.write_text(outline_text, encoding="utf-8")
    print(f"Wrote: {story_out}")
    print(f"Wrote: {outline_out}")


if __name__ == "__main__":
    main()
