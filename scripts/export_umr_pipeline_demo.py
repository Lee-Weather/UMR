"""Embed existing local UMR artifacts into the team's standalone HTML page."""

from __future__ import annotations

import base64
import html
import io
import json
import re
from pathlib import Path

import numpy as np
import imageio.v3 as iio
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
HTML_DIR = ROOT / "czy" / "html"
PAGE = HTML_DIR / "UMR_pipeline_组内分享.html"
DATASET = ROOT / "data/correspondence_weichai_f1_29_smplx_neutral_betas_c4eb7419e9.npz"
SLOTS = ROOT / "output/correspondence_weichai_f1_29_smplx_neutral_betas_c4eb7419e9/correspondence_slots_final.npz"


def load_demo_data() -> dict:
    with np.load(DATASET, allow_pickle=False) as data:
        names = data["names"].tolist()
        raw = data["points"].copy()
    with np.load(SLOTS, allow_pickle=False) as data:
        slot_names = data["names"].tolist()
        learned = data["reconstructed_slots"][[slot_names.index(n) for n in names]]
    return {"raw": raw.round(5).tolist(), "slots": learned.round(5).tolist(), "names": names}


def video_card(robot: str, stem: str, folder: str, config: str) -> str:
    result = ROOT / "umr_data" / folder / (stem + ".npz")
    video = result.with_suffix(".mp4")
    with np.load(result, allow_pickle=False) as data:
        frames, nq = data["qpos"].shape
        fps = float(np.asarray(data["fps"]).reshape(-1)[0])
        source_key = str(np.asarray(data["source_sequence_key"]).item())
    encoded = base64.b64encode(video.read_bytes()).decode("ascii")
    frame = Image.fromarray(iio.imread(video, index=min(60, frames-1), plugin="FFMPEG"))
    frame.thumbnail((960, 540))
    poster_buffer = io.BytesIO()
    frame.save(poster_buffer, format="JPEG", quality=88)
    poster = base64.b64encode(poster_buffer.getvalue()).decode("ascii")
    cmd = (
        "python scripts/retarget_smpl_to_humanoid_surface_vector.py\n"
        f"  --config configs/{config}.json\n"
        f"  --data sample_data/ACCAD/Female1Walking_c3d/{source_key}.npz\n"
        f"  --seq-key {source_key}\n"
        f"  --out umr_data/{folder}/{stem}.npz"
    )
    cmd = " ".join(cmd.split())
    return f'''<article class="box demo-video-card"><h3>{robot} · 站立到行走</h3>
<p class="small">{frames} 帧 · {fps:g} FPS · {frames / fps:.2f} 秒 · qpos ({frames}, {nq})</p>
<video controls playsinline preload="metadata" aria-label="{robot} 本地重定向结果" poster="data:image/jpeg;base64,{poster}" src="data:video/mp4;base64,{encoded}">浏览器不支持视频播放。</video>
<p class="small demo-path">本地结果：<code>umr_data/{folder}/{stem}.npz</code></p>
<details><summary>查看复现命令</summary><p class="small">在项目根目录执行以下单行命令。</p><pre class="code">{html.escape(cmd)}</pre></details></article>'''


