import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
PYTHON = sys.executable

# ── Robot configurations ──────────────────────────────────────────
CONFIGS = {
    "x1":  ROOT / "configs" / "xyber_x1_base.json",
    "f1":  ROOT / "configs" / "weichai_f1_29_base.json",
}

OUTPUT_DIRS = {
    "x1": ROOT / "umr_data" / "X1" / "accad_running",
    "f1": ROOT / "umr_data" / "F1" / "accad_running",
}

# ── Running tasks (robot_key, short_name, motion_file, seq_key) ───
RUNNING_TASKS = [
    ("C2_Run_to_stand",  "C2_-_Run_to_stand_stageii",   "Female1Running_c3d"),
    ("C3_Run",           "C3_-_Run_stageii",             "Female1Running_c3d"),
    ("C4_Run_to_walk",   "C4_-_Run_to_walk1_stageii",   "Female1Running_c3d"),
    ("C5_Walk_to_run",   "C5_-_walk_to_run_stageii",     "Female1Running_c3d"),
]

for d in OUTPUT_DIRS.values():
    d.mkdir(parents=True, exist_ok=True)

# ── Execute ───────────────────────────────────────────────────────
for robot_key in ["x1", "f1"]:
    robot_label = "X1 (xyber_x1)" if robot_key == "x1" else "F1 (weichai_f1_29)"
    config = CONFIGS[robot_key]
    out_dir = OUTPUT_DIRS[robot_key]

    for short_name, filename, subdir in RUNNING_TASKS:
        data_path = ROOT / "sample_data" / "ACCAD" / subdir / (filename + ".npz")
        out_path  = out_dir / f"{short_name}_{robot_key}.npz"
        vid_path  = out_dir / f"{short_name}_{robot_key}.mp4"

        print(f"\n{'='*60}")
        print(f"[{robot_label}] {short_name}")
        print(f"  Data:   {data_path}")
        print(f"  Output: {out_path}")
        print(f"{'='*60}")

        # ── Retarget ──
        if out_path.exists():
            print("  Already exists, skip retarget.")
        else:
            print("  Retargeting...")
            start = time.time()
            r = subprocess.run([
                PYTHON, str(SCRIPTS / "retarget_smpl_to_humanoid_surface_vector.py"),
                "--config", str(config),
                "--data", str(data_path),
                "--seq-key", filename,
                "--out", str(out_path),
            ], cwd=ROOT)
            elapsed = time.time() - start
            if r.returncode != 0:
                print(f"  FAILED ({elapsed:.0f}s)")
                # remove partial output
                if out_path.exists():
                    out_path.unlink()
                continue
            print(f"  Done ({elapsed:.0f}s)")

        # ── Video ──
        if not vid_path.exists():
            print("  Recording video...")
            start = time.time()
            r = subprocess.run([
                PYTHON, str(SCRIPTS / "visualize_robot_retarget_result.py"),
                "--result", str(out_path),
                "--record-video", str(vid_path),
                "--play",
            ], cwd=ROOT)
            elapsed = time.time() - start
            if r.returncode == 0:
                print(f"  Video saved ({elapsed:.0f}s)")
            else:
                print(f"  Video recording skipped")
        else:
            print("  Video already exists.")

print("\n\nAll done!")
