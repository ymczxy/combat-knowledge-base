# v1.6.4 火炮、导弹、防空与传感器验收

v1.6.4 按批准边界完成综合系统闭环：

- 火炮、迫击炮及其弹药；
- 防空系统组件；
- 导弹与发射平台；
- 雷达与传感器平台；
- 多组件系统关系图；
- 多配置技术声明隔离；
- 独立综合系统 Godot Runtime Bundle/Lock。

锁定 Runtime profile 为 `data/curated/destory/integrated_systems_build_profile.json`，包含 16 个实体、20 个配置、58 条技术声明、32 个来源引用和 10 条独立关系断言。其 Bundle/Lock 契约和真实 Godot 4.7.1 加载由自动测试及领域运行矩阵共同验证。

本版本保持事实、体验派生和游戏平衡三层隔离，不包含现实制造、规避防御或攻击操作指导。
