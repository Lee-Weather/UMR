"""Fit eight surface slots together using two joint angles (2-D teaching demo).

Run: python scripts/demo_multi_slot_to_joint_ik.py
Optional: --noise 0.005 adds 5 mm standard-deviation target noise to show compromise.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np

# Each slot is attached to a link, with a local surface offset (meters).
LINK_IDS = np.array([0, 0, 0, 0, 1, 1, 1, 1])
LOCAL = np.array([[.09, .025], [.17, -.025], [.25, .025], [.34, -.025],
                  [.05, .022], [.12, -.022], [.20, .022], [.28, -.022]])


def rotation(angle):
    c, s = np.cos(angle), np.sin(angle)
    return np.array([[c, -s], [s, c]])


def forward(q):
    elbow = rotation(q[0]) @ [0.40, 0.0]
    wrist = elbow + rotation(q.sum()) @ [0.30, 0.0]
    return elbow, wrist


def slot_positions(q):
    elbow, _ = forward(q)
    return np.array([rotation(q[0]) @ point if link == 0 else
                     elbow + rotation(q.sum()) @ point
                     for link, point in zip(LINK_IDS, LOCAL)])


def jacobians(q):
    """Each slot has a 2 x 2 Jacobian; all eight share the SAME q."""
    points = slot_positions(q)
    elbow, _ = forward(q)
    result = np.zeros((len(points), 2, 2))
    result[:, :, 0] = np.column_stack([-points[:, 1], points[:, 0]])
    forearm = points[LINK_IDS == 1] - elbow
    result[LINK_IDS == 1, :, 1] = np.column_stack([-forearm[:, 1], forearm[:, 0]])
    return result


def solve(targets, steps=40):
    q = np.deg2rad([-10., 10.])
    history = [q.copy()]
    lower, upper = np.deg2rad([-60., 0.]), np.deg2rad([150., 150.])
    for _ in range(steps):
        error = (targets - slot_positions(q)).reshape(-1)  # 16 residuals
        j = jacobians(q).reshape(-1, 2)                    # 16 x 2 matrix
        # One joint update jointly minimizes ALL slot errors, plus damping.
        dq = np.linalg.solve(j.T @ j + .04**2 * np.eye(2), j.T @ error)
        dq *= min(1., np.deg2rad(8.) / max(np.linalg.norm(dq), 1e-12))
        q = np.clip(q + .8 * dq, lower, upper)
        history.append(q.copy())
    return np.array(history)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parents[1] / "output/multi_slot_to_joint_demo")
    parser.add_argument("--noise", type=float, default=0., help="Target noise standard deviation in meters.")
    args = parser.parse_args()
    if args.noise < 0:
        parser.error("--noise must be nonnegative")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"], "axes.unicode_minus": False})
    targets = slot_positions(np.deg2rad([30., 105.]))  # Large elbow bend for visibility.
    targets += np.random.default_rng(42).normal(0, args.noise, targets.shape)
    qs = solve(targets)
    points = np.array([slot_positions(q) for q in qs])
    errors = np.linalg.norm(points - targets, axis=2) * 100  # Per-slot cm.
    colors = plt.get_cmap("tab10")(np.arange(8))
    fig = plt.figure(figsize=(12, 6.5), facecolor="#f5f5ef")
    grid = fig.add_gridspec(2, 2, width_ratios=[1.3, 1], hspace=.65, wspace=.35)
    ax, error_ax, angle_ax = fig.add_subplot(grid[:, 0]), fig.add_subplot(grid[0, 1]), fig.add_subplot(grid[1, 1])
    fig.subplots_adjust(top=.83, bottom=.16, left=.08, right=.97)
    fig.suptitle("8 个表面 slots → 同一组肩、肘关节角度", fontsize=18, color="#173c2b", y=.98)
    fig.text(.5, .91, "上臂 4 点 + 前臂 4 点  |  肘角由 10° 弯曲至 105°", ha="center", fontsize=11, color="#60716b")
    fig.text(.5, .04, "同色即同一 slot：空心点为目标，实心点为机器人；虚线表示匹配误差。目标由示意姿态合成。", ha="center", fontsize=10, color="#60716b")
    ax.set(xlim=(-.08, .78), ylim=(-.18, .73), xlabel="x / m", ylabel="y / m", aspect="equal")
    ax.grid(alpha=.2)
    ax.scatter(targets[:, 0], targets[:, 1], s=100, facecolors="none", edgecolors=colors, lw=2, label="目标 slots（空心）")
    for i, point in enumerate(targets):
        ax.text(point[0] + .025, point[1], str(i), fontsize=9, color=colors[i])
    arm, = ax.plot([], [], "o-", color="#afc5b5", lw=11, ms=6, zorder=1, label="机器人肩—肘—腕")
    dots = ax.scatter(points[0,:,0], points[0,:,1], c=colors, s=35, zorder=4, label="机器人 slots（实心）")
    gaps = [ax.plot([], [], "--", color=color, lw=1.3, alpha=.8)[0] for color in colors]
    ax.legend(loc="upper left", fontsize=8)
    info = ax.text(.02, .03, "", transform=ax.transAxes, fontsize=10)
    error_ax.set(title="每个 slot 的误差与整体平均误差", xlabel="求解迭代步", ylabel="误差 / cm", xlim=(0, 40), ylim=(0, errors.max()*1.1))
    error_ax.grid(alpha=.2)
    error_lines = [error_ax.plot([], [], color=c, lw=1, alpha=.65)[0] for c in colors]
    mean_line, = error_ax.plot([], [], color="#173c2b", lw=2.5, label="8 点平均")
    error_ax.legend(fontsize=8)
    angle_ax.set(title="所有 slots 共同决定关节更新", xlabel="求解迭代步", ylabel="角度 / °", xlim=(0, 40), ylim=(-20, 125))
    angle_ax.grid(alpha=.2)
    angle_lines = [angle_ax.plot([], [], color=c, lw=2, label=label)[0] for c, label in [("#205d4c", "肩角 q1"), ("#5877af", "肘角 q2")]]
    angle_ax.legend(fontsize=9)

    def update(i):
        elbow, wrist = forward(qs[i])
        arm.set_data([0, elbow[0], wrist[0]], [0, elbow[1], wrist[1]])
        dots.set_offsets(points[i])
        for k, gap in enumerate(gaps):
            gap.set_data([points[i,k,0], targets[k,0]], [points[i,k,1], targets[k,1]])
        indices = np.arange(i+1)
        for k, line in enumerate(error_lines):
            line.set_data(indices, errors[:i+1, k])
        mean_line.set_data(indices, errors[:i+1].mean(axis=1))
        for k, line in enumerate(angle_lines):
            line.set_data(indices, np.rad2deg(qs[:i+1, k]))
        info.set_text(f"迭代 {i:02d} | 平均误差 {errors[i].mean():.3f} cm\nq1 = {np.rad2deg(qs[i,0]):.1f}°   q2 = {np.rad2deg(qs[i,1]):.1f}°")

    update(len(qs)-1)
    fig.savefig(args.out_dir / "multi_slot_to_joint_ik.png", dpi=150)
    frames = list(range(24)) + list(range(24, len(qs), 2)) + [len(qs)-1]*8
    animation = FuncAnimation(fig, update, frames=frames, interval=125)
    animation.save(args.out_dir / "multi_slot_to_joint_ik.gif", writer=PillowWriter(fps=8), dpi=100)
    plt.close(fig)
    print(f"Mean slot error: {errors[0].mean():.4f} -> {errors[-1].mean():.6f} cm")
    print(f"Final angles: {np.rad2deg(qs[-1]).round(3).tolist()}; outputs: {args.out_dir}")


if __name__ == "__main__":
    main()
