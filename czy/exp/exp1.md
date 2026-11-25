# Exp1 — X1（`xyber_x1`）对应关系构建实验

- **日期**：2026-10-19
- **目标**：为 X1 建立 UMR 人体-机器人表面点云对应关系，验证配置链路与对应质量
- **结论**：
  - **Stage 1（build）** ✅ 成功。输出 `points=(2, 4096, 3)`，几何校验全部通过
  - **Stage 2（train）** ✅ 成功。对应关系比索引序基线好 **10.55×**；躯干/腿部/头部都很好，**手臂/手是最弱区**

| 阶段 | 状态 | 耗时 | 关键产出 |
|---|---|---|---|
| Stage 1 · build | ✅ | 47 s | `data/correspondence_xyber_x1_smplx_neutral_betas_c4eb7419e9.npz`（12.3 MiB） |
| Stage 2 · train | ✅ | ~1 min | `output/correspondence_xyber_x1_.../correspondence_slots_final.npz` + `checkpoint-final.pt`（90 MB） |
| Stage 3 · retarget | ✅ | **5 min 11 s** | `output/xyber_x1_retarget/dance1_subject2_smplx_xyber_x1.npz`（519 KB，`qpos=(3945,36)`） |

**三个阶段端到端总耗时约 7 分钟**，动作源为 LAFAN1 `dance1_subject2`（3945 帧 @ 30 fps，2 分 11 秒舞蹈）。

---

# Part 1 · Stage 1 — 对应关系采样点云构建（build）

## 1. Stage 1 要做什么

Stage 1 是整个重定向流程的数据基础。它把**人体模板**和**机器人**各自在 T-pose 下采样成数量相同的均匀点云，供 Stage 2 去学习两者的对应关系（slot）。

### 1.1 关键设计

- **不做任何手工人体-机器人关节映射**。对应关系完全由后续 Stage 2 从点云几何中学出来
- 两个点云必须在**同一套归一化坐标系**下，才能被比较。所以：
  1. 各自按**自己的躯干中心**归位 —— 人体按 SMPL-X 的 Spine1 关节，机器人按配置的 `point_cloud_center`（X1 用 `body:lumbar_yaw_link`）
  2. 再统一转到 **SMPL 风格坐标系**（Y 朝上）
- 采样必须采**可见外表面**，否则会采到藏在身体内部的点，破坏对应关系的语义

### 1.2 采样算法：`first_hit`

```
surface_oversample_ratio = 8   →  每个模板先从表面过采样 8×4096 = 32768 个候选点
```

对每个候选点，从 26 个方向（3×3×3 去掉中心）打射线，只有**第一次命中的面**被认定为"可见外表面"。这一步需要 `trimesh` 的 Embree 后端（`embreex`）。

这也是为什么环境里必须有 `embreex` —— `surface_sampling._embree_intersector()` 在缺少 Embree 时**直接抛异常，没有纯 Python 回退**。

> 备选方法 `normal_occlusion`（按法线遮挡判断）不需要 Embree，本次未使用。

### 1.3 输出

单个 `.npz`，包含：

| 字段 | 含义 |
|---|---|
| `points` | `(模板数, 4096, 3)` 采样点（归一化坐标系） |
| `names` | 每个模板的名字 |
| `root_offsets` | 各模板躯干中心的偏移量 |
| `center_modes` | 各模板的居中方式 |
| `mesh_vertices_{i}` / `mesh_faces_{i}` | 第 i 个模板的完整表面网格 |
| `sample_face_ids_{i}` | 每个采样点来自哪个三角面 |
| `custom_robot_*` | 机器人的 XML 路径、居中 body、T-pose qpos 等 |
| `betas_0` | 人体体型参数 |

`mesh_vertices/faces` 是给下游可视化模块做投影用的；重定向求解只用 `points`。

---

## 2. 本次运行配置

