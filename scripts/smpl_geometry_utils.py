"""SMPL/SMPL-X geometry helpers shared by the retarget pipeline.

Extracted from the root-level ``view_smpl_mujoco.py`` so that library code no longer
has to import a viewer script. ``smpl_surface_retarget_common`` depends on
``dynamic_surface_template_to_world`` and ``model_faces``; the dynamic-surface
sampling helpers are kept next to them because they form one coherent set.
"""
from __future__ import annotations

import numpy as np
import torch


def _sample_points_on_triangles(triangles, rng):
    r1 = np.sqrt(rng.random(len(triangles)))
    r2 = rng.random(len(triangles))
    w0 = 1.0 - r1
    w1 = r1 * (1.0 - r2)
    w2 = r1 * r2
    points = (
        w0[:, None] * triangles[:, 0]
        + w1[:, None] * triangles[:, 1]
        + w2[:, None] * triangles[:, 2]
    )
    bary = np.stack([w0, w1, w2], axis=1)
    return points, bary


def _farthest_point_sampling(points, num_samples, seed=0):
    if len(points) <= num_samples:
        return np.arange(len(points), dtype=np.int32)

    rng = np.random.default_rng(seed)
    selected = np.empty(num_samples, dtype=np.int32)
    selected[0] = int(rng.integers(len(points)))

    diff = points - points[selected[0]]
    min_dist2 = np.einsum("ij,ij->i", diff, diff)
    for idx in range(1, num_samples):
        next_idx = int(np.argmax(min_dist2))
        selected[idx] = next_idx
        diff = points - points[next_idx]
        dist2 = np.einsum("ij,ij->i", diff, diff)
        min_dist2 = np.minimum(min_dist2, dist2)
    return selected


def build_dynamic_surface_sample_template(vertices0, faces, num_samples, seed=0, oversample_ratio=8):
    rng = np.random.default_rng(seed)
    tri = vertices0[faces]
    face_normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    areas = 0.5 * np.linalg.norm(face_normals, axis=1)
    valid_face_ids = np.nonzero(areas > 1e-12)[0]
    if valid_face_ids.size == 0:
        raise ValueError("No valid mesh triangles found for dynamic surface sampling.")

    valid_areas = areas[valid_face_ids]
    num_candidates = max(num_samples * oversample_ratio, num_samples)
    candidate_face_ids = rng.choice(
        valid_face_ids,
        size=num_candidates,
        replace=True,
        p=valid_areas / valid_areas.sum(),
    )
    candidate_points, candidate_bary = _sample_points_on_triangles(vertices0[faces[candidate_face_ids]], rng)
    keep = _farthest_point_sampling(candidate_points, num_samples=num_samples, seed=seed)
    return {
        "face_ids": candidate_face_ids[keep].astype(np.int32),
        "bary": candidate_bary[keep].astype(np.float32),
    }


def dynamic_surface_template_to_world(vertices, faces, template):
    tri = vertices[faces[template["face_ids"]]]
    bary = template["bary"]
    return (
        bary[:, 0:1] * tri[:, 0]
        + bary[:, 1:2] * tri[:, 1]
        + bary[:, 2:3] * tri[:, 2]
    ).astype(np.float32)


def dynamic_surface_template_normals_to_world(vertices, faces, template):
    tri = vertices[faces[template["face_ids"]]]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    return (normals / np.maximum(lengths, 1e-12)).astype(np.float32)


def model_faces(smpl_model):
    faces = smpl_model.faces if hasattr(smpl_model, "faces") else smpl_model.f
    if torch.is_tensor(faces):
        faces = faces.detach().cpu().numpy()
    return np.asarray(faces, dtype=np.int32)