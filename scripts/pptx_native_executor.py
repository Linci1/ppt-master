#!/usr/bin/env python3
"""
pptx_native_executor.py
=======================
ppt-master Step 6 的 python-pptx 原生执行引擎。

工作流程：
  1. 读取项目目录：design_spec.md / layout_index.json / content.md
  2. 按页型生成 Python 代码（调用 pptx_components.py）
  3. 执行代码 → PPTX

使用方式：
  # 分析参考稿（生成 layout_index.json）
  python3 reference_analyzer.py <ref_pptx> -o project/layout_index.json

  # 执行生成
  python3 pptx_native_executor.py <project_path> --engine native

  # 或两步合一（从参考稿开始完整生成）
  python3 pptx_native_executor.py <project_path> \
      --ref-pptx <ref_pptx> \
      --content content.md
"""

import os, sys, json, argparse, textwrap
from pathlib import Path
from typing import Dict, List, Any, Optional

# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────

SKILL_DIR = Path(__file__).parent.parent.resolve()
COMPONENTS_PY = SKILL_DIR / 'scripts' / 'pptx_components.py'
sys.path.insert(0, str(SKILL_DIR / 'scripts'))

# ─────────────────────────────────────────────────────────────────
# 代码生成器
# ─────────────────────────────────────────────────────────────────

