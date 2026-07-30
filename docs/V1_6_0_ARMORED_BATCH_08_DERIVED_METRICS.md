# v1.6.0 Armored Batch 08：可追溯派生指标

## 目标

Batch 08 在 Batch 07 标准化层之上建立第一类现实技术派生指标：功重比。

它不增加实体，也不把计算结果伪装成来源事实。每个指标必须明确指定输入 claim 的索引和预期字段，才能进入构建结果。

## 为什么不能自动选择参数

同一车辆可能同时存在：

- 基础质量；
- 战斗全重；
- 附加装甲状态质量；
- 空重到最大授权质量区间；
- 不同改型的额定功率。

因此“搜索一个质量字段再除以一个功率字段”会制造看似精确、实际语义错误的结果。Batch 08 禁止这种启发式选择。

每条规格必须写明：

```json
{
  "entity_id": "ckb:platform:ground:challenger_2",
  "formula": "power_to_mass",
  "inputs": {
    "power": {"claim_index": 7, "expected_field": "engine_power"},
    "mass": {"claim_index": 2, "expected_field": "combat_ready_mass"}
  }
}
```

如果 claim 顺序或字段发生变化，构建会失败，要求人工确认后更新规格。

## 当前指标

Batch 08生成5条指标：

1. M1A2 Abrams功重比；
2. Challenger 2基础质量功重比；
3. Challenger 2附加装甲状态功重比；
4. Leclerc空重到最大授权质量范围对应的功重比区间；
5. Type 10公开标准配置功重比。

Challenger 2的两种状态必须保留为两条结果。Leclerc使用质量区间，结果输出为升序区间，不使用中点。

## 输出字段

每个派生指标包括：

- `metric_id`；
- 实体ID和名称；
- 指标类型与公式；
- 结果值和单位；
- 配置限定；
- 功率输入的claim索引、原值、标准值、限定条件和来源；
- 质量输入的claim索引、原值、标准值、限定条件和来源；
- `not_source_fact: true`；
- `not_game_balance: true`。

## 命令行

```bash
PYTHONPATH=src python -m ckb.technical_metrics \
  --output exports/technical/derived-metrics.json \
  --markdown site_docs/compare/derived-metrics.md \
  --fail-on-error
```

默认读取：

```text
data/derived/technical_metrics_v1_6_0_batch_08.json
```

## 解释边界

功重比只表示公开额定功率与指定质量之间的数学比值。它不能单独推导：

- 实际加速；
- 转向性能；
- 越野速度；
- 可靠性；
- 战斗效能；
- 游戏中的机动或平衡数值。

这些结果只能作为进一步研究和体验设计的输入之一。

## CI门禁

Batch 08要求：

1. 5条规格全部成功生成；
2. 覆盖4个实体；
3. 错误数量为0；
4. claim索引和预期字段必须完全匹配；
5. 功率必须标准化为`kW`；
6. 质量必须标准化为`t`；
7. 所有结果必须保留输入与来源；
8. JSON和Markdown产物必须成功生成。

## 后续

下一阶段可以在同样的显式输入机制上增加：

- 道路/越野续航差异；
- 功率与质量的配置矩阵；
- 单位面积质量等明确公式；
- 面向Godot的紧凑派生指标Bundle。

新增公式必须注册并独立测试，不能允许用户输入任意表达式执行。