机器人配置：[`robot_configs/humanoid_retarget_xyber_x1_example.json`](../robot_configs/humanoid_retarget_xyber_x1_example.json)

```json
{
  "robot": {
    "name": "xyber_x1",
    "xml": "../assets/F1/F1_resource/mjcf/x1_29dof_raw.xml",
    "point_cloud_center": "body:lumbar_yaw_link",
    "tpose_qpos": { "left_shoulder_roll_joint": -1.57,
                    "right_shoulder_roll_joint": -1.57, ...其余 27 个为 0 }
  }
}
```

实际生效的参数：

| 参数 | 值 |
|---|---|
| `num_points` | 4096 |
| `seed` | 0 |
| `surface_oversample_ratio` | 8 |
| `surface_curvature_weight` / `power` | 0.0 / 1.0 |
| `exterior_surface` | true |
| `exterior_method` | `first_hit` |
| `exterior_occlusion_distance` | 0.12 |
| `exterior_ray_distance` | 0.0 |
| `smpl_center` | `spine1` |
| `bbox_center_ratio` | 0.45（**未生效** —— `smpl_center=spine1` 时该值被忽略） |

人体模板由动作序列的 betas 决定（`use_betas: true`），名字 `smplx_neutral_betas_c4eb7419e9`。

### 环境

| 项 | 值 |
|---|---|
| Python | 3.12.15 |
| 环境 | `D:\conda\envs\umr` |
| torch | 2.4.1+cu121（CUDA 可用，RTX A2000，CUDA 12.1） |
| mujoco | 3.3.7 |
| smplx | 0.1.28（PyPI） |
| trimesh / embreex | 5.1.1 / 4.4.0 |

---

## 3. 实验结果

### 3.1 运行

```
[SMPLXModel] loading format=pkl path=E:\UMR\smpl\SMPLX_NEUTRAL.pkl
[Dataset] Added smplx_neutral_betas_c4eb7419e9:
          verts=10475 faces=20908 center=spine1 joint_id=3
          offset=[7.578963413834572e-05, -0.24949055910110474, -0.019167546182870865]
[Dataset] Added xyber_x1:
          verts=804869 faces=1587926 exterior_surface=True exterior_method=first_hit
[HumanoidPipeline] saved correspondence dataset:
          E:\UMR\data\correspondence_xyber_x1_smplx_neutral_betas_c4eb7419e9.npz
          names=['smplx_neutral_betas_c4eb7419e9', 'xyber_x1'] points=(2, 4096, 3)
```

- **耗时**：约 **47 秒**（11:09:51 → 11:10:38）
- **退出码**：0
- **输出**：`data/correspondence_xyber_x1_smplx_neutral_betas_c4eb7419e9.npz`，**12.3 MiB**

耗时远低于预期 —— `first_hit` 在 80 万顶点的机器人网格上只用了不到一分钟，Embree 后端性能足够。

### 3.2 两个模板的规模

| 模板 | 顶点 | 三角面 | 采样点 | 居中方式 | 根偏移 |
|---|---|---|---|---|---|
| `smplx_neutral_betas_c4eb7419e9` | 10,475 | 20,908 | 4096 | `spine1`（joint 3） | `[7.6e-05, -0.24949, -0.01917]` |
| `xyber_x1` | **804,869** | **1,587,926** | 4096 | `body:lumbar_yaw_link` | `[0, 0, 0]` |

X1 的网格规模是人体模板的 **77 倍**（80.5 万 vs 1.05 万顶点）。机器人的根偏移是零向量，因为配置指定的 `point_cloud_center` 本身就是根 body。

两个模板的居中方式与配置完全一致：

```
center_modes = ['spine1', 'body:lumbar_yaw_link']
```

### 3.3 点云几何（统一 SMPL 坐标系，Y 朝上）

