# 数据标准

## 稳定 ID

显示名称不能作为主键：

```text
ckb:weapon:firearm:akm
ckb:platform:ground:t_34_85
ckb:ammunition:cartridge:7_62x39
```

## 字段分区

- `identity`：规范名、原文名、别名和外部 ID；
- `classification`：知识域、类别、子类、时代和标签；
- `origin`：国家、机构和时间；
- `technical`：带单位和限定条件的事实参数；
- `relationships`：弹药、平台、家族和替代关系；
- `experience_profile`：玩家感知派生数据；
- `gameplay`：平衡和资源数据；
- `provenance`：字段来源、审核和可信度；
- `rights`：当前暂缓处理但保留的数据权利状态。

## 数值声明

不同口径不强制合并。例如“空重”“战斗全重”“不同批次”应保留为独立 claim，并记录限定条件。

## 审核状态

- `planned`
- `unverified`
- `machine_imported`
- `source_checked`
- `cross_checked`
- `expert_reviewed`
- `deprecated`

## 完整度等级

- A：核心事实、关系、来源和体验完整；
- B：主要字段完整，可用于游戏研究；
- C：可识别、可检索，有基本来源；
- D：目录占位；
- E：疑似冲突或待废弃。
