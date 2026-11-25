"""Retarget the 26 pure-walking ACCAD motions to Weichai F1-29.

Supplement to umr_data/F1/accad_walking (which only holds B1-B4).
Box-carrying motions (B19/B20/B21) and walk-to-hop/leap/crouch/side-step are excluded.

Run:  python batch_f1_walking_extra.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
PYTHON = sys.executable
CONFIG = ROOT / "configs" / "weichai_f1_29_base.json"
OUT_DIR = ROOT / "umr_data" / "F1" / "accad_walking_extra"
ACCAD = ROOT / "sample_data" / "ACCAD"

# (short_name, source stem, ACCAD subfolder)
TASKS: list[tuple[str, str, str]] = [
    # --- Female1Walking_c3d : 11 条 ---
    # Female1_B12_walk_turn_right_90 已放弃：源动作整段离地约 5 cm，求解结果悬空，见 README
    ("Female1_B5_walk_backwards", "B5_-_walk_backwards_stageii", "Female1Walking_c3d"),
    ("Female1_B6_walk_backwards_to_stand", "B6_-_walk_backwards_to_stand_stageii", "Female1Walking_c3d"),
    ("Female1_B7_walk_backwards_turn_forwards", "B7_-_walk_backwards_turn_forwards_stageii", "Female1Walking_c3d"),
    ("Female1_B2_walk_to_stand_t2", "B2_-_walk_to_stand_t2_stageii", "Female1Walking_c3d"),
    ("Female1_B9_walk_turn_left_90", "B9_-_walk_turn_left_(90)_stageii", "Female1Walking_c3d"),
    ("Female1_B10_walk_turn_left_45", "B10_-_walk_turn_left_(45)_stageii", "Female1Walking_c3d"),
    ("Female1_B11_walk_turn_left_135", "B11_-_walk_turn_left_(135)_stageii", "Female1Walking_c3d"),
    ("Female1_B13_walk_turn_right_45", "B13_-_walk_turn_right_(45)_stageii", "Female1Walking_c3d"),
    ("Female1_B14_walk_turn_right_135", "B14_-_walk_turn_right_(135)_stageii", "Female1Walking_c3d"),
    ("Female1_B15_walk_turn_around", "B15_-_walk_turn_around_(same_direction)_stageii", "Female1Walking_c3d"),
    ("Female1_B16_walk_turn_change_direction", "B16_-_walk_turn_change_direction_stageii", "Female1Walking_c3d"),
    # --- Male1Walking_c3d : 5 条 ---
    ("Male1_Walk_B4_stand_to_walk_back", "Walk_B4_-_Stand_to_Walk_Back_stageii", "Male1Walking_c3d"),
    ("Male1_Walk_B10_turn_left_45", "Walk_B10_-_Walk_turn_left_45_stageii", "Male1Walking_c3d"),
    ("Male1_Walk_B13_turn_right_45", "Walk_B13_-_Walk_turn_right_45_stageii", "Male1Walking_c3d"),
    ("Male1_Walk_B15_turn_around", "Walk_B15_-_Walk_turn_around_stageii", "Male1Walking_c3d"),
    ("Male1_Walk_B16_turn_change", "Walk_B16_-_Walk_turn_change_stageii", "Male1Walking_c3d"),
    # --- Male2Walking_c3d : 8 条 ---
    # Male2_B5_walk_backwards 已放弃：源动作整段离地 1.7~8.4 cm，求解结果全程悬空，见 README
    ("Male2_B4_stand_to_walk_backwards", "B4_-_Stand_to_Walk_backwards_stageii", "Male2Walking_c3d"),
    ("Male2_B9_turn_left_90", "B9_-__Walk_turn_left_90_stageii", "Male2Walking_c3d"),
    ("Male2_B10_turn_left_45", "B10_-__Walk_turn_left_45_stageii", "Male2Walking_c3d"),
    ("Male2_B11_turn_left_135", "B11_-__Walk_turn_left_135_stageii", "Male2Walking_c3d"),
    ("Male2_B13_turn_right_90", "B13_-__Walk_turn_right_90_stageii", "Male2Walking_c3d"),
    ("Male2_B14_turn_right_45", "B14_-__Walk_turn_right_45_stageii", "Male2Walking_c3d"),
    ("Male2_B14_turn_right_45_t2", "B14_-__Walk_turn_right_45_t2_stageii", "Male2Walking_c3d"),
    ("Male2_B15_turn_around", "B15_-__Walk_turn_around_stageii", "Male2Walking_c3d"),
]

VIDEO = "--no-video" not in sys.argv
results: list[dict] = []


def run(cmd: list[str]) -> tuple[int, float]:
    start = time.time()
    proc = subprocess.run(cmd, cwd=ROOT)
    return proc.returncode, time.time() - start


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    missing = [
        f"{sub}/{stem}.npz"
        for _, stem, sub in TASKS
        if not (ACCAD / sub / f"{stem}.npz").is_file()
    ]
    if missing:
        print("MISSING SOURCE FILES:")
        for m in missing:
            print("  ", m)
        return 2

    print(f"tasks={len(TASKS)}  out={OUT_DIR}  video={VIDEO}")
    print("=" * 72)

    # 已完成的记录要保留：重跑时不要把 ok + 耗时覆盖成 skipped
    summary_path = OUT_DIR / "_batch_summary.json"
    prior: dict[str, dict] = {}
    if summary_path.exists():
        try:
            prior = {r["short"]: r for r in json.loads(summary_path.read_text(encoding="utf-8"))}
        except Exception:
            prior = {}

    # ---- phase 1: retarget ----
    for i, (short, stem, sub) in enumerate(TASKS, 1):
        data = ACCAD / sub / f"{stem}.npz"
        out = OUT_DIR / f"{short}_weichai_f1_29.npz"
        rec = {"short": short, "source": stem, "subset": sub, "out": str(out.relative_to(ROOT))}
        if out.exists():
            print(f"[{i:02d}/{len(TASKS)}] SKIP (exists) {short}")
            prev = prior.get(short, {})
            if prev.get("retarget") == "ok":
                rec["retarget"] = "ok"
                rec["retarget_sec"] = prev.get("retarget_sec")
            else:
                rec["retarget"] = "skipped"
        else:
            print(f"[{i:02d}/{len(TASKS)}] retarget {short} ...", flush=True)
            code, dt = run([
                PYTHON, str(SCRIPTS / "retarget_smpl_to_humanoid_surface_vector.py"),
                "--config", str(CONFIG),
                "--data", str(data),
                "--seq-key", stem,
                "--out", str(out),
            ])
            rec["retarget"] = "ok" if code == 0 else f"fail({code})"
            rec["retarget_sec"] = round(dt, 1)
            print(f"[{i:02d}/{len(TASKS)}]   -> {rec['retarget']} in {dt:.0f}s", flush=True)
        results.append(rec)

    # ---- phase 2: video ----
    if VIDEO:
        for i, rec in enumerate(results, 1):
            out = ROOT / rec["out"]
            vid = out.with_suffix(".mp4")
            prev = prior.get(rec["short"], {})
            if vid.exists() and prev.get("video") == "ok":
                rec["video"] = "ok"
                rec["video_sec"] = prev.get("video_sec")
            else:
                rec["video"] = "skipped"
            if not out.exists():
                rec["video"] = "no-npz"
                continue
            if vid.exists():
                continue
            print(f"[video {i:02d}/{len(results)}] {rec['short']} ...", flush=True)
            code, dt = run([
                PYTHON, str(SCRIPTS / "visualize_robot_retarget_result.py"),
                "--result", str(out),
                "--record-video", str(vid),
                "--play",
            ])
            rec["video"] = "ok" if code == 0 else f"fail({code})"
            rec["video_sec"] = round(dt, 1)
            print(f"[video {i:02d}/{len(results)}]   -> {rec['video']} in {dt:.0f}s", flush=True)

    summary = summary_path
    # 合并而不是覆盖：保留本次未涉及的条目（例如标记为 abandoned 的两条）
    # 以及本次没有重录的 video/video_sec 与 note
    merged = {k: dict(v) for k, v in prior.items()}
    for rec in results:
        short = rec["short"]
        entry = merged.setdefault(short, {})
        for key, value in rec.items():
            if value is not None:
                entry[key] = value
        for extra in ("video", "video_sec", "note"):
            if extra not in rec and extra in prior.get(short, {}) and extra not in entry:
                entry[extra] = prior[short][extra]
    order = [t[0] for t in TASKS]
    ordered = [merged[s] for s in order if s in merged]
    ordered += [v for k, v in merged.items() if k not in order]
    summary.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in results if r.get("retarget") in ("ok", "skipped"))
    print("=" * 72)
    print(f"retarget ok={ok}/{len(results)}  summary={summary} ({len(ordered)} 条记录)")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())