CSS = '''
/* LOCAL_UMR_DEMO_STYLE */
.local-demo{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fff}
.demo-tabs{display:flex;flex-wrap:wrap;gap:8px;padding:18px;border-bottom:1px solid var(--line)}
.demo-tabs button,.demo-reset{font:inherit;font-size:13px;border:1px solid #a7c5af;background:#fff;color:var(--green);border-radius:7px;padding:9px 14px;cursor:pointer}
.demo-tabs button[aria-selected="true"]{background:var(--green);color:white;border-color:var(--green)}
.demo-body{padding:22px}.demo-controls{display:flex;align-items:center;gap:18px;flex-wrap:wrap;font-size:13px;color:#496354;margin-bottom:16px}
.demo-controls label{display:flex;align-items:center;gap:8px}.demo-controls input{accent-color:var(--green)}
.demo-controls input[type=range]{width:150px}.demo-reset{margin-left:auto;padding:6px 12px}
.demo-canvas{width:100%;height:440px;display:block;background:#f0f5ef;border-radius:9px;touch-action:none;cursor:grab}
.demo-canvas:active{cursor:grabbing}.demo-status{min-height:48px;margin:14px 0 0;font-size:13px;color:var(--muted)}
.demo-video-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px;margin-top:26px}
.demo-video-card video{width:100%;display:block;border-radius:8px;background:#172c25;aspect-ratio:16/9;object-fit:contain}
.demo-path{margin-top:14px;overflow-wrap:anywhere}.demo-video-card details{font-size:13px}.demo-video-card summary{cursor:pointer;color:var(--green);font-weight:700}
.demo-video-card .code{font-size:11px}.local-demo-foot{margin-top:20px;font-size:13px;color:var(--muted)}
@media(max-width:760px){.demo-video-grid{grid-template-columns:1fr}.demo-canvas{height:350px}.demo-body{padding:14px}.demo-reset{margin-left:0}}
/* END_LOCAL_UMR_DEMO_STYLE */
'''


JS = r'''
(() => {
  'use strict';
  const d = JSON.parse(document.getElementById('umr-local-data').textContent);
  const canvas = document.getElementById('umr-points');
  const ctx = canvas.getContext('2d');
  const slider = document.getElementById('umr-slot');
  const lines = document.getElementById('umr-lines');
  const output = document.getElementById('umr-slot-value');
  const status = document.getElementById('umr-demo-status');
  const buttons = [...document.querySelectorAll('[data-umr-stage]')];
  let mode = 'raw', yaw = 0.12, pitch = 0.02, drag = null;
  const normalize = clouds => clouds.map(points => {
    const ys = points.map(p => p[1]);
    const lo = Math.min(...ys), hi = Math.max(...ys);
    return points.map(p => [p[0] / (hi-lo), (p[1]-(hi+lo)/2) / (hi-lo), p[2] / (hi-lo)]);
  });
  const clouds = {raw:normalize(d.raw),slots:normalize(d.slots)};
  function render() {
    const w = canvas.clientWidth, h = canvas.clientHeight, ratio = Math.min(window.devicePixelRatio || 1, 2);
    if (canvas.width !== Math.round(w*ratio) || canvas.height !== Math.round(h*ratio)) {
      canvas.width = Math.round(w*ratio); canvas.height = Math.round(h*ratio);
    }
    ctx.setTransform(ratio,0,0,ratio,0,0); ctx.clearRect(0,0,w,h);
    const s = Math.min(h*0.74,w*0.45), cy = h*0.53;
    const centers = [w*0.26,w*0.74], selected = Number(slider.value);
    const cp = Math.cos(pitch), sp = Math.sin(pitch), co = Math.cos(yaw), si = Math.sin(yaw);
    function project(p,k) {
      const x = p[0]*co+p[2]*si, z = -p[0]*si+p[2]*co;
      return [centers[k]+x*s, cy-(p[1]*cp-z*sp)*s];
    }
    ctx.fillStyle='#456552'; ctx.font='600 13px system-ui';ctx.textAlign='center';
    ctx.fillText('SMPL-X 人体',centers[0],28);ctx.fillText('Weichai F1-29',centers[1],28);
    const points = clouds[mode];
    if(mode==='slots' && lines.checked) {
      ctx.strokeStyle='rgba(83,137,101,.16)';ctx.lineWidth=0.8;
      for(let i=0;i<points[0].length;i+=96) {
        const a=project(points[0][i],0),b=project(points[1][i],1);
        ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();
      }
    }
    points.forEach((cloud,k)=>cloud.forEach((p,i)=>{
      const pos=project(p,k);
      const t=clouds.slots[0][i][1]+0.5;
      ctx.fillStyle=mode==='raw'?(k?'#407a63':'#7c9888'):`hsl(${Math.round(25+t*220)},55%,43%)`;
      ctx.beginPath();ctx.arc(pos[0],pos[1],w<600?0.85:1.15,0,Math.PI*2);ctx.fill();
    }));
    if(mode==='slots') {
      const a=project(points[0][selected],0), b=project(points[1][selected],1);
      ctx.strokeStyle='#d56c36';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();
      [a,b].forEach(pos=>{ctx.fillStyle='#d56c36';ctx.beginPath();ctx.arc(pos[0],pos[1],5,0,Math.PI*2);ctx.fill();ctx.fillStyle='#172823';ctx.textAlign='left';ctx.fillText('#'+selected,pos[0]+8,pos[1]-8);});
    }
    ctx.fillStyle='#6b8273';ctx.font='12px system-ui';ctx.textAlign='center';ctx.fillText('拖动旋转 · 各模板按自身高度归一化显示',w/2,h-14);
  }
  function setMode(next) {
    mode=next;
    buttons.forEach(b=>b.setAttribute('aria-selected',String(b.dataset.umrStage===mode)));
    slider.disabled=mode==='raw';lines.disabled=mode==='raw';
    status.textContent=mode==='raw'?'BUILD · 本地点云数据集：两组独立采样的 4096 点。此时点序号没有对应语义。':'TRAIN · 本地 reconstructed_slots：同一索引用相同颜色表示。橙线高亮当前 slot；拖动滑块可检查不同位置的对应。';
    render();
  }
  buttons.forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.umrStage)));
  document.querySelectorAll('[data-umr-show]').forEach(link=>link.addEventListener('click',()=>setMode(link.dataset.umrShow)));
  slider.addEventListener('input',()=>{output.textContent=slider.value;render();});
  lines.addEventListener('change',render);
  document.getElementById('umr-reset').addEventListener('click',()=>{yaw=0.12;pitch=0.02;render();});
  canvas.addEventListener('pointerdown',e=>{drag=[e.clientX,e.clientY];canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointermove',e=>{if(!drag)return;yaw+=(e.clientX-drag[0])*0.008;pitch=Math.max(-1.2,Math.min(1.2,pitch+(e.clientY-drag[1])*0.008));drag=[e.clientX,e.clientY];render();});
  canvas.addEventListener('pointerup',()=>drag=null);canvas.addEventListener('pointercancel',()=>drag=null);
  new ResizeObserver(render).observe(canvas);setMode('raw');
})();
'''


