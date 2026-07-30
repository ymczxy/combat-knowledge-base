# v1.6.0 装甲车辆内容规模化

## 1. 阶段目标

v1.6.0 不再扩展通用底层抽象，目标是把既有 Entity、Relationship Assertion、Canonical Fact 和事实生命周期能力用于可持续的真实内容生产。

装甲车辆主体库按小批次推进。每个批次都必须明确：

- 新增或补充哪些实体；
- 新增哪些独立关系断言；
- 当前来源和审核状态；
- 哪些字段已经完成，哪些字段明确延期；
- 自动校验和内容质量指标是否通过。

## 2. Batch 01：发展线骨架

`v1.6.0-armored-vehicles-batch-01` 建立美国、英国、法国、中国和日本装甲车辆的首批发展线骨架：

- 27 个 Canonical Entity；
- 19 条独立 Relationship Assertion；
- 覆盖二战、冷战早期、冷战后期和当代；
- 关系全部存入 `data/relationships/`，不新增实体内嵌关系；
- 其中一条关系把旧库中的 M1A2 变型连接到本批新增的 M1 Abrams 家族实体；
- 技术参数和体验模型暂不填充，避免把未经交叉审核的摘要误当作完整档案。

Batch 01 建立时实体保持 `unverified`，单一公开来源只用于建立可追踪的初始记录，不代表事实已经完成审核。

## 3. Batch 02：美国与英国来源复核

`v1.6.0-armored-vehicles-batch-02-source-review` 不新增实体，而是复核 Batch 01 中的美国和英国发展线：

- 复核 13 个实体；
- 复核 11 条关系断言；
- 为每个实体和每条关系断言保留至少两条独立来源；
- 第二来源优先采用 The Tank Museum、美国陆军与英国陆军公开资料；
- 正式状态提升到 `source_checked`，不因来源数量自动提升到 `cross_checked`。

关系语义同时进行了校正：

- M26 Pershing 到 M46 Patton、M48 Patton 到 M60 记录为直接发展；
- M60 到 M1 Abrams 保留为更宽泛的发展线前身；
- Cromwell 到 Comet 保留为直接发展；
- Comet 与 Centurion 改为 `contemporary`，不再伪造直接谱系；
- Challenger 1 到 Challenger 2 改为替代世代的 `development_line_predecessor`，不再写成同一车辆直接升级。

## 4. Batch 03：苏联与德国内嵌关系迁移

`v1.6.0-armored-vehicles-batch-03-embedded-migration` 不新增实体，而是清理 v1.4 阶段遗留的实体内嵌关系：

- 涉及 27 个苏联和德国装甲车辆实体；
- 删除 37 条实体内嵌关系记录；
- 经正反向、对称和语义重复归一化后，对应 24 个 Canonical Fact；
- 其中 5 个事实已在 `armored_development_v1_5_0.json` 中存在；
- 新增 19 条独立 Relationship Assertion；
- 所有迁移记录保持 `unverified`，迁移不等于来源审核。

迁移规则：

1. 正向和反向关系只保留一条稳定方向的独立断言；
2. `contemporary` 等对称关系只保留一条断言；
3. 已存在的独立断言不重复生成；
4. Tiger 和 Panther 的混合 `developed_into` / `development_line_successor` 旧边归一为单一稳定关系；
5. 迁移实体不得重新出现内嵌关系，单元测试会锁定这一约束；
6. 每条迁移断言保留来源和 `migration_origin` 限定信息。

Batch 03 完成后，旧苏德装甲包只保存实体本身，图谱关系统一从 `data/relationships/` 消费。

## 5. 内容批次清单

每个批次在 `data/content_batches/` 下保存一份 JSON 清单，至少包括：

```json
{
  "batch_id": "v1.6.0-armored-vehicles-batch-03-embedded-migration",
  "version": "1.6.0",
  "scope": "...",
  "entity_ids": [],
  "relationship_ids": [],
  "quality_targets": {
    "minimum_sources_per_entity": 1,
    "minimum_sources_per_relationship": 1
  }
}
```

内容审计会拒绝：

- 重复或缺失的 `batch_id`；
- 未知实体 ID；
- 未知关系 ID；
- 批次内重复引用；
- 批次实体缺失名称、分类、时代、标签、来源、玩法状态或权利状态等核心字段；
- 实体独立来源数量低于批次声明值；
- 关系断言独立来源数量低于批次声明值。

专用迁移测试还会拒绝：

- 27 个迁移实体重新出现内嵌关系；
- 24 条规范迁移断言缺失；
- 24 条迁移断言不能归并为 24 个独立 Canonical Fact。

## 6. 内容质量指标

运行：

```bash
PYTHONPATH=src python -m ckb.content_audit \
  --output exports/content/content-report.json
```

报告包括：

- Canonical Entity 和 GroundVehicle 数量；
- 主要国家标签覆盖；
- 审核状态分布；
- 核心字段完整率；
- 至少一个来源和至少两个来源的覆盖率；
- 技术字段与体验模型覆盖率；
- 实体内嵌关系和独立关系数量；
- 独立关系迁移率；
- 关系来源与审核状态覆盖；
- 已纳入内容批次与尚未纳入批次的装甲车辆。

这些指标用于暴露真实欠账，不用于把数量增长包装成内容质量已经完成。

## 7. 来源和审核原则

1. 单一来源只能建立 `unverified` 初始记录。
2. 增加第二条来源时，应优先使用官方档案、博物馆、制造商历史资料、军史机构或高质量专业文献，而不是重复转载。
3. 来源数量不自动改变审核状态。
4. 发展谱系关系必须区分直接发展、宽泛前后继、设计影响和同期关系。
5. 无法确定的关系应省略或使用较弱的正式谓词，不得为了让图谱连续而强行建立关系。
6. 现代装备仍只整理公开知识和游戏抽象，不加入制造、规避防御或现实攻击操作教程。

## 8. 后续批次建议

### Batch 04：法国、中国和日本来源复核

- 为 Batch 01 中法国、中国和日本的 14 个实体补充独立来源；
- 重新判断 AMX-30—勒克莱尔、59式以后中国坦克分支和日本战后主战坦克关系强度；
- 继续使用批次级实体与关系双来源门禁。

### Batch 05：苏联与德国来源复核

- 为 Batch 03 的高价值发展线补充第二来源；
- 优先复核 T-34/T-44/T-54、KV/IS、BT、Panther 和 Tiger 系列；
- 迁移后的关系在完成来源复核前继续保持 `unverified`。

### Batch 06：技术与体验字段

只对已经完成来源审核的代表性车辆填充：

- 尺寸、质量、乘员、动力、机动、防护与武装等公开技术摘要；
- 玩家可感知的声音、视觉、操控、冲击和故障征兆；
- 明确区分原始事实、标准化值、体验派生值和游戏平衡值。

## 9. CI 门禁

v1.6.0 内容批次必须继续通过完整项目 CI，并额外执行：

```bash
PYTHONPATH=src python -m ckb.content_audit \
  --output /tmp/ckb-content-report.json
```

内容审计失败时，不得通过删除清单或降低字段要求绕过；应修复批次数据或明确调整正式规则。