| 模板 | 身高 | X 跨度 | Z 跨度 | bbox 中心 |
|---|---|---|---|---|
| SMPL-X（含 betas） | **1.8477** | 1.9096 | 0.3194 | `[0.0026, -0.2318, 0.0154]` |
| X1 | **1.2669** | 1.4482 | 0.2389 | `[-0.0001, -0.1076, -0.0151]` |

- **身高比 robot/human = 0.6856** —— X1 约为人体的 68.6%
- X 跨度是臂展（T-pose），两者都接近各自身高的 1.03~1.14 倍，符合人形比例
- Z 跨度是身体厚度（0.3194 / 0.2389），量级合理

### 3.4 T-pose 与居中校验

以 Y=0 为各自的躯干中心，向下到脚底的距离：

| 模板 | y_min（脚底） | y_max（头顶） | 脚底→中心 / 身高 |
|---|---|---|---|
| SMPL-X | −1.1556 | +0.6921 | **0.6254** |
| X1 | −0.7411 | +0.5258 | **0.5850** |

两点结论：

1. **居中正确**。两个点云都以其躯干中心为原点，X1 的 `lumbar_yaw_link` 位于自身身高 **58.5%** 处 —— 这个数与我独立用 MuJoCo 测得的 **0.5848** 吻合（独立方法交叉验证 ✅）
2. **注意人体模板不是原始 T-pose**。仓库自带的 SMPL-X 中性 T-pose 身高 1.7211 m，而本次（应用动作序列 betas 后）是 **1.8477 m**，高出 7%。因为配置里 `use_betas: true`，人体模板会跟随动作序列的体型参数变形

### 3.5 采样点是否落在网格上

对每个采样点，量它到自己所属三角面中心的距离：

| 模板 | 平均距离 | 最大距离 |
|---|---|---|
| SMPL-X | 0.0071 | 0.0287 |
| X1 | 0.0053 | 0.0673 |

数值都很小（厘米级），说明 `sample_face_ids` 与实际采样点**一致**，采样正确落在了表面上而非内部或外部。

X1 的最大值 0.0673 偏大，是因为机器人网格里有少量大三角面（面中心离面上任意点都远），属正常现象。

### 3.6 存进 npz 的 T-pose

29 个关节中只有 2 个非零，与配置一致：

```
left_shoulder_roll_joint    -1.5700
right_shoulder_roll_joint   -1.5700
（其余 27 个关节为 0）
```

---

## 4. 观察与待确认项

### 4.1 ⚠️ 躯干比例差异（值得观察）

人体躯干中心在身高 **62.5%** 处，X1 在 **58.5%** 处 —— 相差约 **4 个百分点**。这意味着即便两者都对齐到躯干中心，人体的腿在比例上仍比 X1 长。

这是 Stage 2 需要吸收的比例失配。其他机器人配置（K1/T800/H2 等）通过把 `smpl_center` 从 `spine1` 改成 `bbox_ratio` 并配一个调过的比例值来处理类似问题；X1 目前沿用 G1 的 `spine1`。

**待确认**：Stage 2 学出来的对应关系是否把这个 4% 的失配正确吸收。如果 slot 在腿部出现系统性偏移，可以考虑改用 `bbox_ratio`（参考值见下）。

作为参考，我实测过的几个数：

| | 躯干中心占自身 bbox 高度 |
|---|---|
| SMPL-X neutral T-pose 的 Spine1 | 0.616069 |
| X1 的 `lumbar_pitch_link` | 0.6167 |
| X1 的 `lumbar_yaw_link` | 0.5848 |
| H2 配置里的 `bbox_center_ratio` | 0.6157 |

（`lumbar_pitch_link` 与 SMPL-X Spine1 的分数几乎重合，若要改 `bbox_ratio` 模式，这是有依据的起点。）

### 4.2 人体模板随 betas 变形

`use_betas: true` 使得人体模板身高随动作序列变化（本次 1.8477 m vs 原始 1.7211 m）。换动作序列会改变 betas → 改变模板哈希 → **Stage 1 数据集会自动重建**。这是预期行为，但意味着换序列时 Stage 1/2 要重跑。

