# UMR 重定向数据

本目录按机器人型号存放 UMR 重定向结果，各机器人目录再按动作来源或数据用途分组。
共收录 **172 条轨迹 / 145,168 帧**，其中 4 条为 F1 暂缓候选。条数按 `.npz` 文件计，帧数为各轨迹的 `qpos` 行数之和。

| 目录 | 机器人 | 配置文件 | 结果条数 | 总帧数 |
|---|---|---|---|---|
| [`X1/`](X1) | XYBER X1（`xyber_x1`，1.267 m） | [configs/xyber_x1_base.json](../configs/xyber_x1_base.json) | 13 | 25,937 |
| [`F1/`](F1) | 潍柴 F1-29（`weichai_f1_29`，1.286 m） | [configs/weichai_f1_29_base.json](../configs/weichai_f1_29_base.json) | 129 | 92,082 |
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
│   ├── accad_walking/          B1–B4、快走
│   ├── accad_walking_extra/    转向与倒退走
│   ├── accad_running/          起跑、停跑、倒跑与冲刺
│   ├── accad_general/          站立、重心摆动
│   ├── accad_capability_candidates/  ACCAD 能力候选，含 _deferred 暂缓片段
│   ├── 100style_locomotion/    左右侧移
│   ├── cmu_locomotion/         CMU 运动片段
│   ├── cmu_capability_candidates/    原地转向、弧线、侧移
│   ├── hdm05_locomotion/       倒走与左右定向行走
│   ├── hdm05_capability_candidates/  转向、低速、斜向、侧步
│   ├── lafan1_locomotion/      LAFAN1 走跑、慢走弧线与停走重启
│   ├── lafan1_recovery/        受推恢复
│   ├── hiphi_getting_up/       起身
│   ├── lafan1_dance/           舞蹈
│   └── omnicontact_kick/       射门
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

## F1（潍柴 F1-29）— 129 条

| 目录 | 条数 | 帧数 | 说明 |
|---|---|---|---|
| [`accad_walking/`](F1/accad_walking) | 5 | 3,557 | B1–B4 与 X1 同源，另含快走 S007 |
| [`accad_walking_extra/`](F1/accad_walking_extra/README.md) | 24 | 23,505 | 转向与倒退走，与 G1 的 24 条行走轨迹逐条同源 |
| [`accad_running/`](F1/accad_running) | 12 | 5,374 | C2–C5 与 X1 同源，另含起跑、倒跑、跑走转换和冲刺 |
| [`accad_general/`](F1/accad_general) | 2 | 1,803 | 站立与重心摆动 |
| [`accad_capability_candidates/`](F1/accad_capability_candidates/README.md) | 24 | 15,540 | 停步与反向、侧移、重心摆动及进退步候选，含新增 C25 侧步裁剪 |
| [`accad_capability_candidates/_deferred/`](F1/accad_capability_candidates/_deferred/README.md) | 4 | 2,858 | 暂缓的 ACCAD 能力候选，单独计数 |
| [`100style_locomotion/`](F1/100style_locomotion) | 4 | 1,204 | 左右侧移 |
| [`cmu_locomotion/`](F1/cmu_locomotion) | 4 | 4,526 | CMU 运动片段 |
| [`cmu_capability_candidates/`](F1/cmu_capability_candidates) | 17 | 7,956 | 原地转向、弧线和侧移窗口 |
| [`hdm05_locomotion/`](F1/hdm05_locomotion) | 6 | 3,240 | 倒走与左右定向行走 |
| [`hdm05_capability_candidates/`](F1/hdm05_capability_candidates) | 8 | 3,656 | 原地转向、低速、斜向和侧步窗口 |
| [`lafan1_locomotion/`](F1/lafan1_locomotion) | 14 | 3,079 | 7 条历史轨迹及 7 条新增慢走、弧线和停走重启片段 |
| [`lafan1_recovery/`](F1/lafan1_recovery) | 2 | 600 | 受推恢复 |
| [`hiphi_getting_up/`](F1/hiphi_getting_up) | 1 | 5,468 | HiPHI 起身，使用通用 SMPL-X 路径 |
| [`lafan1_dance/`](F1/lafan1_dance) | 1 | 3,945 | LAFAN1 舞蹈 |
| [`omnicontact_kick/`](F1/omnicontact_kick) | 1 | 5,771 | OmniContact 射门 |

- **ASE F1 行走参考数据（22 条）**分布在 `accad_general/`、`accad_walking/`、`accad_running/`、`cmu_locomotion/` 和 `lafan1_locomotion/`。 [片段与回放索引](F1/README_ase_locomotion.md) · [来源、哈希与 ASE 训练映射](F1/_ase_locomotion_manifest.json)
- **首批 ACCAD F1 能力候选（23 条）**已做运动学几何初筛，动力学和训练表现待验证。 [候选片段与回放](F1/accad_capability_candidates/README.md) · [几何指标与来源清单](F1/accad_capability_candidates/manifest.json)
- **2026-11-27 F1 补充交付（49 条 / 21,058 帧）**含 45 条正式补充和 4 条暂缓候选。 [交付说明](F1/README_capability_delivery_20261127.md) · [逐段来源、帧数与哈希](F1/_capability_delivery_20261127.json)

本次补充的 49 条轨迹均有同名 `.mp4` 回放，视频为 720p、30 fps，轨迹帧率以 `.npz` 中的 `fps` 为准。

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

所有轨迹 `.npz` 共有以下字段：

- `qpos` — `(T, 36)`，每帧含根位姿（3 维位置与 4 维四元数）和 29 个关节位置
- `fps`、`frame_ids` — 帧率与帧索引
- `robot_name`、`robot_xml`、`robot_joint_names` — 机器人型号、模型路径与关节名称
- `source_format`、`source_data`、`source_sequence_key` — 数据格式与来源

额外字段随导出流程变化。常规重定向结果含 `smpl_scale` 和 `ground_z`，从 ASE 归档恢复的 3 条轨迹含 `robot_joint_limits` 和 `reference_sha256`。GitLab 的 `.npz` 通过 Git LFS 管理，可用 `git lfs pull` 获取。GitHub 发布版直接提交重定向后的 `.npz` 文件。

## 命名约定

轨迹通常以动作标识和机器人型号命名，例如 `Female1_C8_back_run_to_stand_weichai_f1_29.npz`。历史文件也使用 `_f1` 和 `_x1` 等后缀。X1 的部分历史视频使用单独的文件名，例如 `Getting_up_xyber_x1.mp4`。

## 数据来源

- **ACCAD** 由 [Ohio State University ACCAD](https://accad.osu.edu/research/motion-lab) 提供。新增 ACCAD 与 CMU 片段的 AMASS 来源文件和哈希见 F1 数据清单。
- **LAFAN1** 来自 [Ubisoft La Forge Animation Dataset](https://github.com/ubisoft/ubisoft-laforge-animation-dataset)。舞蹈、走跑片段及训练归档的来源记录见对应目录和清单。
- **HDM05、CMU、100STYLE** 的新增片段、源序列与裁剪区间见 [F1 补充交付清单](F1/_capability_delivery_20261127.json)。
- **HiPHI**、**OmniContact**、**NR** 片段分别收录在上方目录索引中。重新生成时，请先获取对应的源动作和模型文件。

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
