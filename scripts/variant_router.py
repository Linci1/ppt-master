#!/usr/bin/env python3
"""
variant_router.py
=================
提取变体路由器。分析 extracted_variants/ 下的 SVG 变体文件，
提取结构特征并映射到 layout_type，为 Executor 提供页型选择依据。

工作流程：
  1. 扫描 extracted_variants/ 下所有 SVG
  2. 解析每个 SVG 的结构特征（矩形数、x/y 分布、列数、行数）
  3. 根据 heuristic 规则映射到 layout_type
  4. 输出 variant_index.json（供 Executor/Strategist 使用）

使用方式：
  # 分析变体并生成索引
  python3 variant_router.py <template_dir> -o variant_index.json

  # 查看变体映射
  python3 variant_router.py <template_dir> --list

模板目录示例：
  templates/layouts/chaitin_anfu/
    extracted_variants/
      hw_H1_S8.svg
      hw_H2_S12.svg
      ...
"""

import os, sys, json, argparse, re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from xml.etree import ElementTree as ET

# ─────────────────────────────────────────────────────────────────
# SVG 结构分析
# ─────────────────────────────────────────────────────────────────

SVG_NS = {'svg': 'http://www.w3.org/2000/svg'}


def parse_svg_structure(svg_path: Path) -> Dict:
    """
    解析 SVG 提取结构特征。

    返回:
      {
        'file': str,
        'rects': int,           # 矩形数量（内容色块）
        'texts': int,           # 文本数量
        'images': int,          # 图片数量
        'x_clusters': int,      # x 坐标聚类数（≈列数）
        'y_clusters': int,      # y 坐标聚类数（≈行数）
        'has_timeline': bool,   # 是否含时间线特征
        'has_table': bool,      # 是否含表格特征
        'aspect_ratio': str,    # 'wide' / 'tall' / 'square'
        'layout_hint': str,     # 初步布局推断
      }
    """
    try:
        tree = ET.parse(str(svg_path))
        root = tree.getroot()
    except ET.ParseError:
        return {'file': svg_path.name, 'error': 'parse_failed'}

    ns = SVG_NS

    # 统计矩形
    rects = root.findall('.//svg:rect', ns)
    rect_count = len(rects)

    # 统计文本
    texts = root.findall('.//svg:text', ns)
    text_count = len(texts)

    # 统计图片
    images = root.findall('.//svg:image', ns)
    image_count = len(images)

    # 提取矩形 x/y 坐标（用于判断列/行数）
    xs = []
    ys = []
    for r in rects:
        try:
            x = float(r.get('x', 0))
            y = float(r.get('y', 0))
            w = float(r.get('width', 0))
            h = float(r.get('height', 0))
            if w > 50 and h > 30:  # 只统计大色块
                xs.append(x)
                ys.append(y)
        except (ValueError, TypeError):
            continue

    # x/y 聚类
    x_clusters = _cluster_values(xs, threshold=60) if xs else 0
    y_clusters = _cluster_values(ys, threshold=40) if ys else 0

    # 时间线特征：y 值均匀分布且 x 集中在左侧
    has_timeline = False
    if y_clusters >= 3 and x_clusters <= 2 and text_count > 5:
        has_timeline = True

    # 表格特征：x/y 聚类都 >= 3 且矩形多
    has_table = x_clusters >= 3 and y_clusters >= 2 and rect_count > 8

    # 宽高比
    viewbox = root.get('viewBox', '0 0 1280 720')
    parts = viewbox.split()
    if len(parts) == 4:
        try:
            vb_w = float(parts[2])
            vb_h = float(parts[3])
            ratio = vb_w / vb_h if vb_h else 1
            if ratio > 1.5:
                aspect_ratio = 'wide'
            elif ratio < 0.8:
                aspect_ratio = 'tall'
            else:
                aspect_ratio = 'square'
        except ValueError:
            aspect_ratio = 'wide'
    else:
        aspect_ratio = 'wide'

    # 布局推断
    layout_hint = _infer_layout(
        x_clusters, y_clusters, rect_count,
        image_count, has_timeline, has_table
    )

    return {
        'file': svg_path.name,
        'rects': rect_count,
        'texts': text_count,
        'images': image_count,
        'x_clusters': x_clusters,
        'y_clusters': y_clusters,
        'has_timeline': has_timeline,
        'has_table': has_table,
        'aspect_ratio': aspect_ratio,
        'layout_hint': layout_hint,
    }


