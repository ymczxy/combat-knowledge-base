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

## 快速开始

```bash
python -m ckb.cli validate
python -m ckb.cli stats
python -m ckb.cli catalog-audit
python -m ckb.cli source-audit
python -m ckb.cli build --output exports --profile destory --allow-unverified
```

无安装运行：

```bash
PYTHONPATH=src python -m ckb.cli validate
PYTHONPATH=src python -m ckb.cli build --output exports
```

## 目录

```text
schemas/                 数据 Schema
taxonomy/                统一分类、时代、作用和体验维度
sources/                 来源登记与采集策略
data/catalog/            全量建设目录
data/canonical/          已标准化实体
data/curated/destory/    《destory》筛选配置
src/ckb/                 校验与导出工具
docs/                    设计、标准和路线图
exports/                 自动生成结果
```

## 当前版本

`1.1.0`：在工程基线上加入 502 条目录审计、来源登记审计和《destory》项目裁剪 Bundle。