class CodeGenerator:
    """
    根据 layout_index.json + content 生成 Python 代码。
    输出调用 pptx_components.py 各函数的代码。
    """

    def __init__(self, layout_index: Dict, design_spec: Dict,
                 content_pages: List[Dict]):
        self.layout_index  = layout_index
        self.design_spec   = design_spec
        self.content_pages = content_pages  # [{page_num, title, body, page_type}, ...]
        self.theme         = self._build_theme()

    def _build_theme(self) -> Dict:
        """从 design_spec 或 layout_index 推断主题色"""
        meta = self.layout_index.get('metadata', {})
        theme = meta.get('theme_colors', {})

        # 优先用 layout_index 的实际填充色
        fills = set()
        for page in self.layout_index.get('pages', []):
            for el in page.get('elements', []):
                if el.get('fill'):
                    fills.add(el['fill'])

        primary = None
        for candidate in ['7BBD4A', '4F81BD', '1F497D']:
            if candidate in fills:
                primary = candidate
                break
        if not primary and fills:
            primary = list(fills)[0]

        return {
            'primary':   primary or '7BBD4A',
            'card_deep': '3C7471',
            'canvas_w':  meta.get('canvas_w_in', 13.333),
            'canvas_h':  meta.get('canvas_h_in', 7.5),
        }

    def generate(self) -> str:
        """生成完整的 Python 代码字符串"""
        pages = self.layout_index.get('pages', [])
        hints = self.layout_index.get('component_hints', [])

        lines = [
            '#!/usr/bin/env python3',
            '"""',
            f'自动生成页数: {len(pages)}',
            f'主题色: PRIMARY=#{self.theme["primary"]}',
            '"""',
            '',
            'import sys',
            f"sys.path.insert(0, '{SKILL_DIR}/scripts')",
            '',
            'from pptx import Presentation',
            'from pptx_components import (',
            '    Theme,',
            '    build_card_grid_page,',
            '    build_timeline_page,',
            '    build_data_table_page,',
            '    build_two_column_page,',
            '    build_text_section_page,',
            ')',
            '',
            '# ── 主题配置 ──',
            'from pptx.dml.color import RGBColor',
            f"Theme.PRIMARY = RGBColor("
            f"    0x{self.theme['primary'][:2]},"
            f" 0x{self.theme['primary'][2:4]},"
            f" 0x{self.theme['primary'][4:6]})",
            f"Theme.CARD_DEEP = RGBColor("
            f"    0x{self.theme['card_deep'][:2]},"
            f" 0x{self.theme['card_deep'][2:4]},"
            f" 0x{self.theme['card_deep'][4:6]})",
            '',
            '# ── 创建 Presentation ──',
            'prs = Presentation()',
            'prs.slide_width  = Theme.CANVAS_W',
            'prs.slide_height = Theme.CANVAS_H',
            '',
        ]

        # 按 component_hints 顺序生成每页（而非 layout_index pages）
        # 如果没有 hints，则遍历 layout_index 的实际页数
        if hints:
            page_iter = [(h['page'], h) for h in hints]
        else:
            page_iter = [(i+1, {}) for i, _ in enumerate(pages)]

        hint_map = {h['page']: h for h in hints}

        for page_idx, hint in page_iter:
            func_name = hint.get('func', 'build_card_grid_page') if hint else 'build_card_grid_page'
            page_num  = str(page_idx + 3)  # 假设封面等固定页占前3页

            # 找对应的内容（从 content_pages）
            content = self._find_content(page_idx)

            lines.append(f'# ── 第 {page_idx} 页: {func_name} ──')
            lines.append(self._generate_page_code(func_name, page_num, content, {}))
            lines.append('')

        # 保存路径
        lines.append('# ── 保存 ──')
        lines.append("prs.save('generated.pptx')")

        return '\n'.join(lines)

    def _find_content(self, page_index: int) -> Optional[Dict]:
        """从 content_pages 匹配第 page_index 页的内容"""
        for cp in self.content_pages:
            if cp.get('page_num') == page_index:
                return cp
        return None

    def _generate_page_code(self, func_name: str, page_num: str,
                             content: Optional[Dict],
                             page_data: Dict) -> str:
        """为单页生成函数调用代码"""
        title    = (content or {}).get('title', f'页面 {page_num}')
        subtitle = (content or {}).get('subtitle', '')
        body     = (content or {}).get('body', {})
        logo     = (content or {}).get('logo_path', '')

        # 转成字符串
        title_str    = title.replace('"', '\\"')
        subtitle_str = subtitle.replace('"', '\\"')
        logo_str     = f'"{logo}"' if logo and logo.strip() else 'None'

        # 根据页型生成
        if func_name == 'build_card_grid_page':
            return self._gen_card_grid(title_str, subtitle_str, page_num,
                                        content, logo_str)
        elif func_name == 'build_timeline_page':
            return self._gen_timeline(title_str, subtitle_str, page_num,
                                      content, logo_str)
        elif func_name == 'build_data_table_page':
            return self._gen_data_table(title_str, subtitle_str, page_num,
                                        content, logo_str)
        elif func_name == 'build_two_column_page':
            return self._gen_two_column(title_str, subtitle_str, page_num,
                                        content, logo_str)
        elif func_name in ('build_text_section', 'build_text_section_page'):
            return self._gen_text_section(title_str, subtitle_str, page_num,
                                           content, logo_str)
        else:
            return self._gen_card_grid(title_str, subtitle_str, page_num,
                                         content, logo_str)

    def _gen_card_grid(self, title, subtitle, page_num, content, logo) -> str:
        cards = (content or {}).get('cards', [])
        if not cards:
            cards = [{'title': '待填充', 'lines': ['请补充内容']}]

        cards_repr = []
        for c in cards:
            lines = c.get('lines', [])
            lines_repr = '[' + ', '.join(f'"{l.replace('"', '\\"')}"' for l in lines) + ']'
            cards_repr.append(f"    {{'title': '{c['title'].replace('"', '\\"')}', 'lines': {lines_repr}}}")

        cards_block = ',\n'.join(cards_repr)
        card_style  = (content or {}).get('card_style', 'dark')

        return '\n'.join([
            f'build_card_grid_page(',
            f'    prs,',
            f'    title="{title}",',
            f'    subtitle="{subtitle}",',
            f'    page_num="{page_num}",',
            f'    logo_path={logo},',
            f'    card_style="{card_style}",',
            f'    cards=[',
        ]) + '\n' + cards_block + '\n' + '\n'.join([
            '    ],',
            ')',
        ])

    def _gen_timeline(self, title, subtitle, page_num, content, logo) -> str:
        items = (content or {}).get('timeline_items', [])
        if not items:
            items = [{'time': 'TBD', 'title': '待填充', 'description': ''}]

        items_repr = []
        for it in items:
            items_repr.append(
                f"    {{'time': '{it['time'].replace('"', '\\"')}', "
                f"'title': '{it['title'].replace('"', '\\"')}', "
                f"'description': '{it.get('description', '').replace('"', '\\"')}'}}"
            )
        items_block = ',\n'.join(items_repr)

        return '\n'.join([
            'build_timeline_page(',
            f'    prs,',
            f'    title="{title}",',
            f'    subtitle="{subtitle}",',
            f'    page_num="{page_num}",',
            f'    logo_path={logo},',
            f'    items=[',
        ]) + '\n' + items_block + '\n' + '\n'.join([
            '    ],',
            ')',
        ])

    def _gen_data_table(self, title, subtitle, page_num, content, logo) -> str:
        headers = (content or {}).get('headers', [])
        rows    = (content or {}).get('rows', [])
        col_ws  = (content or {}).get('col_widths', [])

        h_block  = '[' + ', '.join(f'"{h.replace('"', '\\"')}"' for h in headers) + ']'
        r_lines  = []
        for row in rows:
            r_lines.append('    [' + ', '.join(f'"{str(v).replace('"', '\\"')}"' for v in row) + ']')
        r_block  = ',\n'.join(r_lines) or '    []'
        cw_block = '[' + ', '.join(str(w) for w in col_ws) + ']' if col_ws else 'None'

        return '\n'.join([
            'build_data_table_page(',
            f'    prs,',
            f'    title="{title}",',
            f'    subtitle="{subtitle}",',
            f'    page_num="{page_num}",',
            f'    logo_path={logo},',
            f'    headers={h_block},',
            f'    rows=[{r_block}],',
            f'    col_widths={cw_block},',
            ')',
        ])

    def _gen_two_column(self, title, subtitle, page_num, content, logo) -> str:
        left  = content.get('left',  {}) if content else {}
        right = content.get('right', {}) if content else {}

        def bullets_block(d):
            bullets = d.get('bullets', [])
            if not bullets:
                return '[]'
            return '[' + ', '.join(f'"{b.replace('"', '\\"')}"' for b in bullets) + ']'

        return '\n'.join([
            'build_two_column_page(',
            f'    prs,',
            f'    title="{title}",',
            f'    subtitle="{subtitle}",',
            f'    page_num="{page_num}",',
            f'    logo_path={logo},',
            f"    left={{'heading': '{left.get('heading', '左侧').replace('\"', '\\\\\"')}', 'bullets': {bullets_block(left)}}},"
            ,
            f"    right={{'heading': '{right.get('heading', '右侧').replace('\"', '\\\\\"')}', 'bullets': {bullets_block(right)}}},"
            ,
            ')',
        ])

    def _gen_text_section(self, title, subtitle, page_num, content, logo) -> str:
        sections = (content or {}).get('sections', [])
        if not sections:
            sections = [{'heading': '', 'body': '请补充内容'}]

        secs_repr = []
        for s in sections:
            secs_repr.append(
                f"    {{'heading': '{s.get('heading', '').replace('"', '\\"')}', "
                f"'body': '{s.get('body', '').replace('"', '\\"')}'}}"
            )
        secs_block = ',\n'.join(secs_repr)

        return '\n'.join([
            'build_text_section_page(',
            f'    prs,',
            f'    title="{title}",',
            f'    subtitle="{subtitle}",',
            f'    page_num="{page_num}",',
            f'    logo_path={logo},',
            f'    sections=[',
        ]) + '\n' + secs_block + '\n' + '\n'.join([
            '    ],',
            ')',
        ])


