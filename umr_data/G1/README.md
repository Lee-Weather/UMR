# G1 · 重定向数据

Unitree G1（`unitree_g1`，模型高 1.3228 m，`qpos` 36 维 = 7 根位姿 + 29 关节）的重定向结果，
共 **30 条 / 27,149 帧 / 3.8 分钟素材**。

- 机器人模型与对应关系模型：[czy/g1/](../../czy/g1)（本目录只放轨迹）
- UMR 配置：[czy/g1/umr_g1_config.json](../../czy/g1/umr_g1_config.json)
- 采集脚本：[czy/g1/batch_g1_walking_24.py](../../czy/g1/batch_g1_walking_24.py)、[czy/g1/batch_g1_supplement.py](../../czy/g1/batch_g1_supplement.py)

## 目录

| 目录 | 条数 | 帧数 | 内容 |
|---|---|---|---|
| `accad_walking/` | **26** | 25,167 | 24 条与 F1 的 `accad_walking_extra` 逐条同名对齐 + `Female1_B1_stand_to_walk`、`Female1_B3_walk1` |
| `accad_running/` | 2 | 853 | `Female1_C3_Run`（跑步）、`Female1_C5_walk_to_run`（行走→跑步） |
| `accad_general/` | 2 | 1,129 | `Female1_A14_stand_to_skip`、`Female1_A15_skip_to_stand`（跳跃步） |
| `_run_logs/` | — | — | 三条批量的运行汇总（`_summary.json` 6 条代表动作、`_summary_walking24.json` 24 条行走），记录每条的重定向/录像耗时；原始日志只含进度条与求解诊断，结论已摘入本文，故未保留 |

每个 npz 的 `robot_xml` 直接指向基座模型 [czy/g1/g1_29dof_umr.xml](../../czy/g1/g1_29dof_umr.xml)，该模型用绝对路径引用 `czy/g1/meshes/`，因此**移动 `czy/g1/meshes/` 会让回放失效**。

## 与 F1 的对齐关系

`accad_walking/` 的 24 条与 `F1/accad_walking_extra/`（原 26 条中放弃 2 条）**逐条同名、同源轨迹**：

| ACCAD 子集 | 条数 | 内容 |
|---|---|---|
| `Female1Walking_c3d` | 11 | B2_t2、B5-B7 倒退走、B9-B16 转向（45/90/135°/掉头/变向） |
| `Male1Walking_c3d` | 5 | Walk_B4 站立→倒退走、B10/B13 转向、B15 掉头、B16 变向 |
| `Male2Walking_c3d` | 8 | B4 倒退走、B9-B15 转向 |

G1 的任务表不是手抄的：`batch_g1_walking_24.py` 运行时从 `batch_f1_walking_extra.py` 的 `TASKS` 导入，
两边永远一致。

## 质量核查（`_validation.json`）

| 项 | 结果 |
|---|---|
| 完成率 | **30/30 npz + 30/30 mp4**，0 失败 |
| NaN / Inf | 0 |
| 关节限位越界 | 0（29 关节 × 27,149 帧；8 条自定义限位全部命中 `matched_same_name=8`） |
| 逐帧步长 p95 | 0.011–0.087 rad（跑步最大） |
| root 高度 | 0.67–0.91 m（G1 站立 0.793 m） |
| 穿地 | **0 条**超过 5 mm（全帧最低 −0.0034 m） |
| 贴地 | 30 条中 **21 条中位离地 < 1 cm** |
| 人体缩放 | `smpl_scale = 0.7685`（= 1.3228 / 1.7213） |

## 跳跃步：唯一带腾空相的两条

| 片段 | root 高度范围 | 双脚 >2 cm | 双脚 >5 cm | 触地帧 |
|---|---|---|---|---|
| `A14_stand_to_skip` | 0.718~0.907 m（18.9 cm） | **56.6%** | 1.0% | 29.3% |
| `A15_skip_to_stand` | 0.681~0.884 m（20.3 cm） | 8.0% | 2.2% | 52.8% |
| 对照 `B3_walk1` | 0.732~0.818 m（8.6 cm） | 23.1% | 0.0% | 58.7% |
| 对照 `C3_Run` | 0.701~0.818 m（11.7 cm） | 40.4% | **26.1%** | 47.8% |

A14 有 56.6% 的帧双脚离地超 2 cm、root 上下走 19 cm，跳跃相被完整还原，落地时脚底最低 −3.4 mm；
A15 触地帧过半，符合"跳完落回站立"的收尾。行走/跑步/跳跃三者的离地曲线区分得很干净，
说明求解器跟着源动作的实际离地情况走，不是靠平滑糊过去的。

## Male1 那 5 条偏悬空——源数据的问题，两个机器人一致

`Male1Walking_c3d` 的 5 条在 G1 上浮 2.8–5.5 cm，但 F1 上同一批参考轨迹浮得几乎一样多：

| 参考轨迹 | F1 中位离地 | G1 中位离地 | 差 |
|---|---|---|---|
| `Walk_B10_turn_left_45` | +3.08 cm | +3.34 cm | +0.26 cm |
| `Walk_B13_turn_right_45` | +4.64 cm | +5.48 cm | +0.84 cm |
| `Walk_B15_turn_around` | +2.50 cm | +2.81 cm | +0.31 cm |
| `Walk_B16_turn_change` | +3.22 cm | +3.64 cm | +0.42 cm |
| `Walk_B4_stand_to_walk_back` | +4.28 cm | +5.09 cm | +0.81 cm |

两台机器人独立求解、对应的却是同一段人体动作，还都浮了差不多的量 → 悬空来自
**ACCAD Male1 源动作本身**（地面重建偏高约 3 cm），不是机器人或求解器。
其余 23 条（Female1 / Male2）中位离地在 −0.0002 ~ +1.8 cm，基本零穿地零悬空。

## 复现

```bash
# 模型与对应关系（在 czy/g1 下，约 40 s + 1 min）
python scripts/humanoid_retarget_pipeline.py --config czy/g1/umr_g1_config.json --stage build
python scripts/humanoid_retarget_pipeline.py --config czy/g1/umr_g1_config.json --stage train
# 24 条纯行走 -> 本目录/accad_walking
python czy/g1/batch_g1_walking_24.py
# 6 条代表/节律动作 -> accad_walking / accad_running / accad_general
python czy/g1/batch_g1_supplement.py
```

单条：

```bash
python scripts/retarget_smpl_to_humanoid_surface_vector.py \
  --config czy/g1/umr_g1_config.json \
  --data sample_data/ACCAD/Female1Walking_c3d/B5_-_walk_backwards_stageii.npz \
  --seq-key B5_-_walk_backwards_stageii \
  --out umr_data/G1/accad_walking/Female1_B5_walk_backwards_unitree_g1.npz
```

回放：

```bash
python scripts/visualize_robot_retarget_result.py \
  --result umr_data/G1/accad_general/Female1_A14_stand_to_skip_unitree_g1.npz --play
```

## 还没覆盖

- ACCAD 其余 200+ 条动作（跑、跳、武术 90 条、搬箱、坐立等）
- G1 的 27dof 左手球拍版（AdaPT 用）、spherehand / largebox 变体 —— `czy/g1` 里没有这些变体的网格
- HiPHI / OmniContact / NR / GRAIL 源 —— 源数据仍是 LFS 指针，需 `git lfs pull` 后才能生成 G1 版本