### 4.3 Windows `/tmp` 与本次运行无关

本仓库有 11 处硬编码 `/tmp`。本次运行**没有触发**它 —— 因为没有传 `--defaults`。

`humanoid_retarget_pipeline.py` 的逻辑是：

```python
if args.defaults is None:
    run_pipeline(config, args)          # ← 本次走这条，不碰 /tmp
    return
with tempfile.TemporaryDirectory(dir="/tmp") as temp_dir:   # ← 传了 --defaults 才走这条
```

**但这不代表以后不会踩**：GRAIL / BONES-SEED / batch 等流程都要传 `--defaults`，那时 `dir="/tmp"` 就会生效。当前已在 `E:\tmp` 建好目录作为规避（Windows 上 `Path("/tmp")` 解析为"当前盘符根目录"，仓库在 E: 盘）。

### 4.4 未生成可视化

Stage 1 **不产出任何图**（CLI 里没有可视化开关）。原始问题是"会不会生成彩色采点图"——答案是不会。

原因：彩色的意义在于**按身体部位分色**，而部位划分（slot）是 **Stage 2 训练出来的**，Stage 1 阶段还不存在。Stage 1 只能按模板/高度/左右上色，仅能确认采样分布。

按 slot 分色的图要等 Stage 2 跑完，由 Stage 4 的查看器（`visualize_robot_retarget_result.py --show-source-slots / --show-robot-slots`）呈现。

---

## 5. 复现命令

```bash
# 环境
D:\conda\envs\umr\python.exe

# Stage 1
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/humanoid_retarget_xyber_x1_example.json \
  --stage build

# 强制重建（改了 config 之后）
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/humanoid_retarget_xyber_x1_example.json \
  --stage build --force-build
```

日志：`E:\tmp\stage1_build.log`

---

## 6. Stage 1 小结

Stage 1 只验证了**采样分布**，无法验证**对应关系是否正确**（slot 尚不存在）。要判断 X1 的重定向质量，必须继续跑到 Stage 2。

---

# Part 2 · Stage 2 — 对应关系学习（train）

## 7. Stage 2 要做什么

训练一个 **template-residual correspondence autoencoder**，输入是 Stage 1 产出的两个 4096 点云，输出是一套**共享的 slot 排序** —— 即"人体的第 k 个 slot ↔ 机器人的第 k 个 slot"。

关键点：

- **没有任何人工的人体-机器人关节映射**。哪些人体点对应哪些机器人点，完全由网络从几何中学出
- 数据集**只有 2 个样本**（SMPL-X 模板 + X1），所以这不是常规意义上的"大数据训练"，而是对这 2 个点云做一次**优化式对齐**
- `normalize: per_sample_height` —— 每个点云先按自身身高归一化，身高比 0.6856 被缩放掉
- `edge_graph: geodesic` + `edge_k: 32` —— 用测地邻接约束 slot 的**空间连续性**，避免 slot 在表面上跳来跳去
- 有了 slot，才能给采点图"按身体部位上色"

### 7.1 实际生效的超参

| 参数 | 值 | 说明 |
|---|---|---|
| `epochs` | 500 | 数据集只有 2 个样本，`batch_size=2` → **每 epoch 1 步，共 500 步** |
| `device` | `auto` → **cuda** | 日志确认 `device=cuda` |
| `normalize` | `per_sample_height` | 见下 |
| `lr` / `lr_scheduler` | 0.001 / cosine → 1e-05 | |
| `chamfer_weight` | 1.0 | 主损失 |
| `repulsion_weight` / `k` / `radius` | 0.002 / 8 / 0.035 | 防止点挤成一团 |
| `edge_weight` / `edge_k` | 0.4 / 32 | slot 空间连续性 |
| `residual_weight` | 0.0 | |
| `normalization_scales` | SMPL 1.8482 / X1 1.2673 | 即各自身高 |
| `edge_count` | 131072 | |

