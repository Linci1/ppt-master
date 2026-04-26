# 图片→页面自动映射参考

> 面向 Strategist 和 Executor 的图片到页面分配指南。
> 在 Step3 图片提取完成后，本参考指导 Step4 Strategist 如何将图片合理分配到各正文页。

## 1. 图片分类规则

### 1.1 基于尺寸分类

```
1280×720 画布中的图片嵌入标准面积 ≤ 15% (≈ 138,240 px²)
┌─────────────────────────────────────────────────────┐
│ 类型      │ 宽范围     │ 面积上限   │ 最佳嵌入方式  │
├─────────────────────────────────────────────────────┤
│ 微型      │ <200px     │ 10,000 px² │ 行内图标/徽章  │
│ 小型      │ 200-599px  │ 80,000 px² │ img_right 主导  │
│ 中型      │ 600-1199px │ 200,000 px²│ img_bottom/宽图 │
│ 大型      │ ≥1200px    │ 不限制     │ 需缩小至 ≤300px │
│ 正方形    │ 1:1 比例   │ —          │ 居中/卡片配图   │
│ 宽屏      │ >1.5:1     │ —          │ 底部通栏        │
│ 竖屏      │ <0.7:1     │ —          │ 左/右栏         │
└─────────────────────────────────────────────────────┘
```

### 1.2 实际提取数据参考（长亭安服源文档 211 媒体文件）

```
206 PNG 已提取：
  微型 (<200px):   98 个 (47.6%) — UI 图标、小徽章、操作按钮截图
  小型 (200-599px): 47 个 (22.8%) — 功能截图、弹窗、表格局部
  中型 (600-1199px): 45 个 (21.8%) — 仪表盘、架构图、大表截图
  大型 (≥1200px):  16 个 ( 7.8%) — 全页PPT截图、背景素材

典型尺寸分布:
  101×88 — 微型图标类 (最常见)
  200×200 — 方形图标/Logo
  384×384 — 中型正方形素材
  401×233 — 宽屏功能截图
  582×442 — 小仪表盘
  1024×1024 — 中等架构图
  1487×1125 — 大截图 (需缩小 ≥5x)
```

## 2. 页面类型 → 图片映射表

### 2.1 标准布局映射

| 页面类型 | 推荐图片尺寸 | 推荐数量 | 嵌入位置 | 理由 |
|----------|------------|---------|---------|------|
| `lr_split_imagetext` | 200-600px, 小型截图 | 1-2 | 右栏 y=100~600 | 文字在左，图在右，经典布局 |
| `lr_split_balanced` | 300-800px, 中型 | 1-2 | 右栏居中 | 等宽双栏，图不宜过大 |
| `lr_split_dense` | 100-300px, 微型/小型 | 2-4 | 卡片间嵌入 | 密排卡片，小图点缀 |
| `lr_split_righttitle` | 200-500px, 小型 | 1 | 右侧上部 y=80~200 | 标题在上，图紧随其后 |
| `lr_split_lefttitle` | 200-500px, 小型 | 1 | 左侧上部 y=80~200 | 同上，镜像 |
| `standard` | 300-800px, 中型 | 1 | 居中或右下 | 单栏，图不宜占满 |
| `tb_split` | 400-1000px, 中型/大型 | 1 | 下半部 y=360~680 | 上半文字，下半图片 |
| `table_page` | 150-400px, 小型 | 0-2 | 表旁或表下 | 表格为主，图为辅 |
| `chart_page` | 300-800px, 中型 | 1 | 图表嵌入区 | SVG 自绘为主，真实图为辅 |

### 2.2 套路→图片映射

| 套路 ID | 推荐图片类型 | 图片角色 | 示例匹配 |
|----------|------------|---------|---------|
| `sec-attack-chain` | 攻击路径截图、工具界面、Payload截图 | 关键证据展示 | 200-400px 截图，右侧 |
| `sec-vuln-matrix` | 漏洞界面截图、CVE详情截图、修复前后对比 | 漏洞证据 | 100-200px 小截图，嵌入卡片 |
| `sec-redblue-compare` | 攻击日志 vs 防御告警截图 | 双栏对比证据 | 2张同尺寸截图 (200-400px) |
| `sec-asset-risk` | 资产扫描结果、拓扑图、风险热力图 | 数据可视化 | 400-800px 图表类图片 |
| `sec-compliance-overview` | 合规检查表、达标证明、审计截图 | 合规证据 | 200-500px 表格/证书截图 |
| `sec-timeline` | 事件日志、告警序列、时间轴截图 | 时间线证据 | 200-400px 横向截图 |
| `sec-kpi-dashboard` | 仪表盘截图、趋势图、饼图 | 数据佐证 | 300-600px 图表类图片 |
| `sec-architecture` | 架构图、拓扑图、产品界面截图 | 架构展示 | 500-800px 架构类大图 |

## 3. 自动映射算法

### 3.1 尺寸优先匹配

```
输入: 图片列表 [{name, width, height}]
输出: 页面→图片分配表

算法:
1. 图片按面积降序排列
2. 页面按内容区面积降序排列（lr_split_imagetext > tb_split > standard > ...）
3. 贪婪分配: 大图片 → 大内容区页面, 小图片 → 小区域页面
4. 约束检查:
   - 每页 ≤ 4 张图
   - 图片面积 ≤ 页面内容区面积的 15%
   - 95% 页面至少含 1 张图
5. 不满足约束时，跳过该图片或标记为"备选"
```

