"""F1 x HOI sources: HiPHI get-up and OmniContact soccer kick.

Consolidates the two legacy launchers (batch_retarget_weichai.py and
run_weichai_motions.py), which did the same two motions via different code paths
and both wrote into the since-removed output/weichai_f1_29_retarget/.

Outputs land next to the rest of the F1 results:
    umr_data/F1/hiphi_getting_up/
    umr_data/F1/omnicontact_kick/

Run:  python batch_f1_hoi.py                 # both motions
      python batch_f1_hoi.py --which kick
      python batch_f1_hoi.py --no-video --force
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
PYTHON = sys.executable
CONFIG = ROOT / "configs" / "weichai_f1_29_base.json"
OUT_BASE = ROOT / "umr_data" / "F1"
SUFFIX = "_smplx_weichai_f1_29"
LFS_MAGIC = b"version https://git-lfs.github.com/spec/v1"

MOTIONS = {
    "hiphi": {
        "name": "hiphi_getting_up",
        "data": "sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz",
        "seq_key": "motion_actor_smplx",
        "out_dir": "hiphi_getting_up",
        "out_stem": "Getting_up-get_up_0004",
        "desc": "HiPHI 起身",
    },
    "kick": {
        "name": "omnicontact_kick",
        "data": "sample_data/omnicontact/soccer/case3_kick_right/20260330000586_1_1775269234",
        "seq_key": "20260330000586_1_1775269234",
        "out_dir": "omnicontact_kick",
        "out_stem": "case3_kick_right",
        "desc": "OmniContact 射门",
    },
}


def is_lfs_pointer(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size > 400:
        return False
    with path.open("rb") as fh:
        return fh.read(len(LFS_MAGIC)) == LFS_MAGIC


def run(cmd: list[str]) -> tuple[int, float]:
    start = time.time()
    code = subprocess.run(cmd, cwd=ROOT).returncode
    return code, time.time() - start


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--which", choices=["hiphi", "kick", "both"], default="both")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--force", action="store_true", help="重新重定向，即使 npz 已存在")
    args = ap.parse_args()

    keys = ["hiphi", "kick"] if args.which == "both" else [args.which]
    results: list[dict] = []
    print(f"config={CONFIG.relative_to(ROOT)}  out={OUT_BASE.relative_to(ROOT)}  video={not args.no_video}")

    for key in keys:
        m = MOTIONS[key]
        data = ROOT / m["data"]
        out = OUT_BASE / m["out_dir"] / f"{m['out_stem']}{SUFFIX}.npz"
        rec = {"source": key, "desc": m["desc"], "data": m["data"], "out": str(out.relative_to(ROOT))}
        out.parent.mkdir(parents=True, exist_ok=True)

        if is_lfs_pointer(data):
            rec["retarget"] = "blocked-lfs-pointer"
            print(f"[{key}] 源数据仍是 LFS 指针: {m['data']}")
            print(f"        先执行: git lfs pull --include=\"{Path(m['data']).parent.as_posix()}/**\"")
            results.append(rec)
            continue

        if out.exists() and not args.force:
            print(f"[{key}] skip (exists) {out.relative_to(ROOT)}  ({m['desc']})")
            rec["retarget"] = "skipped"
        else:
            print(f"[{key}] retarget {m['desc']} ...", flush=True)
            code, dt = run([
                PYTHON, str(SCRIPTS / "retarget_smpl_to_humanoid_surface_vector.py"),
                "--config", str(CONFIG),
                "--data", str(data),
                "--seq-key", m["seq_key"],
                "--out", str(out),
            ])
            rec["retarget"] = "ok" if code == 0 else f"fail({code})"
            rec["retarget_sec"] = round(dt, 1)
            print(f"[{key}]   -> {rec['retarget']} in {dt:.0f}s", flush=True)
        results.append(rec)

    if not args.no_video:
        for key, rec in zip(keys, results):
            if rec.get("retarget") not in ("ok", "skipped"):
                continue
            out = ROOT / rec["out"]
            vid = out.with_suffix(".mp4")
            rec["video"] = "skipped"
            if not out.exists() or vid.exists():
                continue
            print(f"[{key}] record video ...", flush=True)
            code, dt = run([
                PYTHON, str(SCRIPTS / "visualize_robot_retarget_result.py"),
                "--result", str(out),
                "--record-video", str(vid),   # 必须带路径（旧脚本这里漏了，argparse 直接报错）
                "--play",
            ])
            rec["video"] = "ok" if code == 0 else f"fail({code})"
            rec["video_sec"] = round(dt, 1)
            print(f"[{key}]   -> {rec['video']} in {dt:.0f}s", flush=True)

    summary = OUT_BASE / "_hoi_summary.json"
    existing = {}
    if summary.exists():
        try:
            existing = {r["source"]: r for r in json.loads(summary.read_text(encoding="utf-8"))}
        except Exception:
            existing = {}
    existing.update({r["source"]: r for r in results})
    summary.write_text(json.dumps(list(existing.values()), ensure_ascii=False, indent=2), encoding="utf-8")

    ok = sum(1 for r in results if r.get("retarget") in ("ok", "skipped"))
    blocked = [r["source"] for r in results if r.get("retarget") == "blocked-lfs-pointer"]
    print("=" * 64)
    print(f"ok={ok}/{len(results)}" + (f"  被 LFS 指针阻塞: {blocked}" if blocked else ""))
    return 0 if ok == len(results) else (2 if blocked else 1)


if __name__ == "__main__":
    raise SystemExit(main())