def _cluster_values(values: List[float], threshold: float = 50) -> int:
    """简单聚类：把差值 < threshold 的值归为一组"""
    if not values:
        return 0
    sorted_v = sorted(values)
    clusters = 1
    for i in range(1, len(sorted_v)):
        if sorted_v[i] - sorted_v[i-1] > threshold:
            clusters += 1
    return clusters


def _infer_layout(x_cl: int, y_cl: int, rects: int,
                  images: int, has_timeline: bool,
                  has_table: bool) -> str:
    """根据结构特征推断 layout_type"""
    if has_table:
        return 'table_page'

    if has_timeline:
        return 'timeline'

    if images > 0:
        if x_cl >= 2:
            return 'lr_split_imagetext'
        return 'standard'

    if x_cl >= 3:
        return 'grid'

    if x_cl == 2:
        if y_cl >= 3:
            return 'lr_split_dense'
        return 'lr_split_balanced'

    if x_cl == 1:
        if y_cl >= 3:
            return 'card_list'
        return 'standard'

    # 矩形多但无明确列
    if rects > 15:
        return 'grid'

    return 'standard'


# ─────────────────────────────────────────────────────────────────
# 变体→layout_type 映射（含 Path B 页型推荐）
# ─────────────────────────────────────────────────────────────────

LAYOUT_TO_PPTX_PAGE_TYPE = {
    # layout_type → pptx_components 页型函数名
    'lr_split_imagetext': 'two_column',
    'lr_split_balanced':  'two_column',
    'lr_split_dense':     'two_column',
    'lr_split_righttitle': 'two_column',
    'lr_split_lefttitle':  'two_column',
    'standard':           'text_section',
    'card_list':          'card_grid',
    'grid':               'card_grid',
    'table_page':         'data_table',
    'timeline':           'timeline',
    'kpi_dashboard':      'kpi_dashboard',
    'attack_chain':       'attack_chain',
    'red_blue':           'red_blue',
    'vuln_matrix':        'vuln_matrix',
}

# 内容语义关键词 → layout_type 推荐
KEYWORD_LAYOUT_MAP = {
    # 攻击/路径/kill chain
    '攻击链': 'attack_chain', 'kill chain': 'attack_chain',
    '攻击路径': 'attack_chain', '攻击阶段': 'attack_chain',
    # 红蓝对抗
    '红蓝': 'red_blue', '攻防': 'red_blue',
    '攻防对比': 'red_blue', '对抗': 'red_blue',
    # KPI/态势/总览
    '态势': 'kpi_dashboard', '总览': 'kpi_dashboard',
    'KPI': 'kpi_dashboard', '仪表盘': 'kpi_dashboard',
    '概览': 'kpi_dashboard',
    # 漏洞清单/矩阵
    '漏洞清单': 'vuln_matrix', '漏洞矩阵': 'vuln_matrix',
    '漏洞列表': 'vuln_matrix', 'Vulnerability': 'vuln_matrix',
    # 表格/数据
    '表格': 'table_page', '清单': 'table_page',
    '对比表': 'table_page', '数据表': 'table_page',
    # 时间线
    '时间线': 'timeline', 'Timeline': 'timeline',
    '时间轴': 'timeline', '进展': 'timeline',
    # 网格/卡片
    '网格': 'grid', '卡片': 'grid',
    '能力': 'grid', '模块': 'grid',
}


def recommend_layout(page_title: str = '',
                     page_subtitle: str = '',
                     content_type: str = '',
                     variant_index: Dict = None) -> Dict:
    """
    根据页面标题/副标题/内容类型推荐 layout_type 和 Path B 页型。

    优先级：
      1. 关键词匹配（最精准）
      2. content_type 直映射
      3. 默认 lr_split_imagetext（安服绝对主导布局）

    返回:
      {
        'layout_type': str,
        'pptx_page_type': str,
        'variant_file': str | None,   # 推荐的变体文件名
        'match_method': str,           # 'keyword' / 'content_type' / 'default'
      }
    """
    combined = f'{page_title} {page_subtitle}'.lower()

    # 1. 关键词匹配
    for kw, lt in KEYWORD_LAYOUT_MAP.items():
        if kw.lower() in combined:
            pptx_type = LAYOUT_TO_PPTX_PAGE_TYPE.get(lt, 'card_grid')
            variant_file = _pick_variant(lt, variant_index)
            return {
                'layout_type': lt,
                'pptx_page_type': pptx_type,
                'variant_file': variant_file,
                'match_method': 'keyword',
            }

    # 2. content_type 直映射
    if content_type:
        pptx_type = LAYOUT_TO_PPTX_PAGE_TYPE.get(content_type, 'card_grid')
        variant_file = _pick_variant(content_type, variant_index)
        return {
            'layout_type': content_type,
            'pptx_page_type': pptx_type,
            'variant_file': variant_file,
            'match_method': 'content_type',
        }

    # 3. 默认
    return {
        'layout_type': 'lr_split_imagetext',
        'pptx_page_type': 'two_column',
        'variant_file': _pick_variant('lr_split_imagetext', variant_index),
        'match_method': 'default',
    }


