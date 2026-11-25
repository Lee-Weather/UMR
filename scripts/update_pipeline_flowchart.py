"""Add an offline SVG flowchart to the team UMR page."""
from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / "czy" / "html"
PAGE = HTML_DIR / "UMR_pipeline_组内分享.html"
SVG_FILE = HTML_DIR / "UMR_pipeline_流程图.svg"


def node(x, y, w, title, subtitle, kind="", h=82):
    return f'''<g class="node {kind}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12"/><text x="{x+w/2}" y="{y+32}" class="node-title">{html.escape(title)}</text><text x="{x+w/2}" y="{y+57}" class="node-sub">{html.escape(subtitle)}</text></g>'''


def arrow(path, dashed=False):
    return f'<path class="edge{" reuse" if dashed else ""}" d="{path}" marker-end="url(#umr-arrow)"/>'


svg = '''<svg xmlns="http://www.w3.org/2000/svg" id="umr-pipeline-chart" viewBox="0 0 1120 1450" role="img" aria-labelledby="umr-flow-title umr-flow-desc">
<title id="umr-flow-title">UMR 本地管线完整流程图</title><desc id="umr-flow-desc">人体和机器人模板经过表面采样、数据集构建及自编码器训练得到对应 slots；已有兼容 slots 可直接复用。人体运动和绑定后的 slots 进入逐帧优化，得到机器人轨迹，经 LQR 滤波保存为 NPZ 并可视化。</desc>
<defs><marker id="umr-arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0 L9 4.5 L0 9 Z" fill="#668b77"/></marker></defs>
<style>
text{font-family:'Microsoft YaHei','PingFang SC',system-ui,sans-serif;text-anchor:middle;fill:#233e30}
.node rect{fill:#fff;stroke:#b5cbb9;stroke-width:1.5}.node-title{font-size:19px;font-weight:700}.node-sub{font-size:13px;fill:#607667}
.primary rect{fill:#215d49;stroke:#215d49}.primary .node-title{fill:#fff}.primary .node-sub{fill:#d4e8d8}
.artifact rect{fill:#e3efdf;stroke:#9abb9c}.existing rect{fill:#f8f4e9;stroke:#cdb88a;stroke-dasharray:5 4}
.edge{fill:none;stroke:#668b77;stroke-width:2}.reuse{stroke-dasharray:7 5}.zone{fill:#f1f6ef;stroke:#d5e3d3}.zone-b{fill:#edf4f1;stroke:#d5e3d3}
.zone-title{text-anchor:start;font-size:15px;letter-spacing:1px;font-weight:700;fill:#3c7554}.label{font-size:13px;fill:#607667}.small{font-size:12px;fill:#617365}
</style>
<rect width="1120" height="1450" rx="16" fill="#fff"/>
<rect class="zone" x="24" y="22" width="758" height="600" rx="16"/>
<text class="zone-title" x="48" y="56">A / 模板准备与对应关系学习</text>
<rect class="zone-b" x="24" y="644" width="1072" height="566" rx="16"/>
<text class="zone-title" x="48" y="677">B / 每段动作的重定向</text>
'''
svg += node(60, 90, 300, "人体参考模板", "SMPL-X · gender / betas")
svg += node(440, 90, 300, "机器人参考模板", "MJCF · T-pose · 中心与坐标系")
svg += node(810, 90, 270, "人体运动序列", "逐帧姿态 · 位移 · 帧率")
svg += arrow("M210 172 V210 H400 V238")
svg += arrow("M590 172 V210 H400")
svg += node(165, 240, 470, "01 · BUILD：表面采样", "参考姿态对齐 → 外表面采样 · 默认 4096 点", "primary")
svg += arrow("M400 322 V350 H225 V378")
svg += node(60, 380, 330, "对应关系数据集", "data/correspondence_*.npz", "artifact")
svg += arrow("M390 421 H438")
svg += node(440, 380, 300, "02 · TRAIN：学习对应", "共享模板 + 形状残差 · 默认 500 epochs", "primary")
svg += arrow("M590 462 V518")
svg += node(440, 520, 300, "对应 slots", "统一索引 · slots NPZ + checkpoint", "artifact")
svg += node(60, 520, 300, "已有兼容 slots", "复用缓存，跳过采样与训练", "existing")
svg += arrow("M360 561 H438", True)
svg += arrow("M590 602 V706")
svg += node(440, 708, 300, "表面绑定与体型适配", "绑定人体 / 机器人表面 · 可跨 beta 复用")
svg += arrow("M945 172 V706")
svg += node(810, 708, 270, "人体表面运动与缩放", "目标点位 / 方向 · 身高比例适配")
svg += arrow("M740 749 H808")
svg += arrow("M590 790 V832 H600 V858")
svg += arrow("M945 790 V900 H802")
svg += node(400, 860, 400, "03 · RETARGET：逐帧优化", "表面匹配 + 接触 + 平滑 + 启用的约束", "primary")
svg += arrow("M400 901 H310 V1006 H398")
svg += node(400, 966, 400, "更新机器人姿态 qpos", "以上一帧初始化 · 连续求解整个序列")
svg += arrow("M800 1007 H853 V956 H704 V944", True)
svg += '<text class="label" x="904" y="991">下一帧</text>'
svg += arrow("M600 1048 V1096")
svg += node(400, 1098, 400, "轨迹后处理", "当前配置：LQR 轨迹滤波")
svg += arrow("M600 1180 V1256")
svg += node(400, 1258, 400, "保存机器人动作", "NPZ：qpos · fps · 机器人 / 源数据元信息", "artifact")
svg += arrow("M800 1299 H838")
svg += node(840, 1258, 240, "查看与分享", "MuJoCo 播放 · 可选 MP4")
svg += '<text class="small" x="548" y="1390">实线：主要数据流　　虚线：兼容缓存复用 / 帧间循环　　深绿色：核心执行阶段</text>'
svg += '<text class="small" x="548" y="1418">本图依据当前仓库实现；具体损失项、约束和后处理由配置决定。</text></svg>'
svg = re.sub(r'<style>(.*?)</style>', lambda m: '<style>' + re.sub(r'([^{}]+)\{', lambda rule: ','.join('#umr-pipeline-chart ' + selector.strip() for selector in rule[1].split(',')) + '{', m[1]) + '</style>', svg, flags=re.S)