# ─────────────────────────────────────────────────────────────────
# 工具
# ─────────────────────────────────────────────────────────────────

def load_layout_index(project_path: Path) -> Dict:
    """读取 layout_index.json"""
    p = project_path / 'layout_index.json'
    if p.exists():
        with open(p) as f:
            return json.load(f)

    # 查找可能的位置
    for candidate in ['source_ppt_analysis.md']:
        cp = project_path / candidate
        if cp.exists():
            print(f'  ⚠  找到 {candidate} 但非 layout_index.json，跳过自动分析')
    return {'metadata': {}, 'pages': [], 'component_hints': []}


def load_design_spec(project_path: Path) -> Dict:
    """读取 design_spec.md（内容较自由，尝试提取关键字段）"""
    p = project_path / 'design_spec.md'
    if not p.exists():
        return {}
    with open(p) as f:
        content = f.read()
    # 简单提取（后续可增强为完整解析）
    return {'raw_content': content[:500]}


def load_content_md(project_path: Path) -> List[Dict]:
    """从 markdown 文件解析每页内容"""
    # 尝试多种可能的内容文件
    candidates = [
        project_path / 'content.md',
        project_path / 'sources' / 'content.md',
        project_path / 'content_pages.json',
    ]
    for cp in candidates:
        if cp.exists():
            return parse_content_file(cp)
    return []