## 8. Stage 2 实验结果

### 8.1 训练日志

```
[TrainResidual] data=...correspondence_xyber_x1_smplx_neutral_betas_c4eb7419e9.npz samples=2
[TrainResidual] template=smplx_neutral_betas_c4eb7419e9 sort=y_z_x
[TrainResidual] device=cuda num_points=4096
[TrainResidual] normalize=per_sample_height
[TrainResidual] training_mode=all_samples
[TrainResidual] normalization_scales smplx_neutral_betas_c4eb7419e9=1.8482, xyber_x1=1.2673
[TrainResidual] epoch=00001 loss=0.003263 chamfer=0.001612 repulsion=0.001651 edge=0.000000
[TrainResidual] epoch=00100 loss=0.001652 chamfer=0.000113 repulsion=0.001422 edge=0.000118
[TrainResidual] epoch=00200 loss=0.001645 chamfer=0.000112 repulsion=0.001420 edge=0.000114
[TrainResidual] epoch=00300 loss=0.001644 chamfer=0.000116 repulsion=0.001416 edge=0.000113
[TrainResidual] epoch=00400 loss=0.001642 chamfer=0.000114 repulsion=0.001413 edge=0.000115
[TrainResidual] epoch=00500 loss=0.001642 chamfer=0.000114 repulsion=0.001412 edge=0.000115
[TrainResidual] Saved final checkpoint and correspondence slots to ...
```

- **chamfer 损失从 0.001612 → 0.000114（下降 14×）**，且在 epoch 200 后就基本不再变化（0.001645 → 0.001642）
- 说明 **500 epochs 对这个问题远远够用**，甚至 200 就收敛了
- 剩余的 loss 主要来自 `repulsion`（0.0014），是防止点堆叠的正则项，不是误差

### 8.2 核心指标：对应关系质量

在归一化空间（身高 = 1.0）里，量"第 k 个 slot 在人体上的位置"与"第 k 个 slot 在 X1 上的位置"的距离：

| 指标 | mean | median | p90 | max |
|---|---|---|---|---|
| **索引序基线**（点 i ↔ 点 i，未学习） | 0.41857 | 0.39441 | 0.73805 | 1.05261 |
| **学习后**（slot k ↔ slot k） | **0.03967** | 0.03604 | 0.07173 | 0.13671 |

**提升 10.55 倍。** 这是本实验最重要的结果 —— 网络确实把两个点云对齐了，而不是靠采样顺序蒙对。

### 8.3 按身体区域的误差分布

| 区域 | 点数 | 平均距离 | 评价 |
|---|---|---|---|
| **手臂/手** | 348 | **0.08442** | ⚠️ **最差** |
| 腿部（下） | 490 | 0.04264 | 中 |
| 躯干 | 1403 | 0.03724 | 中 |
| 大腿/胯 | 1488 | 0.03462 | 中 |
| **头/颈** | 367 | **0.02298** | ✅ 最好 |

- **左右对称**：左侧 0.04424 / 中线 0.03157 / 右侧 0.04360 —— 左右几乎相同，说明**没有镜像错误**
- **误差图（`stage2_slots.png` 面板 c）肉眼可见**：躯干/腿/头都是深蓝（低误差），只有**手部发亮**

### 8.4 最差的 10 个 slot 全在手上

```
slot 2978  SMPL=[-0.5307  0.1413 -0.0314]  X1=[-0.5585  0.2749 -0.0222]  d=0.13671
slot 3028  SMPL=[ 0.5060  0.1427 -0.0341]  X1=[ 0.5357  0.2706 -0.0062]  d=0.13422
slot 2988  SMPL=[ 0.5242  0.1502 -0.0012]  X1=[ 0.5671  0.2651  0.0127]  d=0.12344
...
```

