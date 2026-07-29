# Combat Knowledge Base（CKB）

CKB 是面向《destory》及后续战争、破坏与工程模拟项目的统一战斗知识库。

它不重新撰写军事百科，而是把公开资料、官方文件、博物馆馆藏、专业专题站点和开源数据集统一映射为可追溯实体，并生成：

- 供人和 AI 阅读的 Markdown；
- 供检索和分析的 SQLite；
- 供数据交换的 JSON；
- 供 Godot 使用的项目裁剪包；
- 现代装备的“体验可感知”配置。

## 已批准基线

1. CKB 使用独立仓库，不并入 `destory`。
2. 当前阶段不把许可证审查作为阻塞项，但保留来源与权利字段，避免未来不可逆返工。
3. 不采用 30 个实体的最小闭环路线，分类、来源、历史装备、现代装备、体验模型和 Godot 接入并行推进。
4. 现代装备资料必须细化到玩家可感知的声音、视觉、冲击、操控、环境、传感器和故障征兆。
5. 事实、标准化结果、体验派生值、游戏平衡值严格分层。
6. 现代装备只整理公开知识和游戏抽象，不收录制造、规避防御或现实攻击操作教程。

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
python -m ckb.cli build --output exports --profile destory --allow-unverified
```

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

搜索结果默认缓存到 `data/cache/search/`，重复查询优先使用缓存。详细规则见 `docs/V1_3_1_MATCHING.md`。

## 目录

```text
schemas/                 数据 Schema
taxonomy/                统一分类、时代、作用和体验维度
sources/                 来源登记与采集策略
data/catalog/            全量建设目录
data/canonical/          已标准化实体
data/staging/            机器导入与待审核记录
data/cache/              外部搜索结果缓存
data/templates/          人工导入模板
data/curated/destory/    《destory》筛选配置
src/ckb/                 校验、解析与导出工具
docs/                    设计、标准和路线图
exports/                 自动生成结果
```

## 当前版本

`1.3.1`：加入外部结果匹配评分、自动接受阈值、人工审核队列、家族/型号范围判断、搜索缓存和解析决策文件。
