# UMR 重定向数据

本目录按**机器人型号**分类存放 UMR 的重定向结果：`X1` / `F1` / `G1` 三个子目录，
每个子目录内再按**动作来源**（ACCAD 走/跑、HiPHI、LAFAN1、OmniContact、NR 等）分组。

| 目录 | 机器人 | 配置文件 | 结果条数 | 总帧数 |
|---|---|---|---|---|
| [`X1/`](X1) | XYBER X1（`xyber_x1`，1.267 m） | [configs/xyber_x1_base.json](../configs/xyber_x1_base.json) | 13 | 25,937 |
| [`F1/`](F1) | 潍柴 F1-29（`weichai_f1_29`，1.286 m） | [configs/weichai_f1_29_base.json](../configs/weichai_f1_29_base.json) | 35 | 43,855 |
| [`G1/`](G1) | Unitree G1（`unitree_g1`，1.323 m） | [czy/g1/umr_g1_config.json](../czy/g1/umr_g1_config.json) | 30 | 27,149 |

```
umr_data/
├── X1/
│   ├── accad_walking/          B1-B4
│   ├── accad_running/          C2-C5
│   ├── hiphi_getting_up/       起立
│   ├── humanoid_spinkick/      回旋踢
│   ├── lafan1_dance/           舞蹈
│   ├── nr_xuzeyan_seat09/      坐姿
│   └── omnicontact_soccer_kick/ 射门
├── F1/
│   ├── accad_walking/          B1-B4
│   ├── accad_walking_extra/    纯行走补充 24 条（含本目录 README）
│   ├── accad_running/          C2-C5
│   ├── hiphi_getting_up/
│   ├── lafan1_dance/
│   └── omnicontact_kick/
└── G1/
    ├── accad_walking/          26 条（24 条与 F1 逐条对齐 + B1/B3）
    ├── accad_running/          C3、C5
    ├── accad_general/          跳跃步 A14/A15
    ├── _run_logs/              运行日志与历史汇总
    └── README.md               G1 专项说明
```

## X1（XYBER X1）— 13 条

`accad_walking/`（4 条，来自 ACCAD `Female1Walking_c3d`）

| 文件 | 帧数 | 时长 | npz | mp4 |
|---|---|---|---|---|
| `B1_stand_to_walk_x1` | 747 | 6.2s | 102 KB | 3.63 MB |
| `B2_walk_to_stand_x1` | 682 | 5.7s | 94 KB | 3.50 MB |
| `B3_walk1_x1` | 915 | 7.6s | 124 KB | 5.96 MB |
| `B4_stand_to_walk_back_x1` | 906 | 7.5s | 123 KB | 4.35 MB |

`accad_running/`（4 条，来自 `Female1Running_c3d`）

| 文件 | 帧数 | 时长 | npz | mp4 |
|---|---|---|---|---|
| `C2_Run_to_stand_x1` | 639 | 5.3s | 87 KB | 3.14 MB |
| `C3_Run_x1` | 203 | 1.7s | 28 KB | 1.99 MB |
| `C4_Run_to_walk_x1` | 424 | 3.5s | 58 KB | 3.12 MB |
| `C5_Walk_to_run_x1` | **650** | 5.4s | 88 KB | 4.06 MB |

其他来源

| 目录 | npz | 来源 | 帧数 | 时长 | mp4 |
|---|---|---|---|---|---|
| `lafan1_dance/` | `dance1_subject2_smplx_xyber_x1` | LAFAN1 舞蹈 | 3,945 | 131.5s | 29.49 MB |
| `hiphi_getting_up/` | `Getting_up-get_up_0004_hsi_hoi_xyber_x1` | HiPHI 起身 | 5,468 | 60.8s | 45.62 MB（另有 `Getting_up-get_up_0004.mp4` 9.25 MB） |
| `omnicontact_soccer_kick/` | `case3_kick_right_hsi_hoi_xyber_x1` | OmniContact 射门 | 5,771 | 64.1s | 55.43 MB |
| `nr_xuzeyan_seat09/` | `MWVOPT_..._retarget_nr_xyber_x1` | NR 坐姿 | 5,509 | 61.2s | 38.70 MB |
| `humanoid_spinkick/` | `humanoid_spinkick_character_xyber_x1` | 角色动画 | 78 | 1.3s | 0.99 MB |

## F1（潍柴 F1-29）— 35 条

`accad_walking/`（4 条）、`accad_running/`（4 条）与 X1 对应，文件名为
`{动作}_weichai_f1_29` / `{动作}_f1`；帧数与 X1 完全一致（同一源轨迹、同一求解配置），
差别只在机器人形态——所以这 8 组是天然的 X1↔F1 对照数据。

