"""G1 batch: the same 24 pure-walking ACCAD references used for F1.

The task list is imported from ../../batch_f1_walking_extra.py so the two robots always
stay aligned (same stems, same short names, same ACCAD subsets).

Run:  python czy/g1/batch_g1_walking_24.py [--no-video]
"""
from __future__ import annotations

import importlib.util
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
OUT_DIR = ROOT / "umr_data" / "G1" / "accad_walking"
ACCAD = ROOT / "sample_data" / "ACCAD"
SUFFIX = "_unitree_g1"


def load_f1_tasks() -> list[tuple[str, str, str]]:
    src = ROOT / "batch_f1_walking_extra.py"
    spec = importlib.util.spec_from_file_location("f1_walking_batch", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return list(mod.TASKS)


TASKS = load_f1_tasks()
VIDEO = "--no-video" not in sys.argv
results: list[dict] = []


def run(cmd: list[str]) -> tuple[int, float]:
    start = time.time()
    code = subprocess.run(cmd, cwd=ROOT).returncode
    return code, time.time() - start


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"tasks={len(TASKS)} (aligned with F1)  config={CONFIG.relative_to(ROOT)}  out={OUT_DIR.relative_to(ROOT)}")
    print("=" * 78)

    for i, (short, stem, sub) in enumerate(TASKS, 1):
        data = ACCAD / sub / f"{stem}.npz"
        out = OUT_DIR / f"{short}{SUFFIX}.npz"
        rec = {"short": short, "source": stem, "subset": sub, "out": str(out.relative_to(ROOT))}
        if not data.is_file():
            rec["retarget"] = "missing-source"
            print(f"[{i:02d}/{len(TASKS)}] MISSING source {sub}/{stem}.npz")
            results.append(rec)
            continue
        if out.exists():
            print(f"[{i:02d}/{len(TASKS)}] skip (exists) {short}")
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

    if VIDEO:
        for i, rec in enumerate(results, 1):
            out = ROOT / rec["out"]
            vid = out.with_suffix(".mp4")
            rec["video"] = "skipped"
            if not out.exists() or vid.exists():
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

    (OUT_DIR / "_summary_walking24.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in results if r.get("retarget") in ("ok", "skipped"))
    print("=" * 78)
    print(f"retarget ok={ok}/{len(results)}  summary={OUT_DIR / '_summary_walking24.json'}")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())