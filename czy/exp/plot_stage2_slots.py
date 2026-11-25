#!/usr/bin/env python3
"""Plot the learned Stage-2 slot correspondence between SMPL-X and the robot.

Renders a 4-panel PNG:
  (a) SMPL-X 4096-point cloud, front view, coloured by learned slot index
  (b) robot 4096-point cloud, front view, coloured by the SAME slot index
  (c) correspondence error (per-slot distance) painted onto the SMPL-X cloud
  (d) error broken down by body region

If the correspondence is correct, panel (a) and (b) show the same colour layout
in corresponding body parts.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def region_label(points: np.ndarray) -> np.ndarray:
    """Coarse body-region classification from SMPL-frame geometry (Y=up, X=lateral)."""
    y, x = points[:, 1], points[:, 0]
    labels = np.full(len(points), "torso", dtype=object)
    labels[y < -0.45] = "legs"
    labels[(y >= -0.45) & (y < -0.05)] = "thigh/hip"
    labels[(y >= 0.05) & (y < 0.22) & (np.abs(x) > 0.28)] = "thigh/hip"  # placeholder
    labels[(y >= 0.10) & (np.abs(x) > 0.30)] = "arms"
    labels[y >= 0.22] = "head/neck"
    return labels


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slots", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    d = np.load(args.slots, allow_pickle=True)
    names = [str(n) for n in d["names"]]
    R = d["normalized_reconstructed_slots"]      # (2, 4096, 3) normalised + slot-aligned
    T = d["normalized_target_points"]            # (2, 4096, 3) normalised, sampling order
    n_slots = R.shape[1]

    smpl, robot = R[0], R[1]
    err = np.linalg.norm(smpl - robot, axis=1)
    raw = np.linalg.norm(T[0] - T[1], axis=1)     # before correspondence learning

    hue = np.linspace(0.0, 1.0, n_slots)

    fig = plt.figure(figsize=(15, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.22, wspace=0.18)

    def front(ax, pts, c, cmap, title, cb_label, vmin=None, vmax=None):
        s = ax.scatter(pts[:, 0], pts[:, 1], c=c, cmap=cmap, s=7,
                       vmin=vmin, vmax=vmax, linewidths=0)
        ax.set_aspect("equal")
        ax.set_xlabel("X  (lateral)")
        ax.set_ylabel("Y  (up)")
        ax.set_title(title, fontsize=11)
        ax.grid(alpha=0.2)
        fig.colorbar(s, ax=ax, shrink=0.82, label=cb_label)

    front(fig.add_subplot(gs[0, 0]), smpl, hue, "hsv",
          f"(a) {names[0]}\n4096 pts, coloured by learned slot index", "slot index")
    front(fig.add_subplot(gs[0, 1]), robot, hue, "hsv",
          f"(b) {names[1]}\n4096 pts, SAME slot colouring", "slot index")

    e_max = float(np.percentile(err, 99))
    front(fig.add_subplot(gs[1, 0]), smpl, err, "viridis",
          f"(c) correspondence error on {names[0]}\n"
          f"mean={err.mean():.4f}  median={np.median(err):.4f}  p99={e_max:.4f}",
          "|SMPL slot - robot slot|", vmin=0.0, vmax=e_max)

    # (d) per-region error bars
    ax = fig.add_subplot(gs[1, 1])
    labels = region_label(smpl)
    order = ["legs", "thigh/hip", "torso", "arms", "head/neck"]
    means, counts = [], []
    for r in order:
        m = labels == r
        means.append(err[m].mean() if m.sum() else np.nan)
        counts.append(int(m.sum()))
    bars = ax.bar(order, means, color="#4C72B0")
    for b, c, mv in zip(bars, counts, means):
        ax.text(b.get_x() + b.get_width() / 2, mv, f"n={c}", ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("mean per-slot distance")
    ax.set_title(f"(d) error by body region\n"
                 f"index-order baseline mean={raw.mean():.4f}  ->  learned {err.mean():.4f} "
                 f"({raw.mean()/err.mean():.1f}x better)", fontsize=11)
    ax.grid(alpha=0.2, axis="y")
    ax.tick_params(axis="x", rotation=15)

    fig.suptitle("Stage 2 — learned slot correspondence (normalised space, height = 1.0)",
                 fontsize=13, y=0.965)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=130, bbox_inches="tight")
    print(f"saved {args.out}")

    # ---- numeric summary to stdout (for the experiment log) ----
    print(f"\nslots={n_slots}")
    print(f"index-order distance  mean={raw.mean():.5f} median={np.median(raw):.5f}")
    print(f"learned     distance  mean={err.mean():.5f} median={np.median(err):.5f} "
          f"p90={np.percentile(err, 90):.5f} max={err.max():.5f}")
    print(f"improvement factor = {raw.mean() / err.mean():.2f}x")
    for r, mv, c in zip(order, means, counts):
        print(f"  {r:10s} n={c:5d}  mean_err={mv:.5f}")


if __name__ == "__main__":
    main()