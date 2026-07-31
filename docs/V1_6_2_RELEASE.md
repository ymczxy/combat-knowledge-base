# v1.6.2 航空装备验收

v1.6.2 按批准边界完成航空装备闭环：

- 飞机及主要型号/家族关系；
- 二战活塞飞机与发动机；
- 喷气飞机与发动机；
- 航空武器、弹药和 `uses_ammunition` 关系；
- 机载雷达和平台传感器关系；
- 多配置技术声明隔离；
- 独立航空 Godot Runtime Bundle/Lock。

锁定 Runtime profile 为 `data/curated/destory/aviation_build_profile.json`，包含 9 个实体、25 个配置、49 条技术声明、21 个来源引用和 7 条独立关系断言。其 Bundle/Lock 契约和真实 Godot 4.7.1 加载由自动测试及领域运行矩阵共同验证。

本版本不生成游戏伤害、命中、穿透或平衡值，也不包含制造或现实攻击操作教程。
