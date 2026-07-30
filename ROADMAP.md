# Combat Knowledge Base Roadmap

本路线图自 v1.5.2 起作为 CKB 的正式版本规划。版本号只表示计划边界；任何版本均须以仓库实际代码、数据、测试和 CI 结果为准。

## 当前基线：v2.0.0

v2.0.0 已完成首个稳定版门槛：核心 Schema/谓词与主要实体类型冻结，装甲车辆与轻武器等装备领域形成可消费闭环，网站/查询、Godot Bundle/Lock/SDK、发布快照和迁移兼容规则均有自动化验收。

v1.6.1 已完成轻武器与弹药的 Batch 08–11：M2 Browning、12.7 x 99 mm、Magazine 组件边界、Variant/Family 关系闭环，以及独立轻武器 Godot Runtime profile。正式发布快照以远程 CI 和 Godot 4.7.1 Linux Smoke 结果为准。

当前基础架构和首个规模化内容领域已经覆盖：

- Canonical Entity 与独立 Relationship Assertion；
- Predicate Registry 与关系端点语义约束；
- KnowledgeGraph 的邻居、反向、对称、传递和路径查询；
- Relationship Assertion 到 Canonical Fact 的归并；
- 来源去重、冲突检测和审核晋级建议；
- Canonical Fact 生命周期与人工裁决历史；
- 可重复验证的事实发布快照；
- 79 个 Canonical Entity 和 57 个已入批 GroundVehicle；
- 44 条独立关系断言，实体内嵌关系为 0；
- 8 个结构化装甲车辆技术档案、71 条技术声明和 5 条派生指标；
- 技术参数统一单位标准化和多配置隔离；
- 面向 Godot 的紧凑 Bundle、Lock 文件和 GDScript 加载器；
- Godot 4.7.1 Linux 实际运行、配置查询和截图验证；
- Markdown、SQLite、JSON、网站和 Godot Bundle 输出；
- 自动测试、数据校验和 GitHub Actions 门禁。

v1.6.0 完成了装甲车辆主体库的首个可消费闭环，但不代表全部装甲车辆都已经完成来源审核和技术档案，也不代表完整 Godot 插件、缓存与游戏平衡层已经完成。当前活跃阶段转入 v1.6.1。

## v1.5.3：事实生命周期收尾（已完成）

已完成范围：

- 为 Canonical Fact 增加 `proposed`、`accepted`、`disputed`、`rejected`、`deprecated` 生命周期状态；
- 保存人工裁决人、裁决时间、理由和引用的 assertion ID；
- 保存事实状态变更历史，不覆盖旧裁决记录；
- 支持冲突解决记录，并区分自动检测结果与人工正式裁决；
- 冲突事实必须先进入 `disputed`，解决时必须引用多方断言；
- 生成内容稳定、可重复验证的 SHA-256 事实发布快照；
- 增加对应 Schema、CLI、测试和 CI 门禁；
- `suggested_review_status` 与 `suggested_lifecycle_status` 均不得自动修改正式状态。

完成标准已经落实为自动测试与 CI 门禁：

- 同一输入数据和裁决文件生成相同快照标识；
- 非法状态迁移、缺失裁决依据和未知 assertion 引用被校验拒绝；
- 冲突事实保留全部原始证据和完整裁决历史；
- `validate`、`assertion-audit`、`fact-snapshot`、`graph` 和 `stats` 均纳入 CI。

## v1.6：知识内容规模化（当前系列）

### v1.6.0 装甲车辆主体库（已完成）

完成范围：

- 覆盖苏联/俄罗斯、德国、美国、英国、法国、中国、日本等主要发展线；
- 建立稳定的型号、家族、发展谱系与变体关系；
- 将旧式实体内嵌关系全部迁移到独立 Relationship Assertion；
- 建立内容批次、审核队列和质量统计；
- 完成 29 个实体和 17 条关系的多来源审核；
- 为 8 个代表性车辆建立结构化技术与体验档案；
- 将 71 条技术声明转换为可比较的标准化层，其中 55 条数值声明全部成功标准化；
- 以显式输入 claim 和配置限定生成 5 条功重比派生指标；
- 为《destory》生成包含 8 个实体和 18 个配置的紧凑 Godot 运行时 Bundle；
- 在官方 Godot 4.7.1 Linux x86_64 引擎中完成真实加载与查询验证。

v1.6.0 的发布数字是历史快照，不应替代后续版本的实时 `stats` 与内容审计结果。

### v1.6.1 轻武器与弹药（当前阶段）

建立武器、弹药、口径、平台适配和发展关系。

优先目标：

