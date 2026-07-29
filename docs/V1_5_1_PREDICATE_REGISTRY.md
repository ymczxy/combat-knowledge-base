# v1.5.1 Predicate Registry

CKB 从 v1.5.1 开始把关系谓词视为受治理的本体资源，而不是可以任意填写的字符串。

## 目标

Predicate Registry 负责回答以下问题：

- 一个关系名称究竟表示什么；
- 关系的方向是什么；
- 是否存在正式反向关系；
- 是否为对称关系；
- 是否允许进行传递遍历；
- 哪些实体类型或分类可以作为起点和终点；
- 关系是否仍处于有效、实验或废弃状态。

正式注册表位于：

```text
data/ontology/predicates.json
```

Schema 位于：

```text
schemas/predicate_registry.schema.json
```

## 命名规则

谓词名称使用小写英文与下划线：

```text
developed_into
variant_of
uses_ammunition
participated_in
```

不要在正式数据中临时创造近义词。例如，不应同时出现：

```text
uses_ammo
fires_ammunition
ammunition_type
```

这类需求应优先复用 `uses_ammunition`，或先提交新的 Predicate Definition。

## 方向

每条关系都必须按注册表定义的方向写入。

```text
AKM --uses_ammunition--> 7.62×39 mm
```

反向事实不需要重复存储：

```text
7.62×39 mm --ammunition_used_by--> AKM
```

图查询层可以根据注册表中的 `inverse` 自动解析反向事实。只有当反向记录具有独立来源、限定条件或审核状态时，才应额外建立独立 Relationship。

## 对称关系

`contemporary` 和 `related_design` 属于对称关系。

只记录：

```text
A --contemporary--> B
```

即可从 B 查询到 A。不要为了导航方便机械复制第二条边。

## 传递关系

只有注册表中明确标记 `transitive: true` 的关系才能进行传递闭包查询。

例如：

```text
BT-7 --development_line_predecessor--> T-34
T-34 --development_line_predecessor--> T-44
```

允许推导 BT-7 位于 T-44 的更早发展谱系中。

`developed_into` 刻意不设为传递关系，因为它表达较直接的发展步骤，跨越多个型号后不应继续声称“直接发展为”。

## 类型约束

关系可以限制起点和终点的 `entity_type` 或 `classification.class`。

例如：

```text
uses_ammunition
source_entity_types = weapon | platform | system
target_entity_types = ammunition
```

以下关系将被拒绝：

```text
AKM --uses_ammunition--> T-34
```

因为目标不是 `ammunition`。

## 校验

构建图谱时默认执行严格谓词校验：

```bash
PYTHONPATH=src python tools/build_graph.py
```

检查内容包括：

- 谓词是否已经注册；
- 反向关系是否存在并互相指回；
- 对称关系定义是否合法；
- 标签和状态是否完整；
- 起点和终点实体类型是否符合约束；
- 原有 Relationship ID、端点、置信度和来源字段是否有效。

迁移旧数据时可以暂时使用：

```bash
PYTHONPATH=src python tools/build_graph.py --allow-unknown-predicates
```

该参数只用于过渡，不应进入正式发布流水线。

## 新增谓词流程

1. 证明现有谓词无法准确表达该事实。
2. 明确单向、反向或对称语义。
3. 明确是否真的满足数学意义上的传递性。
4. 定义允许的实体类型和分类。
5. 同时补充中英文标签及描述。
6. 为注册表验证、类型错误和查询方向增加测试。
7. 再开始写入使用该谓词的 Relationship。

## 当前阶段边界

Predicate Registry 只负责结构和语义约束，不自动证明历史事实为真。关系是否真实、限定于哪个时期、适用于哪些型号，仍由 Relationship 的 `provenance`、`confidence` 和 `qualifiers` 表达并接受独立审核。
