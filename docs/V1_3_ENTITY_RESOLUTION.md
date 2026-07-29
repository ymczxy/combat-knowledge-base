# v1.3 实体解析与导入流程

## 目标

将 `data/catalog` 中的建设目录转化为具有稳定标识、可追踪来源和明确审核状态的实体候选，同时避免把同名不同物或家族与具体型号错误合并。

## 数据流

```text
CatalogItem
  → 名称标准化
  → 带目录命名空间的稳定 Candidate ID
  → 初步领域/时代分类
  → 同名歧义检测
  → Wikidata / MediaWiki / 人工 CSV 来源候选
  → 人工审核
  → Canonical Entity
```

## Candidate ID

候选 ID 不直接作为最终实体 ID，但在解析期间保持稳定：

```text
ckb:candidate:<catalog-group>:<normalized-name>
```

例如：

```text
ckb:candidate:wwii_armored_vehicles:t_34
ckb:candidate:contemporary_missiles_and_air_defense:javelin
```

将目录组加入 ID 是为了避免古代标枪 `Javelin` 与现代反坦克导弹 `Javelin` 在审核前发生碰撞。

## 审核状态

- `unresolved`：名称唯一，但尚未与外部实体和正式分类完成匹配；
- `ambiguous`：跨目录同名，或目录本身包含多种领域；
- `resolved`：已经完成实体身份确认，等待写入主数据；
- `canonical`：已进入 `data/canonical`，不再属于候选层。

## 命令

生成全部候选、歧义队列和清单：

```bash
PYTHONPATH=src python -m ckb.cli candidates --output exports/candidates
```

查看歧义报告：

```bash
PYTHONPATH=src python -m ckb.cli ambiguity-report
PYTHONPATH=src python -m ckb.cli ambiguity-report --json
```

导入人工 CSV：

```bash
PYTHONPATH=src python -m ckb.cli import-csv data/templates/entity_import_template.csv \
  --output data/staging/manual_import.json
```

## 外部来源适配器

`src/ckb/adapters.py` 提供两个不与业务逻辑耦合的适配器：

- `WikidataAdapter`：通过 `wbsearchentities` 发现 QID、标签、描述和别名；
- `MediaWikiAdapter`：通过 Wikipedia Search API 发现页面 ID、标题和摘要。

解析函数可使用保存的 API 响应离线测试；网络请求仅在显式调用 `search()` 时发生。

## 字段级来源原则

CSV 或 API 导入结果只能进入 staging，默认审核状态为 `machine_imported`。正式实体必须保留：

- 来源 ID；
- URL；
- 行号或外部实体 ID；
- 导入方式；
- 后续人工审核记录。

自动导入不得直接覆盖已经人工审核的 canonical 字段。
