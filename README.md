# Combat Knowledge Base（CKB）

CKB 是面向《destory》及后续战争、破坏与工程模拟项目的统一战斗知识库。

它不重新撰写军事百科，而是把公开资料、官方文件、博物馆馆藏、专业专题站点和开源数据集统一映射为可追溯实体与关系，并生成：

- 供人和 AI 阅读的 Markdown；
- 供检索和分析的 SQLite；
- 供数据交换的 JSON；
- 供 Godot 使用的项目裁剪包；
- 现代装备的“体验可感知”配置；
- 可进行语义校验、事实聚合、生命周期治理和路径查询的知识图谱 Bundle。

## 已批准基线

1. CKB 使用独立仓库，不并入 `destory`。
2. 当前阶段不把许可证审查作为阻塞项，但保留来源与权利字段，避免未来不可逆返工。
3. 不采用 30 个实体的最小闭环路线，分类、来源、历史装备、现代装备、体验模型和 Godot 接入并行推进。
4. 现代装备资料必须细化到玩家可感知的声音、视觉、冲击、操控、环境、传感器和故障征兆。
5. 事实、标准化结果、体验派生值、游戏平衡值严格分层。
6. 现代装备只整理公开知识和游戏抽象，不收录制造、规避防御或现实攻击操作教程。
7. Relationship 与 Entity 同为一等知识对象，关系必须具备稳定 ID、来源、审核状态和正式谓词语义。
8. 多条 Relationship 可以表达同一 Canonical Fact，但原始断言必须保留，不能因聚合而丢失证据链。
9. 系统建议不得自动修改正式审核状态或事实生命周期，所有正式裁决必须进入可追溯账本。

## 在线浏览

中文默认站：

`https://ymczxy.github.io/combat-knowledge-base/`

英文站：

`https://ymczxy.github.io/combat-knowledge-base/en/`

本地预览：

```bash
python -m pip install -e ".[docs]"
PYTHONPATH=src python -m ckb.cli site --output site_docs
mkdocs serve
```

网站提供全局搜索、规范实体详情、按领域/时代浏览、502 条建设目录和设计参考文档。

## 快速开始

```bash
python -m ckb.cli validate
python -m ckb.cli stats
python -m ckb.cli catalog-audit
python -m ckb.cli source-audit
python -m ckb.cli predicate-audit
python -m ckb.cli assertion-audit --output exports/graph/assertion-governance.json
python -m ckb.cli fact-snapshot --output exports/graph/fact-snapshot.json
python -m ckb.cli graph --output exports/graph/ckb-graph.json
python -m ckb.cli build --output exports --profile destory --allow-unverified
```

## v1.5 知识图谱与事实治理

独立关系位于：

```text
data/relationships/
```

正式谓词注册表位于：

```text
data/ontology/predicates.json
```

正式事实裁决账本位于：

```text
data/governance/fact_decisions.json
```

构建图谱：

```bash
PYTHONPATH=src python -m ckb.cli graph \
  --output exports/graph/ckb-graph.json
```

构建过程会校验：

- Relationship ID、端点、置信度和来源；
- 谓词是否注册；
- 反向、对称和传递语义是否自洽；
- 起点和终点实体类型是否符合 Predicate Registry；
- 图中是否存在悬空实体引用；
- Fact Decision 的状态迁移、裁决信息和断言引用是否合法。

图谱 Bundle 1.3 同时保存：

```text
Entity
Relationship Assertion
Canonical Fact
Predicate Registry
Fact lifecycle state
Fact decision history
```

同一事实的正向、反向、对称、嵌入式和独立 Relationship 会归并为一个 Canonical Fact，但全部原始断言和来源仍可回溯。

关系治理报告：

```bash
PYTHONPATH=src python -m ckb.cli assertion-audit \
  --output exports/graph/assertion-governance.json
```

它会输出重复断言组、独立来源、肯定/否定冲突、待人工确认的审核晋级建议、正式生命周期和裁决历史。系统只提出建议，不自动修改正式审核或生命周期状态。

生成可重复发布的事实快照：

```bash
PYTHONPATH=src python -m ckb.cli fact-snapshot \
  --output exports/graph/fact-snapshot.json
```

相同事实与裁决输入会生成相同 SHA-256 `snapshot_id`，用于发布复现、Bundle 追踪和变更判断。

相关规范：

- `docs/V1_5_1_PREDICATE_REGISTRY.md`：谓词注册表；
- `docs/V1_5_2_ASSERTION_GOVERNANCE.md`：断言与规范事实聚合；
- `docs/V1_5_3_FACT_LIFECYCLE.md`：事实生命周期、人工裁决与发布快照。

