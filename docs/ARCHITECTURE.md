# 技术架构

```text
External Sources
  ↓
Source Records / Claims
  ↓
Identity Resolution
  ↓
Canonical Entities
  ↓
Validation
  ├── Markdown
  ├── SQLite
  ├── JSON Bundle
  └── Godot Project Pack
```

## 数据四层

### 1. 来源声明层

保存来源原始口径、限定条件和冲突，不急于压缩成唯一数字。

### 2. 标准化层

统一名称、单位、分类、时代、国家、家族和型号关系。

### 3. 体验层

把现实装备转译为玩家可感知的声学、视觉、冲击、操控、环境、传感器、人员负荷和故障征兆。

### 4. 游戏层

维护平衡值、科技树、AI、特效、音效和 Godot 资源路径。游戏层不得冒充现实事实。

## 权威格式

当前以 JSON 为权威格式；SQLite、Markdown 和 Godot Bundle 均为构建产物。

## 实体类型

`weapon`、`ammunition`、`platform`、`protection`、`fortification`、`sensor`、`fire_control`、`electronic_warfare`、`engineering_equipment`、`material`、`effect`、`environment`、`technology`、`organization`、`manufacturer`、`country`、`conflict`、`source`。
