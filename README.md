# F1-UMR — 人形机器人运动重定向

基于 [UMR (Unified Motion Retargeting)](https://github.com/hanyang9/UMR) 框架，把人体动作捕捉数据重定向到
**潍柴 F1-29 / XYBER X1 / Unitree G1** 三台人形机器人。

## 项目说明

UMR 通过点云对应关系学习，把人体表面运动映射到机器人关节空间，核心三阶段：

1. **构建对应关系** — 采集人体模板与机器人在 T-pose 下的表面点云（`--stage build`）
2. **训练对应模型** — 训练残差自编码器学习人体-机器人点云对应（`--stage train`）
3. **运动重定向** — 逐帧解算机器人关节指令 qpos（`--stage retarget`）

## 支持机器人

| 机器人 | 身高 | qpos | 配置文件 | 机器人模型 |
|---|---|---|---|---|
| Weichai F1-29（`weichai_f1_29`） | 1.286 m | 36 = 7 + 29 | [configs/weichai_f1_29_base.json](configs/weichai_f1_29_base.json) | `assets/F1.5/weichai_f1_29/mjcf/weichai_f1_29.xml` |
| XYBER X1（`xyber_x1`） | 1.267 m | 36 = 7 + 29 | [configs/xyber_x1_base.json](configs/xyber_x1_base.json) | `assets/F1/F1_resource/mjcf/x1_29dof_raw.xml` |
| Unitree G1（`unitree_g1`） | 1.323 m | 36 = 7 + 29 | [czy/g1/umr_g1_config.json](czy/g1/umr_g1_config.json) | [czy/g1/g1_29dof_umr.xml](czy/g1/g1_29dof_umr.xml) |

三台机器人的 `qpos` 都是 36 维（7 位根位姿 + 29 标量关节），轨迹格式完全一致，可互换对比。

> **注意**：仓库自带的 `assets/g1/` 全部是 LFS 指针，`g1_29dof.xml` 引用的 36 个网格没有实体，
> MuJoCo 加载会失败。G1 请用 `czy/g1/` 这套完整模型（见 [czy/g1/README.md](czy/g1/README.md)）。
> 要恢复仓库原生 G1 路径需 `git lfs pull --include="assets/g1/**"`。

## 前置条件

### 1. 人体模型文件（SMPL-X）

**必须**从 SMPL-X 官方渠道下载，因授权协议无法随仓库分发：

```text
smpl/SMPLX_NEUTRAL.pkl    ← 必需
smpl/SMPLX_MALE.pkl       ← 可选
smpl/SMPLX_FEMALE.pkl     ← 可选
```

获取方式：访问 [SMPL-X 官网](https://smpl-x.is.tue.mpg.de/)，注册并接受使用条款后下载。
目录下 `smpl/README.md` 有更多说明。

### 2. 训练好的对应关系模型

`output/correspondence_*/` 下，`correspondence_slots_final.npz` 由 LFS 跟踪（`git lfs pull` 获取）：

| 对应关系 | 用于 | 文件 |
|---|---|---|
| `correspondence_xyber_x1_smplx_neutral_betas_c4eb7419e9` | X1（ACCAD 等通用源） | ✅ |
| `correspondence_weichai_f1_29_smplx_neutral_betas_c4eb7419e9` | F1（ACCAD 等通用源） | ✅ |
| `czy/g1/correspondence/trained/` | G1（ACCAD 等通用源） | ✅ 见 [czy/g1](czy/g1) |

另外还有若干**源数据专用**的对应关系（HiPHI / OmniContact / NR / 角色动画），
因为不同来源的 SMPL-X `betas` 不同 → 模板不同 → 必须各自一套。

> [G1 的 `checkpoint-final.pt`](czy/g1/correspondence/trained/checkpoint-final.pt) 以普通 Git 文件保存，大小约 90.26 MiB。重定向及 `--stage all` 复用的是导出的 `correspondence_slots_final.npz`。

## 快速开始

### 环境准备

```bash
conda create -n umr python=3.12 pip -y
conda activate umr
pip install --index-url https://download.pytorch.org/whl/cu121 torch==2.4.1
pip install -r requirements-umr.txt
```

### 重定向单个动作

```bash
python scripts/retarget_smpl_to_humanoid_surface_vector.py \
  --config configs/weichai_f1_29_base.json \
  --data sample_data/ACCAD/Female1Walking_c3d/B1_-_stand_to_walk_stageii.npz \
  --seq-key B1_-_stand_to_walk_stageii \
  --out umr_data/F1/accad_walking/B1_demo_weichai_f1_29.npz
```

G1 把 `--config` 换成 `czy/g1/umr_g1_config.json`、输出换成 `umr_data/G1/` 即可。

### 录制视频

```bash
python scripts/visualize_robot_retarget_result.py \
  --result umr_data/F1/accad_walking/B1_demo_weichai_f1_29.npz \
  --record-video umr_data/F1/accad_walking/B1_demo_weichai_f1_29.mp4 \
  --play
```

## 批量重定向

所有批处理脚本都**自动跳过已完成动作**，支持断点续跑：

| 脚本 | 范围 | 输出到 |
|---|---|---|
| [batch_f1_walking.py](batch_f1_walking.py) | F1：ACCAD 行走 B1-B4 | `umr_data/F1/accad_walking/` |
| [batch_f1_walking_extra.py](batch_f1_walking_extra.py) | F1：纯行走补充 24 条（转向 / 倒退） | `umr_data/F1/accad_walking_extra/` |
| [batch_running.py](batch_running.py) | X1 + F1：ACCAD 跑步 C2-C5 | `umr_data/{X1,F1}/accad_running/` |
| [batch_f1_hoi.py](batch_f1_hoi.py) | F1：HiPHI 起身 + OmniContact 射门（`--which hiphi\|kick\|both`） | `umr_data/F1/{hiphi_getting_up,omnicontact_kick}/` |
| [czy/g1/batch_g1_walking_24.py](czy/g1/batch_g1_walking_24.py) | G1：24 条纯行走（任务表从 F1 脚本导入，保证逐条对齐） | `umr_data/G1/accad_walking/` |
| [czy/g1/batch_g1_supplement.py](czy/g1/batch_g1_supplement.py) | G1：6 条代表 / 节律动作（走、跑、跳跃步） | `umr_data/G1/{accad_walking,accad_running,accad_general}/` |

## 重定向结果

共 **172 条 / 145,168 帧**，按机器人分类存放在 `umr_data/X1`、`umr_data/F1`、`umr_data/G1`。

| 目录 | 条数 | 帧数 | 内容 |
|---|---|---|---|
| `umr_data/X1/` | 13 | 25,937 | ACCAD 走/跑 + HiPHI 起身 + LAFAN1 舞蹈 + NR 坐姿 + OmniContact 射门 + 回旋踢 |
| `umr_data/F1/` | 129 | 92,082 | 行走、跑步、转向、侧移和恢复等动作，含 4 条 ACCAD 暂缓候选 |
| `umr_data/G1/` | 30 | 27,149 | ACCAD 走（24 条与 F1 逐条对齐 + B1/B3）/ 跑 + 跳跃步 |

2026-11-27 补充 49 条 F1 轨迹，均附同名回放。 [F1 补充交付说明](umr_data/F1/README_capability_delivery_20261127.md)

完整清单、轨迹格式和命名约定见 **[umr_data/README.md](umr_data/README.md)**。
G1 的质量校验与跨机器人对比见 **[umr_data/G1/README.md](umr_data/G1/README.md)**。

## 训练对应关系模型

在新机器人上首次使用，或需要重建对应关系时：

```bash
# Stage 1: 构建对应关系数据集（写 data/correspondence_*.npz）
python scripts/humanoid_retarget_pipeline.py --config configs/weichai_f1_29_base.json --stage build

# Stage 2: 训练残差自编码器（写 output/correspondence_*/(correspondence_slots_final.npz, checkpoint-final.pt)）
python scripts/humanoid_retarget_pipeline.py --config configs/weichai_f1_29_base.json --stage train
```

- 已有 `correspondence_slots_final.npz` 且与当前配置兼容时会**直接复用**（打印 `reuse correspondence slots`）；
  加 `--force-train` 才会重训（500 epoch，G1 实测约 1 分钟）。
- G1 的配置里带 `robot.xml_policy.add_freejoint_root = false`：G1 模型本身已有自由关节，
  这样设置可以避免求解器为每个动作额外生成一份派生 MJCF。
- 完整流水线细节见 [czy/exp/pipeline.md](czy/exp/pipeline.md)。

## 项目结构

```
configs/                 ← F1 / X1 机器人配置
robot_configs/           ← UMR 标准配置模板（含 G1 示例）
scripts/                 ← 核心脚本（重定向 / 建模板 / 训练 / 可视化 / 批处理）
smpl/                    ← SMPL-X 模型（需自行下载）
sample_data/             ← 源运动数据（ACCAD 完整可用；其余多为 LFS 指针）
output/                  ← 对应关系模型（slots npz 已纳入 LFS）
tools/legacy/            ← 归档工具（HOI 源数据接触图查看器，无配套数据，仅存档）
umr_data/
  X1/  F1/  G1/          ← 重定向结果，按机器人分类，内部再按动作来源分组
czy/
  g1/                    ← G1 完整模型 + 对应关系 + 采集脚本
  html/                  ← 组内分享页 HTML + 流水线流程图 SVG
  exp/                   ← 流程与实验文档
batch_f1_walking.py      ← F1 行走批处理
batch_f1_walking_extra.py← F1 纯行走补充（24 条）
batch_running.py         ← X1 + F1 跑步批处理
batch_f1_hoi.py          ← F1 HiPHI 起身 + OmniContact 射门
```

> 几何工具库 `scripts/smpl_geometry_utils.py`（SMPL 动态表面采样 / 蒙皮定点 / `model_faces`）
> 原先寄生在根目录的查看器脚本里，现已抽出；查看器本体归档到 `tools/legacy/`。

## 文档索引

| 文档 | 内容 |
|---|---|
| [umr_data/README.md](umr_data/README.md) | 全部重定向结果的清单、格式、命名约定和脚本索引 |
| [umr_data/G1/README.md](umr_data/G1/README.md) | G1 数据详情：质量校验、跳跃步腾空相、与 F1 的跨机器人对比 |
| [czy/g1/README.md](czy/g1/README.md) | G1 模型与对应关系；为什么要单独做一个 `g1_29dof_umr.xml` |
| [czy/exp/pipeline.md](czy/exp/pipeline.md) | UMR 完整流水线说明 |
| [czy/html/UMR_pipeline_组内分享.html](czy/html/UMR_pipeline_组内分享.html) | 单文件自包含演示页（内嵌点云、流程图、回放视频，可离线打开） |

## 体积与入库注意

- GitLab 通过 Git LFS 跟踪 `.npz`。GitHub 发布版用普通 Git 文件存放已重定向的轨迹，省去源数据、SMPL-X 模型及其余 LFS 对象。
- 回放视频 `.mp4` 在两个远端都以普通 Git 文件存储。
- `czy/html/UMR_pipeline_组内分享.html` 是 12.8 MB 单文件（base64 内嵌），每次重新导出都会产生新 blob。

## 引用

```bibtex
@misc{cao2026unifiedmotionretargetinghumanoids,
  title={Unified Motion Retargeting for Humanoids with Learned Point Cloud Correspondence},
  author={Hanyang Cao and Yuetong Fang and Taesoo Kwon and Runyi Yu and Ji Ma and Jing Tan and Yangchen Zhou and Baoze Du and Yi Gu and Yukang Gao and Ruoli Dai and Lei Han and Renjing Xu},
  year={2026},
  eprint={2609.02134},
  archivePrefix={arXiv},
  primaryClass={cs.RO}
}
```
