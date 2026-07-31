# V1.7 规模化上下文与图谱验收

V1.7 不再以单个诺曼底样例代表“完成”。正式验收口径要求 Place、Country、Organization、Manufacturer、MilitaryUnit、Battle、Conflict、Person、Facility 九类实体分别至少具有 5 个 `source_checked` 实例，并且每个计入实例至少包含 2 个来源与 3 条结构化声明。

当前规模化场景覆盖：

- 诺曼底登陆与底特律军工背景；
- 不列颠战役、RAF Fighter Command 与喷火式生产背景；
- 中途岛战役、美国太平洋舰队、TF 16 与 F4F；
- 普罗霍罗夫卡、近卫第5坦克集团军、T-34 与乌拉尔第183工厂；
- 马岛战争圣卡洛斯阶段、皇家海军特遣群与海鹞。

五项正式输出为：

1. 装备时间轴；
2. 战役—装备关系图；
3. 企业产业链图；
4. 工厂地点图；
5. 部队编制图。

`tests/test_v1_7_scaled_acceptance.py` 固化上述数量、来源、技术声明和图谱规模门槛。若任何一类低于门槛，或任一输出失去可消费数据，V1.7 验收即失败。