def main() -> None:
    source = PAGE.read_text(encoding="utf-8-sig")
    data = load_demo_data()
    f1 = video_card("Weichai F1-29", "B1_stand_to_walk_weichai_f1_29", "F1/accad_walking", "weichai_f1_29_base")
    x1 = video_card("XYBER X1", "B1_stand_to_walk_x1", "X1/accad_walking", "xyber_x1_base")
    section = f'''<section class="section" id="demo"><div class="section-head"><div class="label">03 / LOCAL CODE DEMO</div><div><h2>查看本地管线的真实产物</h2><p class="lead">从本地 NPZ 读取采样点云和训练 slots，在下面旋转、切换并检查对应关系，再观看 F1 / X1 的实际动作回放。</p></div></div>
<div class="local-demo"><div class="demo-tabs" role="tablist" aria-label="切换本地点云产物"><button type="button" role="tab" aria-controls="umr-demo-panel" data-umr-stage="raw" aria-selected="true">01 · 构建后的采样点云</button><button type="button" role="tab" aria-controls="umr-demo-panel" data-umr-stage="slots" aria-selected="false">02 · 训练后的对应 slots</button></div>
<div class="demo-body" id="umr-demo-panel"><div class="demo-controls"><label>高亮 slot <input id="umr-slot" type="range" min="0" max="4095" value="2048" disabled><output id="umr-slot-value">2048</output></label><label><input id="umr-lines" type="checkbox" disabled>显示稀疏对应连线</label><button type="button" class="demo-reset" id="umr-reset">重置视角</button></div><canvas id="umr-points" class="demo-canvas" aria-label="人体和 F1 机器人的真实点云。拖动旋转，切换训练前后数据。"></canvas><p id="umr-demo-status" class="demo-status" aria-live="polite"></p></div></div>
<p class="local-demo-foot">点云来自 <code>data/correspondence_weichai_f1_29_smplx_neutral_betas_c4eb7419e9.npz</code>；对应关系来自同名 output 目录下的 <code>correspondence_slots_final.npz</code>。颜色和连线展示学习结果中的共同索引，并非人工语义标注。</p>
<h3 style="margin-top:34px">03 · 本地求解结果回放</h3><p class="small">同一 ACCAD “站立到行走”动作在两台机器人上的输出；以下视频为仓库中已有的本地渲染结果。</p><div class="demo-video-grid">{f1}{x1}</div>
<details style="margin-top:24px"><summary>在本地打开 MuJoCo 查看器</summary><p class="small">在项目根目录运行，可直接播放 NPZ 关节轨迹。</p><pre class="code">python scripts/visualize_robot_retarget_result.py --result umr_data/F1/accad_walking/B1_stand_to_walk_weichai_f1_29.npz --play</pre></details>
<div class="note">本页展示实际代码产物。点云可交互查看，视频可播放与拖动进度；采样、训练和重定向由仓库中的 Python 代码执行。数据与视频已嵌入 HTML，分享这个文件即可离线演示。</div>
<noscript><p class="note">请启用 JavaScript 查看交互点云。视频仍可通过浏览器原生控件播放。</p></noscript></section>'''
    source, count = re.subn(r'<section class="section" id="demo">.*?</section>', lambda _: section, source, count=1, flags=re.S)
    if count != 1:
        # Newer layouts place point data and motion results next to their principles.
        point_view = re.search(r'<div class="local-demo">.*?<p class="local-demo-foot">.*?</p>', section, re.S)
        motion_view = re.search(r'<div class="demo-video-grid">.*?</div>', section, re.S)
        if point_view is None or motion_view is None:
            raise RuntimeError("Cannot locate generated point and motion views")
        source, point_count = re.subn(
            r'<!-- INTEGRATED_POINT_VIEW -->.*?<!-- END_INTEGRATED_POINT_VIEW -->',
            lambda _: '<!-- INTEGRATED_POINT_VIEW -->' + point_view[0] + '<!-- END_INTEGRATED_POINT_VIEW -->',
            source, count=1, flags=re.S,
        )
        source, motion_count = re.subn(
            r'<!-- INTEGRATED_MOTION_VIEW -->.*?<!-- END_INTEGRATED_MOTION_VIEW -->',
            lambda _: '<!-- INTEGRATED_MOTION_VIEW -->' + motion_view[0] + '<!-- END_INTEGRATED_MOTION_VIEW -->',
            source, count=1, flags=re.S,
        )
        if point_count != 1 or motion_count != 1:
            raise RuntimeError("Expected standalone demo section or integrated product markers")
    source = source.replace('href="#demo">官方演示', 'href="#demo">本地演示')
    source = re.sub(r'/\* LOCAL_UMR_DEMO_STYLE \*/.*?/\* END_LOCAL_UMR_DEMO_STYLE \*/', '', source, flags=re.S)
    source = source.replace('</style>', CSS + '\n</style>', 1)
    source = re.sub(r'<!-- LOCAL_UMR_DEMO_DATA -->.*?<!-- END_LOCAL_UMR_DEMO_DATA -->', '', source, flags=re.S)
    embedded = '<!-- LOCAL_UMR_DEMO_DATA --><script type="application/json" id="umr-local-data">' + json.dumps(data, separators=(',', ':')) + '</script><script>' + JS + '</script><!-- END_LOCAL_UMR_DEMO_DATA -->'
    source = source.replace('</body>', embedded + '</body>', 1)
    PAGE.write_text(source, encoding="utf-8")
    print(f"Updated {PAGE.name}: {PAGE.stat().st_size / 1024 / 1024:.1f} MiB; standalone local demo")


if __name__ == "__main__":
    main()