def _pick_variant(layout_type: str, variant_index: Dict = None) -> Optional[str]:
    """从 variant_index 中选择最匹配的变体文件"""
    if not variant_index:
        return None
    mapping = variant_index.get('layout_mapping', {})
    variants = mapping.get(layout_type, [])
    if variants:
        # 返回矩形数最多（信息密度最高）的变体
        return variants[0].get('file')
    return None


# ─────────────────────────────────────────────────────────────────
# 索引生成
# ─────────────────────────────────────────────────────────────────

def build_variant_index(template_dir: Path) -> Dict:
    """
    扫描 extracted_variants/ 并生成完整的变体索引。

    返回:
      {
        'template': str,
        'total_variants': int,
        'variants': [ {file, rects, texts, ...}, ... ],
        'layout_mapping': {
          'lr_split_imagetext': [ {file, rects}, ... ],
          'grid': [ {file, rects}, ... ],
          ...
        },
        'pptx_page_type_map': {
          'lr_split_imagetext': 'two_column',
          ...
        }
      }
    """
    ev_dir = template_dir / 'extracted_variants'
    if not ev_dir.exists():
        return {
            'template': template_dir.name,
            'total_variants': 0,
            'variants': [],
            'layout_mapping': {},
            'pptx_page_type_map': LAYOUT_TO_PPTX_PAGE_TYPE,
        }

    # 扫描并分析所有 SVG
    variants = []
    for svg_file in sorted(ev_dir.glob('*.svg')):
        info = parse_svg_structure(svg_file)
        if 'error' not in info:
            variants.append(info)

    # 按 layout_hint 分组
    layout_mapping: Dict[str, List] = {}
    for v in variants:
        lt = v.get('layout_hint', 'standard')
        layout_mapping.setdefault(lt, []).append({
            'file': v['file'],
            'rects': v['rects'],
            'x_clusters': v['x_clusters'],
            'y_clusters': v['y_clusters'],
        })

    # 每组按矩形数降序排列（信息密度高的优先）
    for lt in layout_mapping:
        layout_mapping[lt].sort(key=lambda x: x['rects'], reverse=True)

    return {
        'template': template_dir.name,
        'total_variants': len(variants),
        'variants': variants,
        'layout_mapping': layout_mapping,
        'pptx_page_type_map': LAYOUT_TO_PPTX_PAGE_TYPE,
    }


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description='变体路由器：分析 extracted_variants/ 并生成 variant_index.json')
    ap.add_argument('template_dir',
                    help='模板目录路径（如 templates/layouts/chaitin_anfu）')
    ap.add_argument('-o', '--output', default='variant_index.json',
                    help='输出索引文件名（默认: variant_index.json）')
    ap.add_argument('--list', action='store_true',
                    help='仅列出变体映射表')
    args = ap.parse_args()

    template_dir = Path(args.template_dir)
    if not template_dir.exists():
        print(f'⚠ 模板目录不存在: {template_dir}')
        sys.exit(1)

    index = build_variant_index(template_dir)

    # 保存索引
    out_path = template_dir / args.output
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    print(f'✓ 变体索引已生成: {out_path}')
    print(f'  变体数: {index["total_variants"]}')

    if args.list:
        print('\n── layout_type → 变体映射 ──')
        for lt, items in index.get('layout_mapping', {}).items():
            pptx_type = LAYOUT_TO_PPTX_PAGE_TYPE.get(lt, '?')
            print(f'\n  {lt} → pptx: {pptx_type}')
            for it in items:
                print(f'    {it["file"]}  (rects={it["rects"]}, cols={it["x_clusters"]}, rows={it["y_clusters"]})')

        print('\n── 关键词→layout_type 映射 ──')
        for kw, lt in sorted(KEYWORD_LAYOUT_MAP.items(), key=lambda x: x[1]):
            pptx_type = LAYOUT_TO_PPTX_PAGE_TYPE.get(lt, '?')
            print(f'  "{kw}" → {lt} → pptx: {pptx_type}')


if __name__ == '__main__':
    main()
