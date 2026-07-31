# Combat Knowledge Base Roadmap

本路线图自 v1.5.2 起作为 CKB 的正式版本规划。版本号只表示计划边界；任何版本均须以仓库实际代码、数据、测试和 CI 结果为准。

## 当前基线：v2.0.0

v2.0.0 已按本路线图闭合 v1.6–v2.0 的规划边界。当前候选实现已通过本地数据、契约、单元测试和官方 Godot 4.7.1 真机验收；最终发布成立仍以默认分支远程 CKB CI 与 Godot Linux Runtime Smoke 全绿为准。

当前基线覆盖：

- Canonical Entity 与独立 Relationship Assertion；
- Predicate Registry 与关系端点语义约束；
- KnowledgeGraph 的邻居、反向、对称、传递和路径查询；
- Relationship Assertion 到 Canonical Fact 的归并；
- 来源去重、冲突检测和审核晋级建议；
- Canonical Fact 生命周期与人工裁决历史；
- 可重复验证的事实发布快照；
- 187 个 Canonical Entity、135 条独立关系断言和 35 个正式内容批次；
- 152 个 `source_checked` 实体，实体内嵌关系为 0；
- 123 个结构化技术档案和 521 条技术声明；
- 96 条数值声明全部完成单位标准化，425 条描述性声明保留原义，未知数值单位为 0；
- 技术参数统一单位标准化和多配置隔离；
- 七个面向 Godot 的锁定 Bundle/Lock profile；
- 正式 `.ckb` 导入插件、缓存、查询、升级和回滚链路；
- 官方 Godot 4.7.1 的领域矩阵与《destory》真实工程运行验证；
- 九类上下文实体以及全部五项 v1.7 规划图谱输出；
- v1.8 交互站点、高级查询和事实证据回溯；
- Markdown、SQLite、JSON、网站和 Godot Bundle 输出；
- 自动测试、数据校验和 GitHub Actions 门禁。

“规划边界完成”不等于全球装备百科全覆盖。502 条建设目录仍是长期候选池；未进入 `data/canonical` 的候选不能被计作已核实实体，游戏平衡值也不写回事实层。

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

## v1.6：知识内容规模化（已完成）

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

### v1.6.1 轻武器与弹药（已完成）

建立武器、弹药、口径、平台适配和发展关系。

完成范围：

- 明确 Weapon、Ammunition、Cartridge、Magazine 与 Platform 的实体边界；
- 固化 `uses_ammunition`、`compatible_with`、`variant_of` 等关系的端点约束；
- 迁移已有 AKM 等种子数据到正式内容批次；
- 建立可追溯技术声明和独立 Godot Runtime profile；
- 避免把现实弹道资料直接转写为伤害、穿透或游戏平衡值。

### v1.6.2 航空装备（已完成）

完成飞机、活塞/喷气发动机、航空武器与弹药、机载雷达、主要改型/家族关系、多配置隔离和独立航空 Runtime profile。

### v1.6.3 舰艇与海军武器（已完成）

完成舰级/舰艇、动力、舰炮与弹药、导弹/鱼雷、雷达/声呐、服役关系、多配置隔离和独立海军 Runtime profile。

### v1.6.4 火炮、导弹、防空与传感器（已完成）

完成火炮/迫击炮与弹药、防空组件、导弹/发射平台、雷达/传感器平台、多组件系统图和独立综合系统 Runtime profile。

v1.6 核心指标：

- Canonical Entity 数量；
- Canonical Fact 数量；
- 独立来源覆盖率；
- 字段完整率；
- 人工审核率；
- 旧式内嵌关系迁移率；
- 标准化技术声明覆盖率；
- 可实际消费的 Godot 运行时实体与配置数量。

## v1.7：时间、地理、组织与战役（已完成）

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

九类实体均具备通过严格验收的规范数据。已输出装备时间轴、战役装备关系、企业产业链、工厂地点和部队编制图谱，并扩展全量关系图、地图和发展谱系。

## v1.8：检索、查询与可视化（已完成）

- 网站增加关系面板和可展开图谱；
- 增加时间轴、地图、发展谱系、战役装备图和产业链图；
- 增加高级筛选、本地查询 API 和稳定查询契约；
- 支持从事实返回原始断言和来源证据。

以上项目均已实现并纳入站点/查询自动验收；交互浏览器已实际验证搜索、关系展开、递归图谱和证据链。

## v1.9：Godot 数据消费层（已完成）

完成范围：

- 提供正式 Godot 插件或稳定 GDScript SDK；
- 固化 Bundle 兼容规则、资源导入、缓存和查询接口；
- 完成《destory》实际工程接入，而不只是独立烟雾测试项目；
- 在游戏场景中验证实体加载、关系查询和对象配置流程；
- 建立升级、回滚和兼容性测试。

正式 `.ckb` EditorImportPlugin、`CKBService`、缓存与查询 API 已接入《destory》真实工程；游戏对象配置、关系查询、两代 Bundle 升级/回滚及现有 Smoke/SAM 场景均已在官方 Godot 4.7.1 中验证。

## v2.0：首个稳定版本（本地验收完成，待远程合并门禁）

稳定发布需同时满足：

- Schema、核心谓词和主要实体类型稳定；
- 至少一个装备领域完成规模化建设；
- 网站可浏览和查询图谱；
- Godot 能够实际消费 CKB Bundle；
- 发布快照可重现；
- 迁移与兼容规则明确；
- CI、数据校验和治理门禁完整。

逐条需求与可执行证据见 `docs/V1_6_TO_V2_0_ACCEPTANCE.md`。任何本地失败、远程 CI 失败或默认分支未合并，均不得对外宣称最终发布完成。

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
