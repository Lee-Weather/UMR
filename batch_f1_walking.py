import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"
OUTPUT_DIR = ROOT / "umr_data" / "F1" / "accad_walking"
PYTHON = sys.executable
BASE_CONFIG = ROOT / "configs" / "weichai_f1_29_base.json"

tasks = [
    ("B1_stand_to_walk", "B1_-_stand_to_walk_stageii",  "Female1Walking_c3d"),
    ("B2_walk_to_stand", "B2_-_walk_to_stand_stageii",  "Female1Walking_c3d"),
    ("B3_walk1",         "B3_-_walk1_stageii",          "Female1Walking_c3d"),
    ("B4_stand_to_walk_back", "B4_-_stand_to_walk_back_stageii", "Female1Walking_c3d"),
]

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for short_name, filename, subdir in tasks:
    data_path = ROOT / "sample_data" / "ACCAD" / subdir / (filename + ".npz")
    out_path = OUTPUT_DIR / f"{short_name}_weichai_f1_29.npz"
    vid_path = OUTPUT_DIR / f"{short_name}_weichai_f1_29.mp4"

    print(f"\n=== {short_name} ===")
    print(f"Data: {data_path}")
    print(f"Output: {out_path}")

    if out_path.exists():
        print("Already exists, skip retarget.")
    else:
        start = time.time()
        r = subprocess.run([
            PYTHON, str(SCRIPTS / "retarget_smpl_to_humanoid_surface_vector.py"),
            "--config", str(BASE_CONFIG),
            "--data", str(data_path),
            "--seq-key", filename,
            "--out", str(out_path),
        ], cwd=ROOT)
        elapsed = time.time() - start
        if r.returncode != 0:
            print(f"FAILED ({elapsed:.0f}s)")
            continue
        print(f"Done ({elapsed:.0f}s)")

    if not vid_path.exists():
        print("Recording video...")
        start = time.time()
        r = subprocess.run([
            PYTHON, str(SCRIPTS / "visualize_robot_retarget_result.py"),
            "--result", str(out_path),
            "--record-video", str(vid_path),
            "--play",
        ], cwd=ROOT)
        elapsed = time.time() - start
        if r.returncode == 0:
            print(f"Video saved ({elapsed:.0f}s)")
        else:
            print(f"Video recording skipped")
    else:
        print("Video already exists.")

print("\n=== All done ===")