- 明确 Weapon、Ammunition、Cartridge、Magazine 与 Platform 的实体边界；
- 固化 `uses_ammunition`、`compatible_with`、`variant_of` 等关系的端点约束；
- 迁移已有 AKM 等种子数据到正式内容批次；
- 建立首批可追溯技术声明和 Godot 运行时样板；
- 避免把现实弹道资料直接转写为伤害、穿透或游戏平衡值。

### v1.6.2 航空装备

建立飞机、发动机、航空武器、雷达和主要改型关系。

### v1.6.3 舰艇与海军武器

建立舰级、舰艇、动力、舰载武器、传感器和服役关系。

### v1.6.4 火炮、导弹、防空与传感器

建立系统组成、弹药/导弹、平台、传感器和任务关系。

v1.6 核心指标：

- Canonical Entity 数量；
- Canonical Fact 数量；
- 独立来源覆盖率；
- 字段完整率；
- 人工审核率；
- 旧式内嵌关系迁移率；
- 标准化技术声明覆盖率；
- 可实际消费的 Godot 运行时实体与配置数量。

## v1.7：时间、地理、组织与战役

新增并规模化以下实体类型：

- Place；
- Country；
- Organization；
- Manufacturer；
- MilitaryUnit；
- Battle；
- Conflict；
- Person；
- Facility。

目标输出包括装备时间轴、战役装备关系、企业产业链、工厂地点和部队编制图谱。

## v1.8：检索、查询与可视化

- 网站增加关系面板和可展开图谱；
- 增加时间轴、地图、发展谱系、战役装备图和产业链图；
- 增加高级筛选、本地查询 API 和稳定查询契约；
- 支持从事实返回原始断言和来源证据。

## v1.9：Godot 数据消费层

v1.6.0 已提前完成首个锁定 Bundle、GDScript 加载器和 Linux 引擎冒烟测试，但 v1.9 的完整范围仍包括：

- 提供正式 Godot 插件或稳定 GDScript SDK；
- 固化 Bundle 兼容规则、资源导入、缓存和查询接口；
- 完成《destory》实际工程接入，而不只是独立烟雾测试项目；
- 在游戏场景中验证实体加载、关系查询和对象配置流程；
- 建立升级、回滚和兼容性测试。

## v2.0：首个稳定版本

稳定发布需同时满足：

- Schema、核心谓词和主要实体类型稳定；
- 至少一个装备领域完成规模化建设；
- 网站可浏览和查询图谱；
- Godot 能够实际消费 CKB Bundle；
- 发布快照可重现；
- 迁移与兼容规则明确；
- CI、数据校验和治理门禁完整。

## 长期原则

1. 原始断言、规范事实、体验派生值和游戏平衡值严格分层。
2. 所有实体和关系必须保留来源、审核状态、置信度和权利信息。
3. 自动建议只能进入人工审核队列，不得自动改变正式状态。
4. 现代装备只整理公开知识和游戏抽象，不收录制造、规避防御或现实攻击操作教程。
5. 架构服务于内容生产和实际应用，避免为抽象而抽象。
6. Changelog 中的数量不是运行时事实；发布前必须运行 `ckb stats`、`ckb validate` 和全部治理审计。
7. Godot 运行时数据必须使用显式配置，不得自动选择“默认”“最新”或“最佳”型号。

## 每个版本的发布门禁

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m ckb.cli validate
PYTHONPATH=src python -m ckb.cli catalog-audit
PYTHONPATH=src python -m ckb.cli source-audit
PYTHONPATH=src python -m ckb.cli predicate-audit
PYTHONPATH=src python -m ckb.cli assertion-audit --output /tmp/assertion-governance.json --fail-on-conflict
PYTHONPATH=src python -m ckb.cli fact-snapshot --output /tmp/ckb-fact-snapshot.json
PYTHONPATH=src python -m ckb.cli graph --output /tmp/ckb-graph.json
PYTHONPATH=src python -m ckb.cli stats
PYTHONPATH=src python -m ckb.content_audit --output /tmp/ckb-content-report.json
PYTHONPATH=src python -m ckb.technical --output /tmp/ckb-technical-comparison.json --fail-on-unsupported
PYTHONPATH=src python -m ckb.technical_metrics --output /tmp/ckb-derived-metrics.json --fail-on-error
PYTHONPATH=src python -m ckb.godot_bundle --output /tmp/ckb-godot --fail-on-error
PYTHONPATH=src python -m ckb.runtime_contract --bundle /tmp/ckb-godot/ckb_destory_runtime.json --lock /tmp/ckb-godot/ckb-lock.json --fail-on-error
```

对包含 Godot 加载器变更的版本，还必须通过真实 Linux Godot 冒烟测试。若任一门禁失败，应先修复当前基线，不得仅通过修改版本号进入下一版本。
