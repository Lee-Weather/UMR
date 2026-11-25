# UMR 重定向流水线文档

## 概述

UMR（Universal Motion Retargeter）是一个基于表面点云对应关系的人体运动重定向框架。它将 SMPL-X 等人体模板的运动数据映射到各类人形机器人的关节空间。

整个过程分为三个阶段：

```
Stage 1 (build)     →    Stage 2 (train)     →    Stage 3 (retarget)
人体 + 机器人点云    →    训练对应关系 AE      →    逐帧解算关节命令
```

---

## 目录

1. [配置文件体系](#1-配置文件体系)
2. [Stage 1 — 构建对应关系数据集](#2-stage-1--构建对应关系数据集)
3. [Stage 2 — 训练对应关系自编码器](#3-stage-2--训练对应关系自编码器)
4. [Stage 3 — 重定向运动](#4-stage-3--重定向运动)
5. [数据源类型](#5-数据源类型)
6. [跨 Beta 复用](#6-跨-beta-复用)
7. [可视化与录屏](#7-可视化与录屏)
8. [命令速查](#8-命令速查)
9. [故障排除](#9-故障排除)

---

## 1. 配置文件体系

### 1.1 配置层次

配置文件采用分层叠加机制：

```
humanoid_retarget_defaults.json  (全局默认值，位于项目根目录)
        │
        ▼
  机器人配置文件                (如 robot_configs/humanoid_retarget_xyber_x1_example.json)
        │
        ▼
  运行时命令行参数              (最高优先级)
```

通过配置文件的 `extends` 字段或自动继承机制，机器人配置只需包含与默认值不同的字段。

### 1.2 全局默认值

**`humanoid_retarget_defaults.json`**

```json
{
  "smplx_model_dir": "smpl",
  "smpl_template": {
    "type": "smplx",
    "use_betas": true,
    "use_gender": true,
    "name": "auto"
  },
  "robot": {
    "visual_geom_policy": "auto",
    "to_smpl_frame": true,
    "sample_pose": "tpose"
  },
  "correspondence": {
    "slots_field": "reconstructed_slots",
    "smpl_name": "auto"
  },
  "motion": {
    "start": 0,
    "end": -1,
    "stride": 1
  },
  "retarget": {
    "source_ground_align": "global_foot_joint"
  },
  "solver": { ... }
}
```

### 1.3 机器人配置文件

位于 `robot_configs/`，示例：

```json
{
  "robot": {
    "name": "xyber_x1",                          // 机器人名称
    "xml": "assets/F1/F1_resource/mjcf/...xml",   // MJCF/URDF 路径
    "point_cloud_center": "body:lumbar_yaw_link", // 点云居中参考点
    "tpose_qpos": {                               // T-pose 关节角度
      "left_shoulder_roll_joint": -1.57,
      "right_shoulder_roll_joint": -1.57,
      ...
    }
  }
}
```

关键字段说明：

| 字段 | 说明 | 格式 |
|---|---|---|
| `name` | 机器人标识名 | 字符串 |
| `xml` | MJCF 路径 | 相对/绝对路径 |
| `point_cloud_center` | 点云居中参考系 | `body:名称` / `geom:名称` / `joint:名称` |
| `tpose_qpos` | T-pose 关节配置 | `{关节名: 角度值}` |
| `height` | 预设身高(米) | 浮点数，0 表示自动测量 |

---

## 2. Stage 1 — 构建对应关系数据集

### 2.1 目标

采集人体模板和机器人在 T-pose 下的表面点云，产生一对对齐前的对应关系数据集。

### 2.2 流程

```
人体模板 (SMPL-X)                         机器人 (MJCF)
      │                                        │
      ▼                                        ▼
  顶点 + 三角面                              顶点 + 三角面
      │                                        │
      ▼                                        ▼
  拟合 T-pose                               加载 T-pose
  应用 betas                                设置关节角度
      │                                        │
      ▼                                        ▼
  计算躯干中心                              计算躯干中心
  (spine1 关节)                             (point_cloud_center)
      │                                        │
      └──────────── 同一坐标系 ────────────┘
                           │
                           ▼
              可见外表面采样 (first_hit)
              4096 点 × 8 倍过采样
                           │
                           ▼
                保存为 .npz 数据集
```

### 2.3 采样算法

默认使用 **`first_hit`** 算法：

1. 从曲面均匀采样 8×4096 = 32768 个候选点
2. 对每个候选点，从 26 个方向（3×3×3 去中心）发射射线
3. 只保留首次命中网格表面的点
4. 过滤掉被自身几何遮挡的内部点

> ⚠️ 需要 **Embree** 加速库（`embreex`）。如果没有安装，会直接抛出异常，没有纯 Python 回退。

### 2.4 输出

文件路径: `data/correspondence_{robot_name}_{template_name}.npz`

核心字段：

| 字段 | 形状 | 说明 |
|---|---|---|
| `points` | `(N, 4096, 3)` | 各模板的采样点，统一坐标系 |
| `names` | `(N,)` | 模板名称列表 |
| `root_offsets` | `(N, 3)` | 各模板躯干中心偏移 |
| `center_modes` | `(N,)` | 各模板居中方式 |
| `mesh_vertices_i` | `(V_i, 3)` | 第 i 个模板的顶点 |
| `mesh_faces_i` | `(F_i, 3)` | 第 i 个模板的三角面 |

### 2.5 命令

```bash
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/xxx.json \
  --stage build
```

强制重建：

```bash
# 添加 --force-build 参数
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/xxx.json \
  --stage build --force-build
```

---

## 3. Stage 2 — 训练对应关系自编码器

### 3.1 目标

训练一个 template-residual correspondence autoencoder，将人体与机器人的点云对齐，输出共享的 slot 排序。

### 3.2 原理

```
       输入点云            编码器            解码器
  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
  │ 人体: P_h     │───▶│  Encoder     │───▶│  Decoder     │───▶ 重建点云
  │ 机器人: P_r   │    │  共享权重    │    │  共享权重    │
  └──────────────┘    └──────────────┘    └──────────────┘
                            │
                            ▼
                        隐空间 Z
                    (slot 排序依据)
```

- 数据集只有 2 个样本（人体模板 + 机器人）
- 这不是大数据训练，而是对两个点云做优化式对齐
- 使用测地邻接约束（`edge_k=32`）保证 slot 的空间连续性

### 3.3 关键超参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `epochs` | 500 | 数据只有 2 样本，500 epoch ≈ 500 步 |
| `batch_size` | 2 | 同时输入人体 + 机器人 |
| `chamfer_weight` | 1.0 | 主损失：点云对齐质量 |
| `repulsion_weight` | 0.002 | 防点堆叠的正则项 |
| `edge_weight` | 0.4 | slot 空间连续性权重 |
| `normalize` | `per_sample_height` | 各点云按自身身高归一化 |

### 3.4 判断对应质量

训练完毕后，自动输出对应误差统计：

```
chamfer 均值      chamfer max      提升倍数
0.03967           0.13671          10.55× (vs 基线)
```

误差按身体区域分布：

| 区域 | 典型误差 | 评价 |
|---|---|---|
| 头/颈 | ~0.023 | ✅ 最好 |
| 躯干 | ~0.037 | ✅ |
| 腿部 | ~0.042 | ✅ |
| 手臂/手 | ~0.084 | ⚠️ 最差 |

### 3.5 输出

- `output/correspondence_{template}_{robot}/correspondence_slots_final.npz` — 最终 slot 文件
- `output/correspondence_{template}_{robot}/checkpoint-final.pt` — 模型权重

### 3.6 命令

```bash
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/xxx.json \
  --stage train
```

---

## 4. Stage 3 — 重定向运动

### 4.1 目标

读取人体运动序列，利用训练好的 slots，逐帧解算机器人的关节命令。

### 4.2 求解流程

```
对每一帧:
  1. 读取人体姿态 (SMPL-X 参数)
  2. 计算人体表面点云
  3. 根据 slots 确定对应关系
  4. 解二次规划 (QP):
     - 目标: 人体点 → 机器人点 距离最小
     - 约束: 地面接触、自穿透、关节限位、步长限制
  5. 保存关节位置 qpos

所有帧求解完后:
  6. LQR 轨迹滤波 (平滑处理)
```

### 4.3 求解器配置

| 参数 | 说明 |
|---|---|
| `iters=1` | 每帧迭代次数 |
| `ground_contact_map_cost=10.0` | 地面接触权重 |
| `ground_penetration_hard_constraint=true` | 地面穿透硬约束 |
| `self_penetration_margin=-0.001` | 自穿透软约束容差 |
| `step_limit_mode=l2` | L2 步长限制 |
| `trajectory_filter_mode=lqr` | LQR 轨迹滤波 |
| `batch_size=32` | 每批解算帧数 |

### 4.4 运行方式

**方式 A：完整流水线（自动跳过已完成的阶段）**

```bash
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/xxx.json \
  --stage all
```

**方式 B：仅重定向（已有对应关系模型时）**

```bash
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/xxx.json \
  --stage retarget
```

**方式 C：直接调用解算脚本（跳过流水线逻辑）**

```bash
python scripts/retarget_smpl_to_humanoid_surface_vector.py \
  --config configs/weichai_f1_29_base.json \
  --data sample_data/xxx/...npz \
  --seq-key xxxx \
  --out output/.../xxx.npz
```

### 4.5 输出格式

`.npz` 文件包含：

| 字段 | 形状 | 说明 |
|---|---|---|
| `qpos` | `(T, D)` | 关节位置指令序列 |
| `fps` | `(1,)` | 帧率 |
| `frame_ids` | `(T,)` | 帧索引 |
| `ground_z` | `(1,)` | 地面高度 |
| `robot_name` | `()` | 机器人名称 |
| `robot_joint_names` | `(D,)` | 各关节名称 |
| `robot_xml` | `()` | 完整 MJCF |
| `smpl_scale` | `(1,)` | 人体缩放系数 |

> D = 自由度（XYBER X1 / Weichai F1-29 都是 36）

---

## 5. 数据源类型

### 5.1 SMPL-X NPZ（标准格式）

用于 LAFAN1、HiPHI 等数据集。

```
配置:
  "motion": {
    "data": "sample_data/lafan1_smplx",
    "seq_key": "dance1_subject2"
  }
```

加载逻辑：扫描目录下的 `.npz` 文件，按 `seq_key` 选取。

所需字段：`poses` / `trans` / `betas` / `gender` / `mocap_framerate`

### 5.2 SMPL-X NPY 序列

用于 OmniContact 等数据集。

```
配置:
  "motion": {
    "data": "sample_data/omnicontact/soccer/...",
    "seq_key": "20260330000586_1_1775269234"
  }
```

加载逻辑：检测目录下是否包含 `poses.npy` / `transl.npy` / `betas.npy`。

### 5.3 NR (Neural Retargeting) FBX/BVH

用于 NR 数据集。

```
配置:
  "motion": {
    "data": "sample_data/nr/xxx",
    "seq_key": "xxxx_motion_actor_retarget"
  }
```

### 5.4 数据源判断与加载

参考 [scripts/smpl_surface_retarget_common.py](scripts/smpl_surface_retarget_common.py) 中的 `load_motion_collection()` 函数：

```python
def load_motion_collection(path):
    if path.is_dir():
        if is_nr_root(path):      → NR FBX/BVH 格式
        if is_npy_sequence(path): → 单目录 NPY 序列
        else:                     → 扫描 .npz 文件目录
    if .npz:  → 单个 NPZ 文件
    if .bvh:  → BVH 动画文件
```

---

## 6. 跨 Beta 复用

### 6.1 问题

SMPL-X 人体模板的体型由 beta 参数决定。不同的动作序列可能使用不同的 beta 值，导致人体模板的形状不同。默认情况下，对应关系是 beta 绑定的，换序列需要重新训练。

### 6.2 解决方案：`reuse_across_smplx_betas`

启用跨 beta 复用后，将已有的一组 slots 通过重心坐标映射到新的人体模板上：

```json
{
  "correspondence": {
    "reuse_across_smplx_betas": true,
    "shared_smplx_template": {
      "name": "smplx_neutral_betas_xxxx",
      "betas": [1.4775, 0.6674, ...],
      "gender": "neutral"
    }
  }
}
```

原理：

1. 在已有（训练好的）模板上计算 slots 的 **重心坐标**
2. 对新模板，将同一组重心坐标应用到新顶点位置
3. 得到新模板上的等效 slots

> 💡 适用于不同人体数据源使用同一 UMR 模型的情况（如 LAFAN1 → HiPHI、OmniContact）。

---

## 7. 可视化与录屏

### 7.1 播放重定向结果

```bash
# 通过流水线
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/xxx.json \
  --stage view

# 直接调用查看器
python scripts/visualize_robot_retarget_result.py \
  --result output/xxx/xxx.npz \
  --show-source-slots \
  --show-robot-slots
```

### 7.2 录制视频

```bash
python scripts/visualize_robot_retarget_result.py \
  --result output/xxx/xxx.npz \
  --record-video output/xxx/xxx.mp4 \
  --play
```

### 7.3 查看器选项

| 选项 | 说明 |
|---|---|
| `--show-source-slots` | 显示人体表面 slot |
| `--show-robot-slots` | 显示机器人表面 slot |
| `--show-ground-contact-map` | 显示地面接触点 |
| `--show-collision-geoms` | 显示碰撞几何体 |
| `--camera-azimuth` | 镜头水平角度 |
| `--camera-elevation` | 镜头俯仰角度 |
| `--camera-distance` | 镜头距离 |
| `--lock-camera` | 锁定镜头位置 |

---

## 8. 命令速查

### 8.1 完整流水线

```bash
# 完整三阶段（自动跳过已完成的阶段）
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/xxx.json \
  --stage all

# 仅重定向
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/xxx.json \
  --stage retarget
```

### 8.2 直接调用（跳过流水线）

```bash
# 解算
python scripts/retarget_smpl_to_humanoid_surface_vector.py \
  --config configs/xxx.json \
  --data sample_data/xxx/... \
  --seq-key xxx \
  --out output/xxx/xxx.npz

# 录视频
python scripts/visualize_robot_retarget_result.py \
  --result output/xxx/xxx.npz \
  --record-video output/xxx/xxx.mp4 \
  --play
```

### 8.3 按数据集

**LAFAN1 舞蹈**

```bash
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/humanoid_retarget_xyber_x1_example.json \
  --stage retarget
```

**HiPHI 起立**

```bash
python scripts/retarget_smpl_to_humanoid_surface_vector.py \
  --config configs/weichai_f1_29_base.json \
  --data sample_data/hiphi/data/Getting_up/get_up/Getting_up-get_up_0004/motion_actor_smplx.npz \
  --seq-key motion_actor_smplx \
  --out output/weichai_f1_29_retarget/Getting_up-get_up_0004_smplx_weichai_f1_29.npz
```

**OmniContact 踢球**

```bash
python scripts/retarget_smpl_to_humanoid_surface_vector.py \
  --config configs/weichai_f1_29_base.json \
  --data sample_data/omnicontact/soccer/case3_cick_right/20260330000586_1_1775269234 \
  --seq-key 20260330000586_1_1775269234 \
  --out output/weichai_f1_29_retarget/case3_cick_right_smplx_weichai_f1_29.npz
```

---

## 9. 故障排除

### 9.1 Embree 缺失

```
Error: surface_sampling._embree_intersector() 抛出异常
```

安装 Embree：

```bash
pip install embreex
```

### 9.2 路径解析错误

当出现 `File not found` 或路径不对时，检查：

1. MJCF 中的相对路径是基于配置文件位置解析的
2. 使用 `resolve_path()` 的配置，相对路径基于配置文件所在目录
3. 其他路径基于项目根目录

### 9.3 对应关系不匹配

```
ValueError: Slot sample 'xxx' not found in [...]
```

表示当前动作序列的 beta 值与对应关系模型不匹配。解决办法：

- 启用 `reuse_across_smplx_betas` 功能
- 或为当前序列重新训练对应关系模型

### 9.4 GPU 显存不足

降低 `batch_size` 或 `smplx_batch_size` 参数：

```json
{
  "retarget": {
    "smplx_batch_size": 1024
  }
}
```

### 9.5 派生 MJCF 污染

每个动作序列会在源 MJCF 旁生成 `{seq_name}.floating_mjcf.xml`。这些可以安全删除，不影响原始文件。

---

## 附录

### A. 支持的机器人

| 机器人 | 配置 | 自由度 | 对应模型 |
|---|---|---|---|
| XYBER X1 | `robot_configs/humanoid_retarget_xyber_x1_example.json` | 36 | SME-X Neutral |
| Weichai F1-29 | `robot_configs/humanoid_retarget_weichai_f1_29_example.json` | 36 | SME-X Neutral |

### B. 数据集支持

| 数据集 | 源格式 | 数据目录 | 特征 |
|---|---|---|---|
| LAFAN1 | SME-X `.npz` | `sample_data/lafan1_smplx/` | 动作捕捉舞蹈 |
| HiPHI | SME-X `.npz` | `sample_data/hiphi/` | 人体-物体交互 |
| OmniContact | SME-X `.npy` 序列 | `sample_data/omnicontact/` | 全身接触含足球 |
| NR | FBX+BVH | `sample_data/nr/` | 角色动画重定向 |

### C. 输出目录结构

```
output/
├── correspondence_{template}_{robot}/    ← 对应关系模型
│   ├── correspondence_slots_final.npz
│   └── checkpoint-final.pt
│
├── {robot}_retarget/                     ← 重定向结果
│   ├── {seq1}_{robot}.npz
│   ├── {seq1}_{robot}.mp4
│   ├── {seq2}_{robot}.npz
│   └── {seq2}_{robot}.mp4
```

```
umr_data/
├── README.md
├── {robot}_lafan1_dance/
├── {robot}_hiphi_getting_up/
└── {robot}_omnicontact_kick/
```

### D. 数据加载流程图

```
load_motion_collection(path)
      │
      ├── path.is_dir()?
      │     │
      │     ├── is_nr_root()?  ──▶  load_nr_motion_collection()
      │     │                           │
      │     │                           └── scene.fbx → skin cluster → vertices
      │     │                               + motion.bvh → joint angles
      │     │
      │     ├── is_flat_sequence()? ──▶  load_flat_sequence()
      │     │                           │
      │     │                           └── poses.npy + transl.npy + betas.npy
      │     │                               (OmniContact 格式)
      │     │
      │     └── else ──▶  扫描 *.npz / *.bvh 文件
      │                    │
      │                    └── load_smplx_npz_motion() (每个文件)
      │                        (LAFAN1 / HiPHI 格式)
      │
      ├── path.suffix == ".npz"? ──▶  load_smplx_npz_motion()
      │
      └── path.suffix == ".pkl"? ──▶  load_compressed_motion_pickle()
```

---

> **文档版本**：2026-10-26
