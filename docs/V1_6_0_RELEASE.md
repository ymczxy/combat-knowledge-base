# CKB v1.6.0 发布说明

发布日期：2026-07-30

## 发布定位

v1.6.0 是 CKB 第一个完成“内容规模化 → 技术参数标准化 → 可追溯派生 → Godot 运行时交付 → 真实引擎验证”闭环的版本。

它证明装甲车辆公开资料可以被整理为统一、可审核、可重建、可由游戏直接读取的数据产品，而不是一组松散文档。

## 内容快照

发布时的历史快照：

| 指标 | 数量 |
|---|---:|
| Canonical Entity | 79 |
| GroundVehicle | 57 |
| 独立 Relationship Assertion | 44 |
| 实体内嵌关系 | 0 |
| 正式内容批次 | 11 |
| 未入批 GroundVehicle | 0 |
| `source_checked` 实体 | 29 |
| `source_checked` 关系 | 17 |
| 技术档案实体 | 8 |
| 技术声明 | 71 |
| 标准化数值声明 | 55 |
| 描述性声明 | 16 |
| 不支持的数值单位 | 0 |
| 派生指标 | 5 |

这些数字是 v1.6.0 的历史发布记录。后续版本的当前状态必须通过 `ckb stats`、内容审计和 CI 重新计算。

## 首批技术档案

v1.6.0 为以下代表性装甲车辆建立了结构化技术档案：

- M1 Abrams；
- Challenger 2；
- Leclerc；
- Type 10；
- M4 Sherman；
- T-34 Model 1940；
- Panther；
- Type 59。

每条声明保留字段、原始值、原始单位、配置限定和来源。标准化层不会覆盖 Canonical 数据，也不会把多个改型压成单一平均值。

## 派生指标边界

当前 5 条功重比指标来自显式指定的输入 claim，包含公式、输入 claim 引用、配置限定和来源指针。

所有派生指标均满足：

```text
not_source_fact = true
not_game_balance = true
```

它们不是加速度、越野能力、战斗效能或游戏性能评分。

## Godot 运行时交付

运行时生成命令：

```bash
PYTHONPATH=src python -m ckb.godot_bundle \
  --profile data/curated/destory/build_profile.json \
  --output exports/godot \
  --fail-on-error
```

输出：

```text
exports/godot/ckb_destory_runtime.json
exports/godot/ckb-lock.json
```

发布时运行时快照：

| 指标 | 数量 |
|---|---:|
| 实体 | 8 |
| 显式配置 | 18 |
| 技术声明 | 71 |
| 派生指标 | 5 |
| 去重来源引用 | 14 |

Payload SHA-256：

```text
000ed0e4fae78d66812dd662458224cc21801429307484eec74210ee723325df
```

Bundle 文件 SHA-256：

```text
7cdcd143fe08b3764701aa36084a0e7012b344bc1d79f6d1e6aad945cfcea307
```

## 真实 Godot 验证

v1.6.0 使用官方 Godot 4.7.1 Linux x86_64 二进制，在 Ubuntu 24.04 GitHub Actions 运行器中启动真实图形场景。

验证内容包括：

- Bundle 文件 SHA-256；
- Lock、格式和 Schema 版本；
- 资源清单和实体顺序；
- 8 个实体和 18 个配置的索引；
- Challenger 2 基础与附加装甲配置；
- M4A2E8 与 M4A4 Sherman VC Firefly 配置；
- 派生指标查询；
- 来源引用解析；
- Godot 视口生成 1280×720 PNG 截图。

最终结果：

```text
CKB_GODOT_SMOKE_RESULT=PASS
```

真实引擎运行发现并修复了静态检查未发现的 GDScript 首次编译问题：加载器不能在自身脚本编译期间依赖尚未注册的全局 `class_name` 来标注返回类型或构造自身实例。

## 发布边界

v1.6.0 不表示以下工作已经完成：

- 全部 79 个实体都完成独立来源审核；
- 全部 57 个 GroundVehicle 都具备技术档案；
- 游戏平衡数据已经建立；
- 完整 Godot 插件、缓存、升级和回滚机制已经完成；
- 数据已经接入真正的《destory》主工程。

本版本完成的是首个可重复、可验证、可由 Godot 真实读取的装甲车辆数据闭环。

## 下一阶段

v1.6.1 转入轻武器与弹药，重点建立 Weapon、Ammunition、Cartridge、Magazine 和 Platform 的稳定边界、关系约束、首批技术声明与运行时样板。
