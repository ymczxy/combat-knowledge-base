# Combat Knowledge Base Roadmap

本路线图自 v1.5.2 起作为 CKB 的正式版本规划。版本号只表示计划边界；任何版本均须以仓库实际代码、数据、测试和 CI 结果为准。

## 当前基线：v1.5.2

当前基础架构已经覆盖：

- Canonical Entity 与独立 Relationship Assertion；
- Predicate Registry 与关系端点语义约束；
- KnowledgeGraph 的邻居、反向、对称、传递和路径查询；
- Relationship Assertion 到 Canonical Fact 的归并；
- 来源去重、冲突检测和审核晋级建议；
- Markdown、SQLite、JSON、网站和 Godot Bundle 输出基础；
- 自动测试、数据校验和 GitHub Actions 门禁。

v1.5.2 仍属于架构基线，不代表内容规模、来源审核、网站图谱展示或 Godot 实际接入已经完成。

## v1.5.3：事实生命周期收尾

目标：完成 Canonical Fact 的正式治理闭环，并停止继续扩展 v1.5.x 底层抽象。

计划范围：

- 为 Canonical Fact 增加明确生命周期状态：`proposed`、`accepted`、`disputed`、`rejected`、`deprecated`；
- 保存人工裁决人、裁决时间、理由和引用的 assertion ID；
- 保存事实状态变更历史，不覆盖旧裁决记录；
- 支持冲突解决记录，并区分自动检测结果与人工正式裁决；
- 生成内容稳定、可重复验证的事实发布快照；
- 增加对应 Schema、CLI、测试和 CI 门禁；
- 不让 `suggested_review_status` 自动修改正式审核或生命周期状态。

完成标准：

- 同一输入数据和裁决文件能够生成相同快照标识；
- 非法状态迁移、缺失裁决依据和未知 assertion 引用会被校验拒绝；
- 冲突事实能够保留全部证据并记录最终裁决；
- v1.5.3 发布后不再新增通用底层抽象，后续优先建设内容和应用。

## v1.6：知识内容规模化

### v1.6.0 装甲车辆主体库

覆盖苏联/俄罗斯、德国、美国、英国、法国、中国、日本等主要发展线。

核心工作：

- 建立稳定的型号、家族、发展谱系、生产与使用关系；
- 为关键实体补充至少一个可追溯来源，逐步提高独立来源覆盖率；
- 迁移旧式实体内嵌关系到独立 Relationship Assertion；
- 建立内容批次、审核队列和质量统计；
- 为《destory》选择首批可实际消费的装甲车辆数据。

### v1.6.1 轻武器与弹药

建立武器、弹药、口径、平台适配和发展关系。

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
- 旧式内嵌关系迁移率。

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

- 提供 Godot 插件或 GDScript SDK；
- 固化 Bundle 兼容规则、资源导入、缓存和查询接口；
- 完成《destory》实际接入示例；
- 在游戏中验证实体加载、关系查询和对象配置流程。

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

## 每个版本的发布门禁

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m ckb.cli validate
PYTHONPATH=src python -m ckb.cli catalog-audit
PYTHONPATH=src python -m ckb.cli source-audit
PYTHONPATH=src python -m ckb.cli predicate-audit
PYTHONPATH=src python -m ckb.cli assertion-audit --output /tmp/assertion-governance.json --fail-on-conflict
PYTHONPATH=src python -m ckb.cli graph --output /tmp/ckb-graph.json
PYTHONPATH=src python -m ckb.cli stats
```

若任一门禁失败，应先修复当前基线，不得仅通过修改版本号进入下一版本。
