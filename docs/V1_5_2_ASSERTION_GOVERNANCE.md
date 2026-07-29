# v1.5.2 Relationship Assertion Governance

## 1. 三层结构

CKB 将图谱知识拆分为三层：

1. `Relationship`：某个数据记录对关系事实作出的独立断言；
2. `CanonicalFact`：把语义等价的正向、反向、嵌入式和独立断言归并后的事实；
3. `PredicateDefinition`：解释事实所使用谓词的方向、反向关系和类型约束。

Relationship 不会因为聚合而删除。事实层只负责统一导航、证据汇总和治理状态，不覆盖原始断言。

## 2. 事实规范化

以下两条断言属于同一事实：

```text
A --development_line_predecessor--> B
B --development_line_successor--> A
```

对称谓词也会按端点稳定排序，因此：

```text
A --contemporary--> B
B --contemporary--> A
```

只生成一个 Canonical Fact。

每个事实拥有稳定 `fact:` ID，并保留全部 `assertion_ids`。

## 3. 重复与证据合并

相同事实的多条断言不会在图谱输出中被误计为多个事实。治理报告会分别给出：

- assertion 数量；
- fact 数量；
- 重复断言组数量；
- 每个事实的独立来源数量。

来源按 `source_id + url` 去重。相同来源被多个嵌入或独立记录重复引用时，只计作一个证据来源。

## 4. 冲突检测

Relationship 可以使用：

```json
{"qualifiers": {"polarity": "affirmed"}}
```

或：

```json
{"qualifiers": {"polarity": "denied"}}
```

同一 Canonical Fact 同时出现肯定和否定断言时，事实被标记为 `conflict: true`。冲突事实不会获得自动晋级建议。

## 5. 审核状态与晋级建议

事实层同时输出：

- `asserted_review_status`：现有断言中最高的正式审核状态；
- `suggested_review_status`：根据独立来源数量生成的待人工确认建议。

建议规则：

- 至少一个可识别来源：可建议 `source_checked`；
- 至少两个独立来源：可建议 `cross_checked`；
- 存在冲突：不建议晋级；
- 系统永远不直接修改原断言的审核状态。

来源数量只是审核工作流触发条件，不等同于事实已经正确。

## 6. CLI

生成治理报告：

```bash
PYTHONPATH=src python -m ckb.cli assertion-audit \
  --output exports/graph/assertion-governance.json
```

CI 或发布门禁需要在存在冲突时失败：

```bash
PYTHONPATH=src python -m ckb.cli assertion-audit --fail-on-conflict
```

排除旧式实体内嵌关系：

```bash
PYTHONPATH=src python -m ckb.cli assertion-audit --exclude-embedded
```

## 7. Graph Bundle 1.2

图谱 Bundle 现在同时包含：

- 原始实体；
- 原始 Relationship 断言；
- 聚合后的 Canonical Fact；
- Predicate Registry；
- assertion、fact、重复组和冲突统计。

应用层默认应使用 `facts` 进行导航和统计；需要审计证据时，再回溯 `assertion_ids` 和原始 `relationships`。
