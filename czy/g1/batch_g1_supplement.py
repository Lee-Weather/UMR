"""G1 (Unitree) data supplement: retarget a representative slice of ACCAD motions.

Correspondence model comes from umr_g1_config.json (built in this folder).
Results go to umr_data/G1/{accad_walking,accad_running,accad_general}/,
the npz robot_xml points straight at czy/g1/g1_29dof_umr.xml (xml_policy disables derived MJCF).

Run:  python czy/g1/batch_g1_supplement.py            (from repo root)
      python batch_g1_supplement.py --no-video
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

G1_DIR = Path(__file__).resolve().parent
ROOT = G1_DIR.parents[1]
SCRIPTS = ROOT / "scripts"
PYTHON = sys.executable
CONFIG = G1_DIR / "umr_g1_config.json"
OUT_DIR = ROOT / "umr_data" / "G1"
ACCAD = ROOT / "sample_data" / "ACCAD"

# (short name, source stem, ACCAD subfolder, 动作说明, 输出子目录)
TASKS = [
    ("Female1_B1_stand_to_walk", "B1_-_stand_to_walk_stageii", "Female1Walking_c3d", "站立→行走", "accad_walking"),
    ("Female1_B3_walk1", "B3_-_walk1_stageii", "Female1Walking_c3d", "行走循环", "accad_walking"),
    ("Female1_B10_walk_turn_left_45", "B10_-_walk_turn_left_(45)_stageii", "Female1Walking_c3d", "左转 45° 行走", "accad_walking"),
    ("Female1_C3_Run", "C3_-_Run_stageii", "Female1Running_c3d", "跑步", "accad_running"),
    ("Female1_C5_walk_to_run", "C5_-_walk_to_run_stageii", "Female1Running_c3d", "行走→跑步", "accad_running"),
    ("Male2_B14_turn_right_45", "B14_-__Walk_turn_right_45_stageii", "Male2Walking_c3d", "右转 45°（男 2 体型）", "accad_walking"),
    ("Female1_A14_stand_to_skip", "A14_-_stand_to_skip_stageii", "Female1General_c3d", "站立→跳跃步", "accad_general"),
    ("Female1_A15_skip_to_stand", "A15_-_skip_to_stand_stageii", "Female1General_c3d", "跳跃步→站立", "accad_general"),
]

VIDEO = "--no-video" not in sys.argv
results: list[dict] = []


def run(cmd: list[str]) -> tuple[int, float]:
    start = time.time()
    code = subprocess.run(cmd, cwd=ROOT).returncode
    return code, time.time() - start


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    missing = [f"{sub}/{stem}.npz" for _, stem, sub, _, _ in TASKS if not (ACCAD / sub / f"{stem}.npz").is_file()]
    if missing:
        print("MISSING SOURCES:", *missing, sep="\n  ")
        return 2

    print(f"tasks={len(TASKS)}  config={CONFIG.relative_to(ROOT)}  out={OUT_DIR.relative_to(ROOT)}  video={VIDEO}")
    print("=" * 74)

    for i, (short, stem, sub, desc, bucket) in enumerate(TASKS, 1):
        out = OUT_DIR / bucket / f"{short}_unitree_g1.npz"
        rec = {"short": short, "source": stem, "subset": sub, "desc": desc, "out": str(out.relative_to(ROOT))}
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            print(f"[{i}/{len(TASKS)}] skip (exists) {short}")
            rec["retarget"] = "skipped"
        else:
            print(f"[{i}/{len(TASKS)}] retarget {short}  ({desc}) ...", flush=True)
            code, dt = run([
                PYTHON, str(SCRIPTS / "retarget_smpl_to_humanoid_surface_vector.py"),
                "--config", str(CONFIG),
                "--data", str(ACCAD / sub / f"{stem}.npz"),
                "--seq-key", stem,
                "--out", str(out),
            ])
            rec["retarget"] = "ok" if code == 0 else f"fail({code})"
            rec["retarget_sec"] = round(dt, 1)
            print(f"[{i}/{len(TASKS)}]   -> {rec['retarget']} in {dt:.0f}s", flush=True)
        results.append(rec)

    if VIDEO:
        for i, rec in enumerate(results, 1):
            out = ROOT / rec["out"]
            vid = out.with_suffix(".mp4")
            rec["video"] = "skipped"
            if not out.exists() or vid.exists():
                continue
            print(f"[video {i}/{len(results)}] {rec['short']} ...", flush=True)
            code, dt = run([
                PYTHON, str(SCRIPTS / "visualize_robot_retarget_result.py"),
                "--result", str(out),
                "--record-video", str(vid),
                "--play",
            ])
            rec["video"] = "ok" if code == 0 else f"fail({code})"
            rec["video_sec"] = round(dt, 1)
            print(f"[video {i}/{len(results)}]   -> {rec['video']} in {dt:.0f}s", flush=True)

    (OUT_DIR / "_summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in results if r.get("retarget") in ("ok", "skipped"))
    print("=" * 74)
    print(f"retarget ok={ok}/{len(results)}  summary={OUT_DIR / '_summary.json'}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())