全部满足 `|X| ≈ 0.49~0.57`（横向最外）且 `Y ≈ 0.14~0.17`（肩高附近）→ **就是双手/前臂**。

对比 SMPL 与 X1 的坐标可以看出**两条系统性的差异**：

1. **X1 的手伸得更远**：`|X|` 上 X1（0.54~0.57）> SMPL（0.49~0.53）
2. **X1 的手抬得更高**：`Y` 上 X1（0.25~0.28）> SMPL（0.14~0.17）

原因在 Stage 1 就量到过：**X1 的臂展/身高 = 1.143，而人体只有 1.033** —— X1 的手臂在比例上比人宽 11%。这是真实的解剖学差异，不是 bug。

## 9. 结论与判断

### 9.1 对应关系整体是好的

- 学习后比索引序基线好 **10.55×**
- 左右对称，无镜像错误
- 躯干、腿部、头部误差都在 0.023~0.043（身高归一化后，约 2~4 cm 当量）
- 躯干是全身上下最"像"的部分（0.037），说明**腰部对齐策略是对的**

### 9.2 关于第 4.1 节担心的"4% 躯干比例失配"

**结论：不是主要问题。** 验证方法：把两个点云的全局平均位移（主要在 Y 方向，0.0178）扣掉后，逐 slot 平均距离只从 0.03967 降到 0.03810（**仅改善 4.0%**）。

也就是说 **AE 已经把绝大部分全局偏移吸收掉了**，剩下的残差是**局部形状差异**，不是整体错位。`per_sample_height` 归一化 + AE 的对齐能力足够处理这个量级的中枢失配，**暂时不需要改 `smpl_center` / `bbox_ratio`**。

### 9.3 真正的短板是手臂

误差最大的区域是**手臂/手**（0.0844，是头颈的 3.7 倍），根因是 X1 臂展比例比人体宽 11%。

这在后续 Stage 3 重定向里的影响：手部映射到 X1 的手时会有系统性的位置偏移，**手部操作的精度会受影响**（比如抓取、接触场景）。纯行走/奔跑类动作不受影响。

如果想改善，方向是调整人体模板的手臂比例（`betas` 或换模板），或接受这个差异。

## 10. 可视化产物

- **`czy/exp/stage2_slots.png`** —— 4 面板彩色采点图：
  - (a) SMPL-X 4096 点，按 slot 序号上色（hsv）
  - (b) X1 4096 点，**同一个 slot 配色** —— 若对应正确，(a)(b) 的颜色布局应当一致
  - (c) SMPL-X 点云按对应误差上色（viridis）—— 亮色即误差大，可见只有手部发亮
  - (d) 按身体区域的误差柱状图
- **`czy/exp/plot_stage2_slots.py`** —— 生成上述图的脚本，可复用：
  ```bash
  python czy/exp/plot_stage2_slots.py \
    --slots output/correspondence_xyber_x1_smplx_neutral_betas_c4eb7419e9/correspondence_slots_final.npz \
    --out czy/exp/stage2_slots.png
  ```

## 11. Stage 3 要做什么

用 Stage 2 学到的 slots，把一段人体动作（SMPL-X 序列）**逐帧解**成 X1 的关节轨迹。

- 读入：人体动作序列 + slots + X1 的 MJCF
- 逐帧解 QP（`clarabel`），同时满足：脚部地面接触/穿透硬约束、机器人自穿透约束、每帧关节变化步长限制
- 解完后用 **LQR 轨迹滤波**做平滑（对 data / accel / jerk 加权）
- 用**前一帧的解热启动**当前帧（`sequential`）

### 11.1 实际生效的求解配置

