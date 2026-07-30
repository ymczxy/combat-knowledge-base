# Godot 与《destory》接入

## 原则

Godot 不加载整个 CKB，只加载由项目 Profile 裁剪并锁定版本的运行时子集。

## 数据分层

```text
encyclopedia_data    历史和展示
simulation_data      弹丸、爆炸、热、烟气、压力和结构作用
balance_data         成本、冷却、解锁和难度
presentation_data    声音、动画、特效、图标和模型路径
```

现实技术声明、技术派生指标和游戏平衡必须保持分层。运行时 Bundle 中的功重比等指标明确标记为 `not_source_fact` 与 `not_game_balance`。

## 两种输出

### 研究与工具输出

```bash
PYTHONPATH=src python -m ckb.cli build \
  --profile destory \
  --output exports
```

该命令生成完整项目子集，适合编辑器工具、研究浏览、SQLite和Markdown，不建议作为游戏常驻运行时文件。

### Godot 运行时输出

```bash
PYTHONPATH=src python -m ckb.godot_bundle \
  --profile data/curated/destory/build_profile.json \
  --output exports/godot \
  --fail-on-error
```

输出：

```text
exports/godot/ckb_destory_runtime.json
exports/godot/ckb-lock.json
```

运行时 Bundle 只包含显式白名单实体、最小分类、配置 ID、标准化技术值、描述性声明、体验派生档案、派生指标和来源索引。它不包含完整 canonical 实体、审核记录、权利结构或游戏平衡字段。

## 推荐 Resource

```gdscript
class_name WeaponDefinition
extends Resource

@export var ckb_id: String
@export var display_name: String
@export var category: StringName
@export var era: StringName
@export var ammunition_ids: PackedStringArray
@export var simulation_profile: Resource
@export var balance_profile: Resource
@export var presentation_profile: Resource
```

装甲车辆侧建议以 `entity.id` 建立运行时索引，再按 `configuration_id` 选择技术声明和派生指标。不得忽略声明的 `qualifiers` 后直接把多个改型合并成单一数值。

## 运行时结构

```text
manifest
source_table[]
entities[]
  id
  display_name
  classification
  configurations[]
  technical_claims[]
    claim_ref
    field
    kind
    value / unit
    qualifiers
    configuration_id
    source_refs[]
  derived_metrics[]
    metric_ref
    value / unit
    input_claim_refs[]
    configuration_id
    source_refs[]
```

`source_refs` 指向顶层去重 URL 表；`input_claim_refs` 指向同一实体的技术声明。Godot 无需加载完整研究文档即可保留追溯链。

## 锁定发行版本

游戏发行版本必须同时携带 `ckb-lock.json`。Lock 文件固定实体顺序、格式版本、Payload SHA-256、实际 Bundle 文件 SHA-256和资源清单。

发行前至少检查：

1. Lock 的 `bundle_filename` 与实际文件一致；
2. 实际文件 SHA-256 与 `bundle_file_sha256` 一致；
3. Bundle manifest 的 `content_sha256` 与 Lock 一致；
4. 运行时代码支持对应 `format_version` 与 `schema_version`；
5. 游戏自己的 `balance_data` 不写回 CKB 事实层。
