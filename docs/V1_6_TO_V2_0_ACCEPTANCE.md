# v1.6–v2.0 需求—证据验收矩阵

本文件是“是否按预定目标完成”的唯一汇总口径。通过标准不是版本号或文案，而是规划项同时具备规范数据/实现、自动测试、运行时证据和发布门禁。

## 验收矩阵

| 版本 | 批准范围 | 主要实现证据 | 自动验收 |
|---|---|---|---|
| v1.6.0 | 装甲车辆主体、技术标准化、多配置、Godot Runtime | `data/canonical/`、`data/curated/destory/build_profile.json`、`src/ckb/technical.py`、`src/ckb/godot_bundle.py` | 技术、派生指标、Bundle/Lock 与 Godot Smoke 测试 |
| v1.6.1 | 轻武器、弹药、弹匣、适配与家族关系 | `data/curated/destory/small_arms_build_profile.json`、v1.6.1 批次与关系数据 | 小武器内容、谓词端点、Runtime 契约与 Godot Smoke |
| v1.6.2 | 飞机、活塞/喷气发动机、航空武器/弹药、机载雷达、改型、多配置、Runtime | `data/canonical/v1_6_2/`、`data/relationships/v1_6_2_*.json`、`aviation_build_profile.json` | `tests/test_v1_6_full_domain_closure.py`、领域 Godot 4.7.1 矩阵 |
| v1.6.3 | 舰级/舰艇、动力、舰炮/弹药、导弹/鱼雷、雷达/声呐、服役、多配置、Runtime | `data/canonical/v1_6_3/`、`data/relationships/v1_6_3_*.json`、`naval_build_profile.json` | `tests/test_v1_6_full_domain_closure.py`、领域 Godot 4.7.1 矩阵 |
| v1.6.4 | 火炮/迫击炮与弹药、防空组件、导弹/发射平台、雷达/传感器平台、系统图、Runtime | `data/canonical/v1_6_4/`、`data/relationships/v1_6_4_*.json`、`integrated_systems_build_profile.json` | `tests/test_v1_6_full_domain_closure.py`、领域 Godot 4.7.1 矩阵 |
| v1.7 | 九类上下文实体；时间轴、战役装备、产业链、工厂地点、部队编制 | `v1_7_context_*.json`、`src/ckb/visualizations.py` | `tests/test_v1_7_scaled_acceptance.py`、`tests/test_visualizations.py` |
| v1.8 | 关系面板、可展开图谱、时间轴、地图、谱系、战役装备、产业链、高级筛选、本地 API、证据回溯 | `src/ckb/query.py`、`src/ckb/site.py`、`assets/` | `tests/test_v1_8_acceptance.py`、查询/站点测试、浏览器实测、`mkdocs build --strict` |
| v1.9 | 正式 Godot SDK/插件、兼容、导入、缓存、查询、真实工程、场景、升级/回滚 | CKB 两代游戏 profile；《destory》`addons/ckb`、`data/ckb`、对象绑定与测试场景 | `tests/test_destory_game_bundle.py`；《destory》Import、Integration 28/28、Smoke 34/34、SAM 7/7 |
| v2.0 | 稳定合同、可消费领域、网站查询、Godot 消费、可重现快照、迁移兼容、完整 CI | `data/releases/v2_0_0.json`、`docs/V2_0_MIGRATION.md`、`src/ckb/stability_gate.py` | 全量 unittest、全部审计、七 profile Bundle/Lock、Godot 4.7.1、本地稳定门禁、远程 CI |

## 冻结快照

- 187 个 Canonical Entity；
- 135 条独立 Relationship Assertion，实体内嵌关系为 0；
- 35 个正式内容批次；
- 152 个 `source_checked` 实体；
- 123 个结构化技术档案；
- 521 条技术声明，其中 96 条数值声明已标准化、425 条描述性声明保留原义、未知数值单位为 0；
- 七个锁定 Runtime profile。

精确 Runtime 数量和 SHA-256 见 `data/releases/v2_0_0.json`。`python -m ckb.stability_gate --fail-on-error` 会把实时结果与该快照逐字段比较。

## 完成口径

本矩阵的“完成”只覆盖 v1.6–v2.0 已批准的版本边界，不表示 502 条建设目录、全球全部武器装备或所有历史资料都已完成收录。

最终发布必须同时满足：

1. 本地全量测试与全部数据/治理/站点/Runtime 门禁通过；
2. 官方 Godot 4.7.1 真实运行通过；
3. 两个仓库的变更提交并合并到默认分支；
4. 默认分支远程 CI 全绿。

任一条件缺失，都只能称为“实现候选”，不能称为最终 100% 发布完成。