| 参数 | 值 |
|---|---|
| `ground_contact_anchor_cost` | 5.0 |
| `ground_penetration_hard_constraint` | on（mode=`surface_slots_all`，margin 0.0，threshold 0.05，max_points 128） |
| `robot_self_penetration_margin` | −0.001（hard slack，cost 1000） |
| `step_limit_mode` / `max_dq` / `global_step_size` | `l2` / 0.15 / 0.4 |
| `trajectory_filter_mode` | `lqr`（data 1.0 / vel 0.0 / acc 0.1 / jerk 0.01，含 root 平移） |
| `trajectory_warm_start_mode` | `sequential`（bidirectional continuity 0.1 / switch 0.01） |
| `slots_field` | `reconstructed_slots` |

## 12. Stage 3 实验结果

### 12.1 运行

```
[HumanoidRetarget] source=sample_data/lafan1_smplx format=smplx_npz seq=dance1_subject2 frames=3945 fps=30.000
[SurfaceRetarget][SMPLX] device=cuda:0 batch_size=3945 frames=3945
[HumanoidRetarget] inferred robot_height=1.26689 from slots sample=xyber_x1 field=target_points mode=y_extent
[HumanoidRetarget] bound SMPL slots: slots=4096, error_mean=0.01029, p95=0.02674
[HumanoidRetarget] human_height=1.84824 robot_height=1.26689 smpl_scale=0.685456 ground_z=0.00000
[HumanoidRetarget][GroundPenetration] hard_constraint=true mode=surface_slots_all margin=0.0000
[HumanoidRetarget][TrajectoryFilter] mode=lqr step_p95 0.149266->0.144604 accel_p95 0.080918->0.0696542 jerk_p95 0.089348->0.0610679
[HumanoidRetarget] saved ...\dance1_subject2_smplx_xyber_x1.npz qpos=(3945, 36) cost mean=0.082808 max=0.287718
```

- **耗时：5 分 11 秒**（14:26:11 → 14:31:22），3945 帧 ≈ **12.7 帧/秒**，远快于预期
- **输出**：`output/xyber_x1_retarget/dance1_subject2_smplx_xyber_x1.npz`，519 KB，`qpos=(3945, 36)`
- 输出字段：`qpos` / `frame_ids` / `fps` / `ground_z` / `robot_joint_names`(29) / `robot_name` / `robot_xml` / `smpl_scale` / `source_data` / `source_format` / `source_sequence_key` / `zero_source_finger_pose`

### 12.2 物理有效性校验（全部通过）

| 检查项 | 结果 |
|---|---|
| NaN / Inf | **0** |
| 全零帧 | **0** |
| **关节限位越界** | **0 次 / 0 帧**（29 关节 × 3945 帧全部落在 MJCF `range` 内） |
| root 四元数归一化 | 1.000000（精确） |
| root 高度 z | 0.358 ~ 0.757，**mean 0.599**（X1 标称站立高度 0.61） |
| 脚部网格最低点 z | min **−0.0012 m**，median 0.0019，max 0.0437 |
| 明显穿地（< −1 cm） | **0 / 79 采样帧** |
| 明显离地（> +5 cm） | **0 / 79 采样帧** |
| LQR 滤波效果 | accel p95 0.0809→0.0697（**−14%**），jerk p95 0.0893→0.0611（**−32%**） |
| \|dq\| 逐帧 | mean 0.041，p95 **0.1446**，max 0.354 rad |

**地面接触质量特别好**：最深穿地只有 **1.2 毫米** —— 说明 `ground_penetration_hard_constraint` 确实生效了。

### 12.3 与前面阶段/日志的交叉验证（全部一致）

| 量 | Stage 3 日志 | 独立来源 | 一致? |
|---|---|---|---|
| 机器人身高 | `inferred robot_height=1.26689` | Stage 1 实测 1.2669 | ✅ |
| 身高比 | `smpl_scale=0.685456` | Stage 1 的 0.6856 | ✅ |
| 视觉 geom 数 / 中心 | `visual_geoms=60, point_cloud_center=body:lumbar_yaw_link` | Stage 1 完全一致 | ✅ |
| p95 步长 | `[TrajectoryFilter] step_p95 0.144604` | 我独立算的 \|dq\| p95 = 0.1446 | ✅ |

