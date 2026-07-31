# V1.8 交互查询与证据回溯

V1.8 的网站入口为 `explorer/index.md`。它加载本地生成的 `query-index.json`，所有筛选和关系展开都在浏览器本地执行。

高级筛选支持名称/别名/标签全文检索，以及实体类型、领域、类别、子类、时代、标签、审核状态、技术字段、最少来源数和是否具有技术档案的组合过滤。

关系图支持：

- `out`、`in`、`both` 三种方向；
- 按谓词过滤；
- 从任一实体逐层展开相邻实体；
- 对每条关系查看证据。

查询索引契约为 `ckb.local.query-index` v1.1。证据链固定为：

`Canonical Fact -> Relationship Assertions -> Source Records`

Python API 和 CLI 使用同一语义。CLI 示例：

```bash
PYTHONPATH=src python -m ckb.cli query \
  --class Manufacturer \
  --review-status source_checked \
  --technical-field industry \
  --minimum-sources 2 \
  --has-technical
```

按实体查询关系及证据：

```bash
PYTHONPATH=src python -m ckb.cli query \
  --entity-id ckb:system:air_defense:patriot \
  --predicate uses_sensor \
  --direction out \
  --evidence
```

按规范事实回溯全部断言与来源：

```bash
PYTHONPATH=src python -m ckb.cli query \
  --fact-id fact:component_sensor_patriot_an_mpq_65:sensor_used_by:system_air_defense_patriot
```

CI 会执行站点源生成、JavaScript 语法检查和 MkDocs `--strict` 成品构建。
