# v1.6.0 Batch 05：技术声明与玩家体验派生档案

## 目标

Batch 05 不再扩展实体数量，而是验证现有知识模型能否承载可追溯、可比较且不会混淆事实与游戏平衡的车辆档案。

首批选择四种已经完成来源复核的现代主战坦克：

- M1 Abrams；
- Challenger 2；
- Leclerc；
- Type 10。

## 技术声明模型

`technical` 不保存一个无法解释的扁平参数表，而保存带限定条件的声明列表：

```json
{
  "profile_version": "1.0",
  "profile_scope": "...",
  "claims": [
    {
      "field": "maximum_road_speed",
      "value": 65,
      "unit": "km/h",
      "qualifiers": {"surface": "road"},
      "source_urls": ["https://..."]
    }
  ]
}
```

每条声明必须包含：

- 稳定字段名；
- 数值或分类值；
- 单位；
- 限定条件对象；
- 至少一个可追溯的绝对来源 URL。

同一车辆的不同改型、路面条件、燃料条件、装甲配置或质量口径必须分别保存，不得静默合并。例如 Challenger 2 的基础质量与加装装甲后的战备质量是两个声明；M1 Abrams 家族参数必须保留具体配置限定。

## 玩家体验派生模型

`experience_profile` 是由公开技术事实推导的表现建议，不是历史原始事实，也不是最终游戏平衡值：

```json
{
  "profile_version": "1.0",
  "derivation_status": "derived_from_public_technical_facts",
  "basis_fields": ["combat_mass", "maximum_road_speed"],
  "dimensions": {"mass_inertia": 0.8},
  "cues": {"movement": "..."},
  "not_game_balance": true
}
```

规则包括：

- 必须列出推导所依据的技术字段；
- 所有维度值限定在 0—1；
- 每个档案必须有可读的表现提示；
- 必须明确 `not_game_balance: true`；
- 最终速度、伤害、装甲血量和经济数值仍应由独立的 `gameplay` 层决定。

## 首批差异表达

- M1 Abrams：突出高质量、燃气轮机动力、四人乘员和人工装填带来的惯性与乘员协同感；
- Challenger 2：区分基础与加装装甲质量，表达保护优先、较重惯性和四人乘员节奏；
- Leclerc：表达三人乘员、自动装弹和较高公路/越野机动形成的系统化、高节奏体验；
- Type 10：表达较低质量、主动液气悬挂、自动装弹和 C4I 集成形成的敏捷与网络化体验。

这些描述只用于帮助游戏研发理解“玩家应该感受到什么”，不包含现实攻击流程、弱点利用方法或制造说明。

## CI 门禁

Batch 05 的清单要求每个实体：

- 至少两个独立实体来源；
- 至少六条技术声明；
- 完整的派生体验档案。

内容审计还会拒绝缺失单位、限定条件、来源 URL，或超出 0—1 范围的体验维度。质量报告新增技术声明总数和派生体验档案数量，以避免只统计“字段非空”。
