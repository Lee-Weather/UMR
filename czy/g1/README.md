# Unitree G1 · 模型与对应关系

本目录提供 UMR 跑 G1 所需的**机器人模型**和**对应关系模型**。
重定向的轨迹数据不在这里，在 [umr_data/G1/](../../umr_data/G1)。

> 为什么需要这个目录：仓库自带的 `assets/g1/` 只有 6 个 MJCF/URDF，**133 个网格全是 LFS 指针**
> （`g1_29dof.xml` 引用的 36 个 mesh 一个实体都没有），MuJoCo 加载 5 个模型全部失败，
> 因此 `data/`、`output/`、`umr_data/` 里原本没有任何 G1 产物。这里用你提供的完整网格绕开了这个问题。

## 目录

| 路径 | 内容 | 说明 |
|---|---|---|
| `g1_29dof.xml` / `.urdf` / `main_mesh_collision_halfspherehand.urdf` | 原始模型 | 你的原始文件，未改动 |
| `meshes/`（69 STL + `half_sphere.obj`） | 原始网格 | 你的原始文件，未改动 |
| `scenes/scene_g1_29dof_wbt_plane.xml` | 带场景的入口 | 你的原始文件，未改动 |
| **`g1_29dof_umr.xml`** | **UMR 专用单文件模型（新建）** | 见下节 |
| **`umr_g1_config.json`** | **UMR 配置（新建）** | 指向上面这个 xml；含 `xml_policy.add_freejoint_root=false`，求解时不再生成派生 MJCF |
| `correspondence/` | 对应关系数据集 + 训练产物 | 95.0 MB |
| `batch_g1_walking_24.py` | 24 条纯行走（任务表从 F1 脚本导入，保证对齐） | 断点续跑 |
| `batch_g1_supplement.py` | 6 条代表 / 节律动作 | 断点续跑 |

## 为什么需要一个 `g1_29dof_umr.xml`

直接用现有两个 xml 都跑不通，踩了两个坑：

1. **`g1_29dof.xml` 单独加载失败**：`<pair geom2="floor" ...>`（14 条脚-地接触对）引用的
   `floor` geom 只存在于场景文件里 → `geom 'floor' not found in collision 0`。
2. **用 `scenes/scene_g1_29dof_wbt_plane.xml` 也失败**：UMR 会给没有自由关节的模型插入浮空根，
   但它的 `model_has_freejoint()` 只遍历 `root.iter("body")`、**不展开 `<include>`**，
   看不到 `g1_29dof.xml` 里已有的 `floating_base_joint`，于是又插了一个浮空根；
   同时 `absolutize_asset_paths()` 只处理顶层 `<asset><mesh>`，场景里没有 mesh，`meshdir` 被清掉
   → `Error opening file 'E:\UMR/czy/g1/pelvis.STL'`（第一次跑 6 条全挂就是这个）。

`g1_29dof_umr.xml` = `g1_29dof.xml` + 一行内联地板 geom（`name="floor"`、`group=2`），
没有 `<include>`、保留 `meshdir="./meshes/"`。校验：`nq=36 nv=35 njnt=30 nmesh=35 nu=29`，
`qpos0` 根高 0.793 m。

## 对应关系模型

```
correspondence/
├── correspondence_unitree_g1_smplx_neutral_betas_b80de5d138.npz   3.91 MB
└── trained/
    ├── correspondence_slots_final.npz                             0.87 MB
    └── checkpoint-final.pt                                       90.26 MB
```

| 项 | 值 |
|---|---|
| SMPL-X 模板 | `smplx_neutral_betas_b80de5d138`（betas 全 0，10,475 顶点） |
| 机器人网格 | `unitree_g1`（218,483 顶点 / 436,846 面） |
| 采样点 | 4096 点，`exterior_surface=true`、`first_hit` 遮挡剔除 |
| 点云中心 | `body:waist_yaw_link` |
| 训练 | 500 epoch，chamfer 收敛到 **0.000107** |
| 归一化高度 | SMPL-X 1.7211 m / G1 **1.3228 m** |

> 名字里的 `b80de5d138` 与仓库 `robot_configs/humanoid_retarget_unitree_g1_hiphi_shared_correspondence.json`
> 声明的完全一致，这份数据集可直接喂那套配置（指到本目录，或拷进 `data/` 与 `output/`）。

## 体积

| 部分 | 大小 |
|---|---|
| 模型（原始 + `g1_29dof_umr.xml`） | 63.7 MB |
| 对应关系（含 90 MB checkpoint） | 95.0 MB |

不便入库时可只保留 `correspondence/*.npz` + `correspondence/trained/correspondence_slots_final.npz`
（4.8 MB，足够继续做重定向），checkpoint 仅继续训练时才需要。

## 仓库原生 G1 路径

`assets/g1/`（LFS 指针那套）仍然不能用。若要启用它，需要
`git lfs pull --include="assets/g1/**"`（约 135 MB，本地 `.git/lfs` 缓存里已有）。
恢复后那套可以和本目录这套交叉验证。