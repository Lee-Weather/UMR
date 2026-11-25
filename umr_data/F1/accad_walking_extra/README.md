# Weichai F1-29 · ACCAD 纯行走补充数据

对 ACCAD 中**纯行走**（直线 / 转向 / 倒退）动作的重定向补充。
`umr_data/F1/accad_walking/` 只有 B1-B4，本目录补齐其余 **24 条**。

- 生成脚本：根目录 [batch_f1_walking_extra.py](../../../batch_f1_walking_extra.py)
- 配置：[configs/weichai_f1_29_base.json](../../../configs/weichai_f1_29_base.json)
- 对应关系模型：[output/correspondence_weichai_f1_29_smplx_neutral_betas_c4eb7419e9](../../../output/correspondence_weichai_f1_29_smplx_neutral_betas_c4eb7419e9)
- 生成时间：2026-11-16，RTX A2000

## 收录范围（24 条 / 23,505 帧 / 3.3 分钟素材）

| 子集 | 条数 | 内容 |
|---|---|---|
| `Female1Walking_c3d` | 11 | B9-B16 转向（45/90/135°/掉头/变向，B12 放弃）、B5-B7 倒退走、B2_t2 走→站重录 |
| `Male1Walking_c3d` | 5 | Walk_B10/B13 转向、B15 掉头、B16 变向、B4 站立→倒退走 |
| `Male2Walking_c3d` | 8 | B9-B15 转向、B4 倒退走（B5 放弃） |

**未收录**（有意排除）：

- 搬箱动作 10 条：`B19 walk_to_pick_up_box`、`B20 walk_with_box`、`B21 put_down_box_to_walk`（含 `_s2`/`_s3`/`_a` 变体）
- 行走衔接变体 20 条：`walk_to_hop`、`walk_to_leap`、`side_step`、`walk_to_crouch`、`crouch_to_walk`、`skip_to_walk`
- **源动作悬空而放弃 2 条**：`Female1_B12_walk_turn_right_90`、`Male2_B5_walk_backwards`（详见下文）

## 文件

- `*.npz` — 关节轨迹（`qpos (T,36)`、`fps`、`robot_joint_names`、`source_data` 等 12 个字段），24 个共 3.1 MB
- `*.mp4` — MuJoCo 回放录像，24 个共 156.6 MB
- `_batch_summary.json` — 每条的重定向/录制状态与耗时（含 2 条 `abandoned` 记录）
- `_validation.json` — NaN / 关节限位 / 步长统计
- `_foot_clearance.json` — 全帧脚底离地高度与触地帧占比
- `_batch.log` — 完整运行日志（含已删除的 2 条）

## 质量核查

| 项 | 结果 |
|---|---|
| 交付量 | **24 npz + 24 mp4**（26 条中 2 条放弃，见下） |
| NaN / Inf | 0 |
| 关节限位越界 | 0 次（29 关节 × 全帧，全部落在 MJCF `range` 内） |
| 逐帧步长 \|dq\| p95 | 0.010–0.022 rad（与已发布结果同量级，无跳变） |
| root 高度 | 0.56–0.66 m |
| 脚部触地（全帧统计） | 触地帧占比 2.4%–100%，中位离地 0–4.3 cm（含负值即轻微穿地），逐条见 `_foot_clearance.json` |

### 已放弃的 2 条轨迹

`Male2_B5_walk_backwards` 与 `Female1_B12_walk_turn_right_90` **已删除，不纳入本数据集**。

原因：这两条的 **ACCAD 源动作本身整段离地**——日志里 `GroundContactMap` 的近地 slot 只有
261/3,993,600 和 598/3,813,376（正常片段是 2.5 万–3 万），`GroundContactAnchor` 只在
4/975 和 15/931 帧激活。而求解器的地面接触目标是"保持源片段的离地高度"
（`ground_target_z = target_distances_for_contact[...]`），因此机器人忠实复现了悬空：

| 片段 | 全帧最低点 | 中位离地 | 触地帧 | 说明 |
|---|---|---|---|---|
| `Male2_B5_walk_backwards` | +1.66 cm | +6.48 cm | 0% | 全程不触地 |
| `Female1_B12_walk_turn_right_90` | +0.24 cm | +5.08 cm | 1.6% | 仅 15/931 帧触地 |

先验证过不是求解权重问题：把 `--ground-contact-map-cost` 提到 30、`--ground-contact-map-threshold`
提到 0.25、`--ground-contact-map-max-points` 提到 256 后重跑，中位离地仅从 5.08 cm 降到 4.84 cm。
也试过按慢变漂移做垂直重接地（可把触地率提到 ~71%），但属于对求解结果的后处理修正，
最终决定不保留这两条，宁可少两条也不要人为改过的轨迹。

若以后想重做，源文件仍在
`sample_data/ACCAD/Male2Walking_c3d/B5_-__Walk_backwards_stageii.npz` 和
`sample_data/ACCAD/Female1Walking_c3d/B12_-_walk_turn_right_(90)_stageii.npz`，
批处理脚本里对应的两行以注释保留。

### 其余片段的离地情况

24 条中触地帧占比 2.4%–100%（最低 `Male1_Walk_B13_turn_right_45` 2.4%、
`Male2_B15_turn_around` 4.4%、`Male1_Walk_B16_turn_change` 5.2%），与已发布结果同量纲
（已发布 11 条中 `case3_kick_right` 2.2%、`B3_walk1` 17.9%），属于当前配置的既有特性，未做额外修正。

## 复现

```bash
python batch_f1_walking_extra.py            # 断点续跑：已存在的 npz/mp4 自动跳过
python batch_f1_walking_extra.py --no-video # 只算轨迹，不录视频
```

## 注意

本目录共 161.6 MB，`.gitignore` **没有**排除 `umr_data/`，且 `.gitattributes` 只把 `*.npz` 纳入 LFS，
**`*.mp4` 不在 LFS 规则里**。若要提交，请先给 `*.mp4` 补上 LFS 规则，或把 mp4 排除出版本库。