SVG_FILE.write_text(svg, encoding="utf-8")
source = PAGE.read_text(encoding="utf-8")
overview = '''<section class="section" id="overview"><div class="section-head"><div class="label">01 / PIPELINE MAP</div><div><h2>从人体动作到机器人轨迹</h2><p class="lead">沿箭头阅读完整数据流：上半部分建立模板对应，下半部分处理每段动作。已有兼容 slots 时，可直接进入表面绑定与逐帧求解。</p></div></div><div class="pipeline-map">''' + svg + '''</div><p class="small" style="margin-top:14px">流程图可在手机上横向滑动查看。真实点云、slots 与动作结果已放在下方核心原理的对应步骤中。</p></section>'''
source, count = re.subn(r'<section class="section" id="overview">.*?</section>', lambda _: overview, source, count=1, flags=re.S)
if count != 1:
    raise RuntimeError("Overview section not found")
css = '\n/* PIPELINE_MAP */\n.pipeline-map{background:white;border:1px solid var(--line);border-radius:14px;overflow-x:auto}.pipeline-map svg{display:block;width:100%;min-width:750px;height:auto}.pipeline-map svg .node{padding:0;background:none}.pipeline-map svg .label{letter-spacing:0}@media print{.pipeline-map svg{min-width:0}.pipeline-map{break-inside:avoid}}\n/* END_PIPELINE_MAP */\n'
source = re.sub(r'/\* PIPELINE_MAP \*/.*?/\* END_PIPELINE_MAP \*/', '', source, flags=re.S)
source = source.replace('</style>', css + '</style>', 1)
source = source.replace('href="#overview">流程概览', 'href="#overview">完整流程图')
PAGE.write_text(source, encoding="utf-8")
print("Updated HTML overview and exported standalone SVG")