## v1.6 装甲车辆与 Godot 运行时

v1.6.0 完成了首个可消费装甲车辆闭环：

- 79 个规范实体，其中 57 个 GroundVehicle；
- 44 条独立 Relationship Assertion，实体内嵌关系为 0；
- 8 个结构化技术档案和 71 条技术声明；
- 55 条数值声明统一单位标准化，16 条描述性声明保留原义；
- 5 条显式绑定配置和输入 claim 的派生指标；
- 8 个实体、18 个配置的 Godot 紧凑运行时 Bundle；
- Bundle/Lock 哈希、版本、实体顺序和来源引用校验；
- 官方 Godot 4.7.1 Linux x86_64 实际运行验证。

生成标准化技术比较和派生指标：

```bash
PYTHONPATH=src python -m ckb.technical \
  --output exports/technical-comparison.json \
  --fail-on-unsupported

PYTHONPATH=src python -m ckb.technical_metrics \
  --output exports/derived-metrics.json \
  --fail-on-error
```

生成 Godot 运行时 Bundle 与 Lock：

```bash
PYTHONPATH=src python -m ckb.godot_bundle \
  --profile data/curated/destory/build_profile.json \
  --output exports/godot \
  --fail-on-error

PYTHONPATH=src python -m ckb.runtime_contract \
  --bundle exports/godot/ckb_destory_runtime.json \
  --lock exports/godot/ckb-lock.json \
  --fail-on-error
```

Godot 加载器位于 `examples/godot/CKBRuntimeBundle.gd`。加载器不会自动选择“默认”“最新”或“最佳”配置，调用方必须显式传入 `configuration_id`。

相关规范：

- `docs/DATA_STANDARD.md`：技术声明和标准化边界；
- `docs/GODOT_INTEGRATION.md`：Bundle、Lock 和 Godot 加载方式；
- `docs/V1_6_0_RELEASE.md`：v1.6.0 发布快照与验证范围。

## v1.3 候选实体解析

将 502 条建设目录生成稳定 Candidate ID、初步分类、歧义队列和清单：

```bash
PYTHONPATH=src python -m ckb.cli candidates --output exports/candidates
PYTHONPATH=src python -m ckb.cli drafts --output data/staging/catalog_drafts
```

查看同名和混合目录歧义：

```bash
PYTHONPATH=src python -m ckb.cli ambiguity-report
PYTHONPATH=src python -m ckb.cli ambiguity-report --json
```

从人工 CSV 导入 staging：

```bash
PYTHONPATH=src python -m ckb.cli import-csv data/templates/entity_import_template.csv \
  --output data/staging/manual_import.json
```

详细流程见 `docs/V1_3_ENTITY_RESOLUTION.md`。

## v1.3.1 外部实体匹配

使用离线样本验证匹配评分和决策：

```bash
PYTHONPATH=src python -m ckb.cli resolve-fixture \
  tests/fixtures/t34_resolution.json \
  --output exports/resolution
```

联网查询并解析单个候选：

```bash
PYTHONPATH=src python -m ckb.cli resolve-one "T-34" \
  --group wwii_armored_vehicles \
  --source wikidata \
  --language en \
  --output exports/resolution/t34
```

结果分为：

- `auto_accept`：身份匹配置信度高，但仍不代表技术参数已经核实；
- `human_review`：必须人工确认；
- `reject`：相关性不足。

歧义候选的最佳外部命中始终进入 `human_review`，不会因为歧义惩罚被直接丢弃；其余低质量命中仍可判定为 `reject`。

搜索结果默认缓存到 `data/cache/search/`，重复查询优先使用缓存。详细规则见 `docs/V1_3_1_MATCHING.md`。

## 目录

```text
schemas/                 数据 Schema
taxonomy/                统一分类、时代、作用和体验维度
sources/                 来源登记与采集策略
data/catalog/            全量建设目录
data/canonical/          已标准化实体
data/relationships/      独立关系断言
data/ontology/           谓词注册表和本体资源
data/governance/         事实裁决账本与治理数据
data/staging/            机器导入与待审核记录
data/cache/              外部搜索结果缓存
data/templates/          人工导入模板
data/curated/destory/    《destory》筛选配置
src/ckb/                 校验、解析与导出工具
docs/                    设计、标准和路线图
exports/                 自动生成结果
```

## 当前版本

`2.0.0`：完成跨装备领域知识实体、独立关系断言、时间/地点/组织/战役上下文、查询接口、Godot Bundle/Lock/SDK 消费链路，并通过稳定版发布门禁。
