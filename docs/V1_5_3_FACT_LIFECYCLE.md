# v1.5.3 Canonical Fact Lifecycle

## 1. 目标

v1.5.2 已经能够把语义等价的 Relationship Assertion 聚合为 Canonical Fact，但当时事实只有自动计算出的审核建议，没有正式、可追溯的人工裁决生命周期。

v1.5.3 增加独立的 Fact Decision Ledger，使以下信息成为版本化数据：

- 事实当前处于什么正式状态；
- 谁作出了裁决；
- 裁决发生在什么时间；
- 裁决理由是什么；
- 裁决引用了哪些原始 Relationship Assertion；
- 一个事实经历过哪些历史状态。

自动检测和人工裁决仍严格分离。`suggested_review_status` 与 `suggested_lifecycle_status` 只表示系统建议，不会修改正式状态。

## 2. 生命周期状态

Canonical Fact 支持五种正式状态：

| 状态 | 含义 |
|---|---|
| `proposed` | 根据当前断言聚合出的候选事实，尚未正式裁决。 |
| `accepted` | 已由人工确认，可进入正式发布内容。 |
| `disputed` | 存在来源冲突、解释分歧或证据不足，需要继续审查。 |
| `rejected` | 经审查不应作为正式事实发布，但证据和裁决历史仍保留。 |
| `deprecated` | 曾经有效或已发布，后来因新证据、模型迁移或语义替换而停用。 |

允许的状态迁移为：

```text
proposed   -> accepted | disputed | rejected
accepted   -> disputed | deprecated
disputed   -> accepted | rejected | deprecated
rejected   -> proposed | deprecated
deprecated -> proposed
```

不允许通过覆盖字段跳过历史。每一次变化都必须新增一条 Decision。

## 3. 裁决账本

默认账本位于：

```text
data/governance/fact_decisions.json
```

基本格式：

```json
{
  "ledger_version": "1.0",
  "decisions": [
    {
      "id": "decision:t34_lineage_accept_001",
      "fact_id": "fact:example:predecessor_of:example_2",
      "from_status": "proposed",
      "to_status": "accepted",
      "decided_by": "reviewer_id",
      "decided_at": "2026-07-30T08:00:00+08:00",
      "reason": "Two independent sources support the relationship.",
      "assertion_ids": [
        "rel:example:source_a",
        "rel:example:source_b"
      ]
    }
  ]
}
```

字段要求：

- `id`：全局稳定，必须以 `decision:` 开头；
- `fact_id`：必须指向当前图谱中实际存在的 Canonical Fact；
- `from_status`：必须与该事实按时间排序后的当前状态一致；
- `to_status`：必须符合允许的状态迁移；
- `decided_by`：人工裁决人或审核主体的稳定标识；
- `decided_at`：带时区的 ISO 8601 时间；
- `reason`：不可为空；
- `assertion_ids`：必须属于该事实，且不可重复。

对应 Schema：

```text
schemas/fact_decision_ledger.schema.json
```

## 4. 冲突事实规则

当同一 Canonical Fact 同时存在 `affirmed` 和 `denied` 断言时，系统输出：

```json
{
  "conflict": true,
  "lifecycle_status": "proposed",
  "suggested_lifecycle_status": "disputed"
}
```

系统不会自动写入 `disputed`。人工账本必须先记录：

```text
proposed -> disputed
```

之后才能执行正式解决：

```text
disputed -> accepted | rejected | deprecated
```

解决冲突时，Decision 必须至少引用两条属于该事实的断言，避免只根据单边证据宣告冲突已经解决。

## 5. 治理与校验

完整校验：

```bash
PYTHONPATH=src python -m ckb.cli validate
```

断言与事实治理报告：

```bash
PYTHONPATH=src python -m ckb.cli assertion-audit \
  --output exports/graph/assertion-governance.json
```

报告包括：

- 原始断言与 Canonical Fact 统计；
- 重复断言组；
- 来源去重结果；
- 冲突事实；
- 审核晋级建议；
- 正式生命周期状态；
- 当前裁决与全部裁决历史；
- 完整 Decision Ledger。

以下情况会导致校验失败：

- Decision ID 重复或格式错误；
- 状态值或状态迁移非法；
- 裁决时间无效或缺少时区；
- 裁决人、理由或断言引用为空；
- Fact ID 不存在；
- 引用的 Assertion 不属于该 Fact；
- 冲突事实跳过 `disputed`；
- 解决冲突时未同时引用至少两条断言。

## 6. 可重复事实快照

生成发布快照：

```bash
PYTHONPATH=src python -m ckb.cli fact-snapshot \
  --output exports/graph/fact-snapshot.json
```

快照只依赖规范化后的事实、来源排序和裁决账本，不写入生成时间等非确定性字段。相同输入会生成相同：

```text
snapshot_id: sha256:<digest>
```

这使发布版本能够判断：

- 数据是否真正发生变化；
- 某次游戏 Bundle 使用的是哪一个事实状态；
- 两次构建是否可以重现；
- 审核裁决是否影响了正式发布内容。

## 7. Graph Bundle 1.3

图谱 Bundle 1.3 在每个 Canonical Fact 中增加：

```text
lifecycle_status
suggested_lifecycle_status
current_decision
decision_history
decision_count
```

Bundle 顶层增加：

```text
fact_lifecycle_counts
```

应用层应遵循：

1. 默认使用 `accepted` 事实作为稳定发布内容；
2. `proposed` 可用于编辑器、研究和待审界面；
3. `disputed` 必须显式展示冲突状态；
4. `rejected` 与 `deprecated` 默认不进入游戏运行时内容，但必须保留在审计数据中；
5. 需要追溯证据时，通过 `assertion_ids` 回到原始 Relationship Assertion。

当前 v1.5.3 只建立治理与发布基础，不自动过滤项目 Bundle。按生命周期裁剪正式运行时内容应在后续内容生产与 Godot 消费层中明确实现。

## 8. CI 门禁

CI 必须实际执行：

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m ckb.cli validate
PYTHONPATH=src python -m ckb.cli assertion-audit --output /tmp/assertion-governance.json --fail-on-conflict
PYTHONPATH=src python -m ckb.cli fact-snapshot --output /tmp/ckb-fact-snapshot.json
PYTHONPATH=src python -m ckb.cli graph --output /tmp/ckb-graph.json
PYTHONPATH=src python -m ckb.cli stats
```

v1.5.3 完成后，CKB 停止继续扩展 v1.5.x 通用底层抽象，下一阶段进入 v1.6.0 装甲车辆内容规模化。
