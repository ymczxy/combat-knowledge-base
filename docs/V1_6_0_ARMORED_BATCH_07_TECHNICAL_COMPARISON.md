# v1.6.0 Armored Batch 07：技术声明标准化与比较层

## 目标

Batch 07 不新增装甲车辆实体，也不改写任何原始技术声明。它为当前已经建立技术档案的八个实体生成一个可重复构建的比较层，使不同来源采用的英制、公制和历史单位可以在同一视图中比较。

覆盖实体：

- M1 Abrams
- Challenger 2
- Leclerc
- Type 10
- M4 Sherman
- T-34 Model 1940
- Panther
- Type 59

## 数据边界

规范实体中的 `technical.claims` 仍然是事实来源层。每条声明保留：

- 原始字段；
- 原始数值；
- 原始单位；
- 改型、路面、燃油、装甲套件等限定条件；
- 来源 URL。

标准化层只额外生成：

- 标准值；
- 标准单位；
- 转换状态；
- 无法识别时的明确错误。

它不会：

- 从同一车辆的多个改型中选择一个“代表参数”；
- 合并不同测试条件下的速度、质量或续航；
- 将体验档案或游戏平衡值混入现实参数排序；
- 猜测未知单位。

## 当前标准单位

| 维度 | 标准单位 |
|---|---|
| 质量 | `t` |
| 速度 | `km/h` |
| 行程与续航 | `km` |
| 发动机功率 | `kW` |
| 车体尺寸 | `m` |
| 口径与装甲厚度 | `mm` |
| 压力 | `kPa` |
| 人员与弹药数量 | 保留 `people`、`rounds` |

目前支持的来源单位包括 `short_ton`、`long_ton`、`mph`、`mi`、`hp`、`bhp`、`PS`、`ch`、`t`、`kg`、`km/h`、`km`、`m`、`cm` 和 `mm` 等。

## 命令行

生成完整 JSON 比较数据：

```bash
PYTHONPATH=src python -m ckb.technical \
  --output exports/technical/comparison.json \
  --fail-on-unsupported
```

同时生成站点 Markdown：

```bash
PYTHONPATH=src python -m ckb.technical \
  --output exports/technical/comparison.json \
  --markdown site_docs/compare/technical.md \
  --fail-on-unsupported
```

按字段和实体筛选：

```bash
PYTHONPATH=src python -m ckb.technical \
  --field engine_power \
  --field combat_mass \
  --entity ckb:platform:ground:m1_abrams \
  --entity ckb:platform:ground:type_10_tank \
  --output /tmp/mbt-comparison.json
```

## 输出结构

每一行包含：

```json
{
  "entity_id": "ckb:platform:ground:m1_abrams",
  "field": "maximum_road_speed",
  "original": {"value": 42, "unit": "mph"},
  "normalized": {"value": 67.592448, "unit": "km/h"},
  "qualifiers": {"configuration": "M1 family"},
  "source_urls": ["https://..."],
  "comparison_status": "normalized"
}
```

描述性声明保留原值，但其 `comparison_status` 为 `descriptive`，不会参与数值排序。无法转换的数值声明标记为 `unsupported_numeric`，并在启用 `--fail-on-unsupported` 时使 CI 失败。

## CI 门禁

Batch 07 要求：

1. 当前71条技术声明全部进入比较输出；
2. 所有数值声明均能转换或保持在明确的标准单位中；
3. 未知数值单位数量必须为0；
4. 原始值、限定条件和来源必须完整保留；
5. M4等多改型实体必须继续输出多条独立记录；
6. JSON比较数据和Markdown比较页面都必须成功生成。

## 后续

完成标准化以后，下一步可以建立：

- 指定配置的横向对比查询；
- 功重比等明确公式的派生指标；
- 按时代、国家和车辆类别的比较页面；
- 面向Godot的紧凑比较Bundle。

派生指标必须记录公式、输入声明和限定条件，不能直接回写为原始事实。
