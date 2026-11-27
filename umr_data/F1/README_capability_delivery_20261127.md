# F1 参考轨迹补充交付（2026-11-27）

共补充 **49** 段，其中 45 段为正式补充，4 段为 ACCAD 能力候选的 `deferred` 片段。每段均为原帧率 `qpos` + 同名 1280×720@30fps MuJoCo 回放视频。

| 目录 | 段数 | 内容 |
|---|---:|---|
| `hdm05_locomotion` | 6 | HDM05 back/left/right 定向行走 |
| `hdm05_capability_candidates` | 8 | HDM05 pivot/低速/斜向/侧步窗口 |
| `cmu_capability_candidates` | 17 | CMU pivot/弧线/侧移窗口 |
| `100style_locomotion` | 4 | 100STYLE 左右侧移 |
| `lafan1_locomotion` | 7 | LAFAN slow_arc、slow_walk1_s1、pause_restart_multiple（仅新增 7 段） |
| `lafan1_recovery` | 2 | LAFAN recovery_push |
| `accad_capability_candidates` | 1 | ACCAD C25 侧步裁剪（仅新增 1 段） |
| `accad_capability_candidates/_deferred` | 4 | ACCAD 能力候选暂缓片段 |

说明：

- 已存在的 LAFAN 4 段（slow_walk1_s2、slow_walk2_s4、slow_walk3_s3、pause_restart_walk3_s3）与 `accad_capability_candidates/manifest.json`（23 段）均未改动；新增内容另有清单。
- 未收录：`Female1_B12_walk_turn_right_90`、`Male2_B5_walk_backwards`，UMR 已因源动作悬空放弃。
- 各段 `qpos` 内的 `source_data` 保留原重定向输入路径（旧参考审查目录），便于追溯；视频由本机 MuJoCo 3.15 离屏渲染。
- 训练侧 50 Hz `tracking_50hz` 未复制；此处只保存原帧率 `qpos`。

逐段哈希与来源见 [_capability_delivery_20261127.json](_capability_delivery_20261127.json)。
