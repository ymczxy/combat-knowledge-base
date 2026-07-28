# Godot 与《destory》接入

## 原则

Godot 不加载整个 CKB，只加载由项目 Profile 裁剪并锁定版本的子集。

## 数据分层

```text
encyclopedia_data    历史和展示
simulation_data      弹丸、爆炸、热、烟气、压力和结构作用
balance_data         成本、冷却、解锁和难度
presentation_data    声音、动画、特效、图标和模型路径
```

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

## 构建

```text
CKB canonical JSON
  ↓
data/curated/destory/build_profile.json
  ↓
ckb build --profile destory
  ↓
ckb_destory.json / ckb_destory.sqlite / generated .tres
```

游戏发行版本使用 `ckb-lock.json` 固定实体、数据版本、构建哈希和资源清单。