| 目录 | 条数 | 帧数 | 说明 |
|---|---|---|---|
| `accad_walking/` | 4 | 3,250 | B1-B4，同 X1 |
| `accad_walking_extra/` | 24 | 23,505 | 纯行走补充（转向/倒退），与 G1 逐条对齐，详见 [该目录 README](F1/accad_walking_extra/README.md) |
| `accad_running/` | 4 | 1,916 | C2-C5，同 X1 |
| `hiphi_getting_up/` | 1 | 5,468 | HiPHI 起身（走的是通用 SMPL-X 路径） |
| `lafan1_dance/` | 1 | 3,945 | LAFAN1 舞蹈 |
| `omnicontact_kick/` | 1 | 5,771 | OmniContact 射门 |

## G1（Unitree G1）— 30 条

| 目录 | 条数 | 帧数 | 说明 |
|---|---|---|---|
| `accad_walking/` | 26 | 25,167 | 其中 24 条与 F1 的 `accad_walking_extra` 逐条同名对齐，另加 B1/B3 |
| `accad_running/` | 2 | 853 | C3、C5 |
| `accad_general/` | 2 | 1,129 | 跳跃步 A14（站立→跳跃步）、A15（跳跃步→站立），本目录唯一带腾空相的动作 |

G1 的机器人模型与对应关系模型**不在本目录**：

- 模型：[czy/g1/g1_29dof_umr.xml](../czy/g1/g1_29dof_umr.xml)（+ `czy/g1/meshes/`）
- 对应关系数据集与训练产物：[czy/g1/correspondence/](../czy/g1/correspondence)
- 每个 npz 的 `robot_xml` 直接指向 `czy/g1/g1_29dof_umr.xml`，该模型用绝对路径引用
  `czy/g1/meshes/` —— 所以**移动 `czy/g1/meshes/` 会让回放失效**

详细说明（含质量校验、跨机器人对比）见 [G1/README.md](G1/README.md)。

## 数据文件格式

每个 `.npz` 包含 12 个字段：

- `qpos` — 关节位置轨迹 `(T, 36)`（7 根位姿 + 29 关节）
- `fps`、`frame_ids` — 帧率与帧索引
- `robot_name`、`robot_xml`、`robot_joint_names`、`robot_joint_limits` — 机器人定义
- `smpl_scale` — 人体→机器人缩放系数
- `source_format`、`source_data`、`source_sequence_key` — 源数据溯源

## 命名约定

- ACCAD 结果：`{子集前缀}_{动作号}_{描述}_{机器人}.npz`，如 `Male1_Walk_B10_turn_left_45_weichai_f1_29.npz`
- 非 ACCAD 结果：`{源序列名}_{adapter}_{机器人}.npz`，如 `dance1_subject2_smplx_xyber_x1.npz`
- X1 的历史 mp4 命名与 npz stem 不完全一致（如 `Getting_up_xyber_x1.mp4`），属早期遗留

## 数据来源

- **ACCAD**：[Ohio State University ACCAD](https://accad.osu.edu/research/motion-lab)（仓库内唯一一份完整可用的源数据）
- **LAFAN1**：[Ubisoft La Forge Animation Dataset](https://github.com/ubisoft/ubisoft-laforge-animation-dataset)（本仓库只带 `dance1_subject2` 一条，且是 LFS 指针，需 `git lfs pull`）
- **HiPHI**、**OmniContact**、**NR**、**GRAIL**、**AdaPT**：源文件均为 LFS 指针，需先 `git lfs pull` 才能重新生成

## 相关脚本

| 脚本 | 用途 |
|---|---|
| [batch_f1_walking.py](../batch_f1_walking.py) | F1：ACCAD 行走 B1-B4 |
| [batch_f1_walking_extra.py](../batch_f1_walking_extra.py) | F1：纯行走补充 24 条 |
| [batch_running.py](../batch_running.py) | X1 + F1：ACCAD 跑步 C2-C5 |
| [batch_f1_hoi.py](../batch_f1_hoi.py) | F1：HiPHI 起身 + OmniContact 射门（`--which hiphi\|kick\|both`，源数据仍为 LFS 指针时给出拉取提示） |
| [czy/g1/batch_g1_walking_24.py](../czy/g1/batch_g1_walking_24.py) | G1：24 条纯行走（任务表从 F1 脚本导入） |
| [czy/g1/batch_g1_supplement.py](../czy/g1/batch_g1_supplement.py) | G1：B1/B3/B10/C3/C5/B14 + 跳跃步 A14/A15 |

单条重定向的统一入口是
[scripts/retarget_smpl_to_humanoid_surface_vector.py](../scripts/retarget_smpl_to_humanoid_surface_vector.py)，
回放/录像用 [scripts/visualize_robot_retarget_result.py](../scripts/visualize_robot_retarget_result.py)：

```bash
python scripts/visualize_robot_retarget_result.py \
  --result umr_data/F1/accad_walking/B1_stand_to_walk_weichai_f1_29.npz --play
```