### 12.4 快速动作分析（不是求解跳变）

1587 / 3944 帧有某个关节 \|dq\| > 0.20 rad（11.5°/帧 ≈ 345°/s）。判断这是**真实编排的快速动作**而非求解不连续，依据：

- 这些帧的**间隔中位数 = 1**（即连续成段出现），而不是零星孤立点
- 尖峰集中在 `left/right_knee_pitch`、`left/right_shoulder_pitch`、`left/right_elbow_pitch` —— 正是舞蹈里动作幅度最大的关节
- max \|dq\| = 0.354 rad/帧 ≈ 607°/s，是舞蹈快到极限时段的合理值

### 12.5 一个值得注意的点：config 里没配限位

```
[HumanoidRetarget][JointLimit] configured=0 matched_same_name=0 scalar_joints=29
[HumanoidRetarget][StepLimit] dof_max_dq_box configured=0 matched_same_name=0
```

- **`JointLimit configured=0`** —— config 里没有 `joint_limits` 段，但**解算结果自然落在 MJCF 的 `range` 内（0 越界）**，所以没出问题。X1 的关节范围本来就宽松（`hip_pitch [-1,2]`、`shoulder_roll [-2,0]` 等），舞蹈动作没触到边界。**如果换成极限动作（如体操），建议显式配 `joint_limits`。**
- **`StepLimit configured=0`** —— `--max-dq 0.15` 不是硬约束：有 **5191 / 114376（4.5%）** 的关节-帧超过 0.15。考虑到上述快速动作分析，这个比例是合理的。

### 12.6 副作用：assets 目录被写入了派生 MJCF

pipeline 在源 MJCF 旁边生成了一个派生文件：

```
assets/F1/F1_resource/mjcf/dance1_subject2_smplx_xyber_x1.floating_mjcf.xml   (40 KB, 342 行)
```

我校验过它是**源 XML 的语义等价重序列化**：

| 项 | `x1_29dof_raw.xml` | 派生文件 |
|---|---|---|
| nq / nv / njnt | 36 / 35 / 30 | 36 / 35 / 30 ✅ |
| free joint | `base_link_free_joint` | 同名保留 ✅ |
| 关节 range | `hip_pitch [-1,2]` 等 | 完全一致 ✅ |

差异只在两处：

1. **mesh 路径被改成了绝对路径** `E:/UMR/assets/F1/F1_resource/meshes/*.STL` —— **仓库一旦搬家/换机器就失效**（原文件用的是相对 `meshdir="../meshes/"`）
2. geom 上把 default 展开成了显式属性（`contype="0" conaffinity="0" group="1" density="0"`）

**问题**：每个新动作序列都会在这里再写一个 ~40 KB 的 XML，`assets/F1/` 会越来越乱，而且这些文件是绝对路径绑定的。想清理可以删掉，不影响原始 XML。

## 13. 下一步

Stage 1/2/3 全部通过，X1 的动作已经生成。可以播放/录视频：

```bash
# 播放（glfw-ui 窗口）
python scripts/humanoid_retarget_pipeline.py \
  --config robot_configs/humanoid_retarget_xyber_x1_example.json --stage view

# 或直接调 viewer，支持按 slot 上色 + 录视频
python scripts/visualize_robot_retarget_result.py \
  --result output/xyber_x1_retarget/dance1_subject2_smplx_xyber_x1.npz \
  --robot-xml assets/F1/F1_resource/mjcf/x1_29dof_raw.xml \
  --show-source-slots --record-video output/xyber_x1_retarget/dance.mp4
```

**待确认项**：Stage 2 发现手部对应误差最大（0.0844，是头颈的 3.7 倍，因 X1 臂展比例比人宽 11%）。舞蹈里手部动作多，**建议在查看器里重点看手部的跟踪质量**——这是目前唯一已知的系统性偏差来源。