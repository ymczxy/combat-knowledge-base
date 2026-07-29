# v1.3.1 外部实体匹配与解析决策

## 目标

把 v1.3.0 生成的目录候选与 Wikidata、Wikipedia 等外部搜索结果进行统一评分，输出可追踪的自动接受、人工审核和拒绝决策。

## 评分组成

总分由以下部分组成：

- 名称相似度；
- 词元重合度；
- 别名匹配奖励；
- 领域与类别上下文奖励；
- 歧义候选惩罚。

评分只用于候选排序，不代表事实已经核验。

## 决策阈值

- `auto_accept`：首名分数至少 0.90、领先下一名至少 0.08，且目录候选本身不是歧义项；
- `human_review`：分数至少 0.62，但不足以安全自动接受；
- `reject`：相关性不足。

任何来自混合目录或跨类别同名的候选，即使名称完全一致，也不会自动进入主库。

## 实体范围

解析器初步判断外部结果代表：

- `family`：武器或装备家族；
- `class`：舰艇级别等类别实体；
- `variant`：型号、批次或改进型；
- `prototype`：原型或技术验证机；
- `model`：一般具体型号。

该判断用于避免把“家族”和“具体型号”错误合并。

## 离线解析

```bash
PYTHONPATH=src python -m ckb.cli resolve-fixture \
  tests/fixtures/t34_resolution.json \
  --output exports/resolution
```

输出：

```text
exports/resolution/
├── decisions.json
├── review_queue.json
└── manifest.json
```

## 联网解析单个候选

```bash
PYTHONPATH=src python -m ckb.cli resolve-one "T-34" \
  --group wwii_armored_vehicles \
  --source wikidata \
  --language en \
  --output exports/resolution/t34
```

Wikipedia 示例：

```bash
PYTHONPATH=src python -m ckb.cli resolve-one "T-34" \
  --group wwii_armored_vehicles \
  --source wikipedia \
  --language en
```

搜索结果默认写入 `data/cache/search/`。再次运行相同查询时优先读取缓存；使用 `--refresh` 可重新查询。

## 安全边界

- 自动接受只表示“实体身份高度可信”，不表示技术参数已核实；
- 自动接受结果仍以 `source_checked` 之前的审核状态进入 staging；
- 外部搜索摘要不直接作为主库正文；
- 低置信度和同名异物必须由人工确认；
- 后续版本会加入国家、年代、制造商、口径和平台关系等更强约束。