### 3.2 语义增强匹配（阶段 2，依赖图片描述）

```
当图片有文字描述时（未来），使用语义匹配:

1. 提取图片关键词（如"漏洞详情""攻击日志""资产列表"）
2. 匹配页面标题关键词
3. 关键词重叠度越高，分配优先级越高
4. 无描述时回退到尺寸优先匹配
```

## 4. Strategist 使用流程

### 4.1 Step3 输出清单（由 Executor/脚本生成）

```json
// images_manifest.json — 放在项目根目录
{
  "extracted_from": "/path/to/source.pptx",
  "total": 211,
  "images": [
    {
      "name": "image10.png",
      "path": "images/image10.png",
      "width": 1024,
      "height": 1024,
      "size_category": "medium",
      "aspect": "square",
      "file_size_kb": 85
    },
    {
      "name": "image101.png",
      "path": "images/image101.png",
      "width": 401,
      "height": 233,
      "size_category": "small",
      "aspect": "wide",
      "file_size_kb": 32
    }
  ]
}
```

### 4.2 Strategist 八项确认中图片分配步骤

```
Step 4.X 图片分配:

1. 遍历 Content Outline 的每一页
2. 根据页面的 layout_type 和 routine_id 查映射表(§2)确定推荐图片尺寸
3. 从 images_manifest.json 中匹配满足尺寸约束的图片
4. 标记已分配的图片（避免重复使用）
5. 写入 design_spec 的 images 字段:
   {
     "page_id": "P05",
     "images": [
       {"name": "image101.png", "position": [850, 120], "max_width": 200}
     ]
   }
6. 检查 95% 覆盖: 统计含图页数 / 总正文页数 ≥ 0.95
```

### 4.3 分配冲突解决

```
冲突: 2 页都适合同一张图
解决优先级:
  1. 套路页面 > 非套路页面 (套路页面对图片依赖更强)
  2. 图片面积更接近页面内容区 15% 上限的 → 优先
  3. 前面页面 > 后面页面 (顺序优先)
  
当图片不够时:
  - 图表页可用 SVG 自绘替代 (chart_page 类型)
  - 纯文字页降级但要标记 review
  - 不要用占位色块
```

## 5. 图片预处理脚本参考

```python
# extract_image_metadata.py — 在 Step3 后运行
import os, struct, json
from pathlib import Path

def get_png_size(path):
    with open(path, 'rb') as f:
        f.seek(16)
        w = struct.unpack('>I', f.read(4))[0]
        h = struct.unpack('>I', f.read(4))[0]
        return w, h

def classify_size(w):
    if w < 200: return "tiny"
    if w < 600: return "small"
    if w < 1200: return "medium"
    return "large"

def classify_aspect(w, h):
    ratio = w / h if h else 1
    if 0.9 < ratio < 1.1: return "square"
    if ratio >= 1.5: return "wide"
    if ratio <= 0.7: return "tall"
    return "normal"

def generate_manifest(images_dir, manifest_path):
    manifest = {"images": []}
    for f in sorted(os.listdir(images_dir)):
        if f.lower().endswith('.png'):
            path = os.path.join(images_dir, f)
            w, h = get_png_size(path)
            manifest["images"].append({
                "name": f,
                "path": f"images/{f}",
                "width": w,
                "height": h,
                "size_category": classify_size(w),
                "aspect": classify_aspect(w, h),
                "file_size_kb": round(os.path.getsize(path) / 1024, 1)
            })
    manifest["total"] = len(manifest["images"])
    with open(manifest_path, 'w') as fp:
        json.dump(manifest, fp, indent=2, ensure_ascii=False)
    print(f"Manifest: {manifest['total']} images → {manifest_path}")

# 用法:
# generate_manifest("projects/my_project/images/", "projects/my_project/images_manifest.json")
```

## 6. 检查清单（Strategist 自检）

```
☐ images_manifest.json 是否存在？
☐ 每页 design_spec 是否指定了 images 字段？
☐ 含图页数 / 总正文页数 ≥ 0.95？
☐ 是否有页指定了不存在的图片？
☐ 是否有图片被超过 2 页引用？
☐ 大型图片 (≥1200px) 是否指定了 max_width ≤ 300？
☐ chart_page 类型的图片是否优先使用 SVG 自绘？
☐ 是否避免使用占位色块代替真实图片？
```

## 7. 当前限制与改进方向

| 限制 | 现状 | 改进方向 |
|------|------|----------|
| 无图片内容理解 | 仅按尺寸匹配 | 接入 `vision_analyze` 或 CLIP 获取图片描述 |
| 无去重检测 | 相似截图可能重复分配 | 添加感知哈希 (pHash) 去重 |
| 无质量筛选 | 低分辨率/模糊图混入 | 添加清晰度评分 (Laplacian variance) |
| 清单手动生成 | 需手写 images_manifest | Step3 结束后自动运行预处理脚本 |
| 交叉引用追踪 | 图片可能被多页引用 | 添加引用计数，防重复 |