def parse_content_file(path: Path) -> List[Dict]:
    """解析内容文件，返回 [{page_num, title, body}, ...]"""
    ext = path.suffix.lower()
    if ext == '.json':
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []

    if ext == '.md':
        with open(path) as f:
            content = f.read()

        pages = []
        # 简单按 # 页标题 分割
        import re
        # 匹配 ## P01 页面标题 或 ## 页面标题
        pattern = r'^##\s+(?:\d+\s+)?(.+?)$|^##\s+P(\d+)\s+(.+?)$'
        parts = re.split(pattern, content, flags=re.MULTILINE)

        # parts: [preamble, title_or_None, page_num_or_None, title, ...]
        current = {}
        for i, part in enumerate(parts):
            part = part.strip()
            if not part:
                continue
            # 检查是否是页码标题
            m = re.match(r'P(\d+)\s+(.+)', part)
            if m:
                if current:
                    pages.append(current)
                current = {'page_num': int(m.group(1)), 'title': m.group(2).strip()}
            elif not any(x in part for x in ('P0', 'P1', 'P2', 'P3', 'P4', 'P5')) and len(part) < 80:
                if not current.get('title'):
                    current['title'] = part
                else:
                    current.setdefault('sections', []).append(part)

        if current:
            pages.append(current)
        return pages

    return []


# ─────────────────────────────────────────────────────────────────
# 执行引擎
# ─────────────────────────────────────────────────────────────────

def run_executor(project_path: str,
                 ref_pptx: str = None,
                 content_file: str = None,
                 output_name: str = 'generated.pptx',
                 dry_run: bool = False) -> str:
    """
    主执行入口。

    Returns: 生成的 PPTX 文件路径
    """
    project_path = Path(project_path)

    # 1. 分析参考稿（如提供）
    if ref_pptx:
        import subprocess
        layout_out = project_path / 'layout_index.json'
        print(f'正在分析参考稿: {ref_pptx}')
        r = subprocess.run(
            [sys.executable, str(SKILL_DIR / 'scripts' / 'reference_analyzer.py'),
             str(ref_pptx), '-o', str(layout_out)],
            capture_output=True, text=True
        )
        if r.returncode != 0:
            print(f'⚠ reference_analyzer 失败: {r.stderr}')
        else:
            print(r.stdout.strip())

    # 2. 加载数据
    layout_index = load_layout_index(project_path)
    design_spec  = load_design_spec(project_path)

    if content_file:
        content_pages = parse_content_file(Path(content_file))
    else:
        content_pages = load_content_md(project_path)

    if not layout_index.get('pages'):
        print('⚠ layout_index.json 为空或不存在，请先运行 reference_analyzer.py')
        return None

    # 3. 生成代码
    gen = CodeGenerator(layout_index, design_spec, content_pages)
    code = gen.generate()

    # 4. 写临时文件
    gen_code_path = project_path / 'generated_pages.py'
    with open(gen_code_path, 'w') as f:
        f.write(code)
    print(f'✓ 代码已生成: {gen_code_path}')

    if dry_run:
        print('⚠ dry_run 模式，不执行代码')
        return str(gen_code_path)

    # 5. 执行代码（用系统 Python，确保 pptx 可用）
    print('正在执行生成...')
    import subprocess
    try:
        result = subprocess.run(
            ['/usr/local/bin/python3', str(gen_code_path)],
            cwd=str(project_path),
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            print(f'⚠ 代码执行失败 (exit {result.returncode})')
            if result.stdout:
                print('  stdout:', result.stdout.strip()[:500])
            if result.stderr:
                print('  stderr:', result.stderr.strip()[:500])
        else:
            if result.stdout:
                print(result.stdout.strip())
            print(f'✓ PPTX 已生成: {project_path / output_name}')
    except subprocess.TimeoutExpired:
        print('⚠ 执行超时（60s）')
    except Exception as e:
        print(f'⚠ 执行异常: {e}')

    out_pptx = project_path / output_name
    print(f'✓ PPTX 已生成: {out_pptx}')
    return str(out_pptx)


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description='ppt-master python-pptx 原生执行引擎（Step 6）')
    ap.add_argument('project', help='项目目录路径')
    ap.add_argument('--ref-pptx', dest='ref_pptx',
                     help='参考 PPTX 文件（如指定则先运行 reference_analyzer）')
    ap.add_argument('--content', dest='content',
                     help='内容文件路径（.md 或 .json）')
    ap.add_argument('-o', '--output', dest='output',
                     default='generated.pptx',
                     help='输出 PPTX 文件名（默认: generated.pptx）')
    ap.add_argument('--dry-run', action='store_true',
                     help='只生成代码，不执行')
    args = ap.parse_args()

    result = run_executor(
        project_path  = args.project,
        ref_pptx      = args.ref_pptx,
        content_file  = args.content,
        output_name   = args.output,
        dry_run       = args.dry_run,
    )

    if result:
        print(f'\n输出文件: {result}')


if __name__ == '__main__':
    main()
