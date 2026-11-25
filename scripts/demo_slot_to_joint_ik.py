"""Visualize a surface-slot target becoming two arm joint angles.

Run: python scripts/demo_slot_to_joint_ik.py
This is a 2-D teaching example of Jacobian IK, not the full UMR solver.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np


def forward(q):
    """Shoulder is fixed; q[1] is the elbow angle relative to the upper arm."""
    a, b = q
    elbow = 0.40 * np.array([np.cos(a), np.sin(a)])
    wrist = elbow + 0.30 * np.array([np.cos(a + b), np.sin(a + b)])
    return elbow, wrist


def jacobian(q):
    """J maps small joint-angle changes (radians) to slot displacement (meters)."""
    a, b = q
    return np.array([
        [-0.40 * np.sin(a) - 0.30 * np.sin(a + b), -0.30 * np.sin(a + b)],
        [0.40 * np.cos(a) + 0.30 * np.cos(a + b), 0.30 * np.cos(a + b)],
    ])


def solve(target, steps=40):
    q = np.deg2rad([-10.0, 35.0])
    history = [q.copy()]
    limits = np.deg2rad([[-60.0, 150.0], [0.0, 150.0]])
    for _ in range(steps):
        error = target - forward(q)[1]
        j = jacobian(q)
        # Damped least squares: minimize ||J dq - error||^2 + damping^2 ||dq||^2.
        dq = j.T @ np.linalg.solve(j @ j.T + 0.04**2 * np.eye(2), error)
        dq *= min(1.0, np.deg2rad(8.0) / max(np.linalg.norm(dq), 1e-12))
        q = np.clip(q + 0.8 * dq, limits[:, 0], limits[:, 1])
        history.append(q.copy())
    return np.array(history)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[1] / "output/slot_to_joint_demo")
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"], "axes.unicode_minus": False})
    target = np.array([0.38, 0.36])  # Illustrative human slot after frame/scale alignment.
    qs = solve(target)
    wrists = np.array([forward(q)[1] for q in qs])
    errors = np.linalg.norm(wrists - target, axis=1) * 100
    fig = plt.figure(figsize=(11, 6), facecolor="#f5f5ef")
    grid = fig.add_gridspec(2, 2, width_ratios=[1.35, 1], hspace=0.65, wspace=0.35)
    ax = fig.add_subplot(grid[:, 0])
    err_ax = fig.add_subplot(grid[0, 1])
    angle_ax = fig.add_subplot(grid[1, 1])
    fig.suptitle("表面对应点 → 关节角度：二维双关节 IK 示例", fontsize=17, color="#173c2b", y=0.98)
    fig.subplots_adjust(top=0.84, bottom=0.16, left=0.08, right=0.97)
    fig.text(0.5, 0.04, "教学简化：固定肩部、单个腕部 slot、目标静止；迭代步不是动作时间帧。", ha="center", fontsize=10, color="#60716b")
    ax.set(xlim=(-0.08, 0.78), ylim=(-0.20, 0.72), xlabel="x / m", ylabel="y / m", aspect="equal")
    ax.grid(alpha=0.2)
    ax.plot(*target, marker="*", color="#d47b3f", ms=17, label="人体对应点（目标）")
    arm, = ax.plot([], [], "o-", color="#205d4c", lw=6, ms=8, label="机器人肩—肘—腕")
    trail, = ax.plot([], [], "--", color="#7eae92", lw=1.5, label="机器人 slot 迭代路径")
    gap, = ax.plot([], [], ":", color="#d47b3f", lw=2)
    ax.legend(loc="upper left", fontsize=9)
    info = ax.text(0.02, 0.03, "", transform=ax.transAxes, fontsize=10, va="bottom")
    err_ax.set(title="位置误差逐步减小", xlabel="求解迭代步", ylabel="误差 / cm", xlim=(0, len(qs)-1), ylim=(0, max(errors)*1.1))
    err_ax.grid(alpha=0.2)
    error_line, = err_ax.plot([], [], color="#d47b3f", lw=2)
    angle_ax.set(title="关节角度共同调整", xlabel="求解迭代步", ylabel="角度 / °", xlim=(0, len(qs)-1), ylim=(-20, 110))
    angle_ax.grid(alpha=0.2)
    shoulder_line, = angle_ax.plot([], [], color="#205d4c", lw=2, label="肩角 q1")
    elbow_line, = angle_ax.plot([], [], color="#5877af", lw=2, label="肘角 q2")
    angle_ax.legend(fontsize=9)

    def update(i):
        elbow, wrist = forward(qs[i])
        arm.set_data([0, elbow[0], wrist[0]], [0, elbow[1], wrist[1]])
        trail.set_data(wrists[:i+1, 0], wrists[:i+1, 1])
        gap.set_data([wrist[0], target[0]], [wrist[1], target[1]])
        indices = np.arange(i+1)
        error_line.set_data(indices, errors[:i+1])
        shoulder_line.set_data(indices, np.rad2deg(qs[:i+1, 0]))
        elbow_line.set_data(indices, np.rad2deg(qs[:i+1, 1]))
        info.set_text(f"迭代 {i:02d}  |  误差 {errors[i]:.3f} cm\nq1 = {np.rad2deg(qs[i,0]):.1f}°   q2 = {np.rad2deg(qs[i,1]):.1f}°")
        return arm, trail, gap, info, error_line, shoulder_line, elbow_line

    update(len(qs)-1)
    fig.savefig(args.out_dir / "slot_to_joint_ik.png", dpi=150)
    frames = list(range(0, len(qs), 2)) + [len(qs)-1]*8
    animation = FuncAnimation(fig, update, frames=frames, interval=150, blit=False)
    animation.save(args.out_dir / "slot_to_joint_ik.gif", writer=PillowWriter(fps=7), dpi=100)
    plt.close(fig)
    print(f"Initial / final error: {errors[0]:.4f} / {errors[-1]:.6f} cm")
    print(f"Saved PNG and GIF to: {args.out_dir}")


if __name__ == "__main__":
    main()
