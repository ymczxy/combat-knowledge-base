# Changelog

## 2.0.0

- 冻结 CKB Schema、核心谓词、实体边界和 Godot Runtime Bundle/Lock 合同。
- 完成装甲车辆、轻武器/弹药、航空、舰船、防空传感器及时间/地点/组织/战役上下文首批规范化内容。
- 新增时间索引、实体/关系查询 API、Godot `CKBQuery` SDK 和独立关系断言消费。
- 明确 v2.0 迁移、兼容性、发布快照和回滚规则，并通过稳定版门禁。

## 1.6.1

- 完成 M2 Browning 与 12.7 x 99 mm / .50 BMG source-checked vertical slice。
- 建立 Magazine component 边界、方向性 `accepts_magazine` 谓词及显式端点约束。
- 为 `variant_of` / `has_variant` 增加端点类型约束，并完成 Thompson family 与 M1A1 闭环。
- 新增独立轻武器 Godot Runtime Bundle、Lock 和 Linux Smoke 场景；装甲车辆 Runtime 快照保持不变。
- 通过 157 项单元测试、完整治理审计、Bundle/Lock Contract、CKB CI 和 Godot Linux Runtime Smoke。
- 保持现实技术资料、体验派生值和游戏平衡值分层；不包含装药、制造、攻击操作或游戏平衡指导。

## 1.6.0

- 完成首个装甲车辆主体库：79 个 Canonical Entity，其中 57 个 GroundVehicle，覆盖苏联/俄罗斯、德国、美国、英国、法国、中国和日本主要发展线。
- 建立 11 个正式内容批次，全部 57 个 GroundVehicle 均纳入批次，未入批数量为 0。
- 将全部实体内嵌关系迁移为独立 Relationship Assertion；当前 44 条独立断言，内嵌关系为 0，独立存储率为 100%。
- 完成 29 个实体和 17 条关系的独立多来源审核，保留其余记录的 `unverified` 状态，不以数量替代可信度。
- 为 M1 Abrams、Challenger 2、Leclerc、Type 10、M4 Sherman、T-34 Model 1940、Panther 和 Type 59 建立首批结构化技术与体验档案。
- 新增 71 条可追溯技术声明；55 条数值声明标准化为统一单位，16 条描述性声明原样保留，未知数值单位为 0。
- 新增 5 条显式绑定配置和输入 claim 的功重比派生指标，并标记为 `not_source_fact` 与 `not_game_balance`。
- 新增面向 Godot 的紧凑运行时 Bundle 与 `ckb-lock.json`，包含 8 个实体、18 个显式配置、71 条技术声明、5 条派生指标和 14 个去重来源引用。
- 新增 Godot 4 `CKBRuntimeBundle` 加载器，校验文件 SHA-256、格式与 Schema 版本、资源清单、实体顺序和配置索引；调用方必须显式选择 `configuration_id`。
- 在 Ubuntu 24.04 上使用官方 Godot 4.7.1 Linux x86_64 二进制完成真实场景冒烟测试，验证 Bundle/Lock、多配置查询、来源解析和 1280×720 截图生成。
- 真实引擎测试发现并修复加载器首次编译时通过全局 `class_name` 自引用导致的 GDScript 编译问题。
- 同步项目包、运行时、README、Roadmap 和发布文档版本为 1.6.0，并增加版本一致性回归测试。

## 1.5.3

- 为 Canonical Fact 增加 `proposed`、`accepted`、`disputed`、`rejected`、`deprecated` 生命周期状态。
- 新增版本化事实裁决账本，保存裁决人、裁决时间、理由、引用断言和完整状态变更历史。
- 校验事实状态迁移、未知事实、无效断言引用、重复引用和带时区的 ISO 8601 裁决时间。
- 冲突事实必须先进入 `disputed`，正式解决时必须同时引用至少两条相关断言。
- 新增确定性的 `ckb fact-snapshot`，相同事实和裁决输入生成相同 SHA-256 快照 ID。
- Graph Bundle 升级为 1.3，输出事实生命周期、当前裁决、裁决历史和状态统计。
- `validate`、`stats`、`assertion-audit` 和 `graph` 接入事实裁决账本及生命周期校验。
- 新增裁决账本 JSON Schema、生命周期测试和 CI 快照门禁。
- 同步项目包和运行时版本为 1.5.3。

## 1.5.2

- 新增 Relationship Assertion 到 Canonical Fact 的聚合层，保留全部原始断言和证据链。
- 对正向、反向、对称、实体内嵌和独立 Relationship 进行稳定规范化与事实归并。
- 按 `source_id + url` 去重来源，输出独立来源数量、重复断言组和事实置信度。
- 支持 `affirmed` / `denied` 极性并检测同一事实的正反冲突。
- 分离 `asserted_review_status` 与 `suggested_review_status`，审核建议不得自动修改正式状态。
- 新增 `ckb assertion-audit` 命令、治理报告、冲突门禁及对应测试。
- Graph Bundle 升级为 1.2，包含 Entity、Relationship Assertion、Canonical Fact 与 Predicate Registry。
- 同步项目包和运行时版本为 1.5.2。

## 1.5.1

- 新增正式 Predicate Registry，为关系定义中英文语义、反向关系、对称性、传递性和状态。
- 为发展谱系、型号、影响、同期、相关设计、弹药、动力、武装、生产、设计、使用、战役、地点和组织关系建立首批规范谓词。
- `KnowledgeGraph` 新增反向/对称关系解析和受控传递遍历，不再要求为导航机械复制反向边。
- 新增关系端点的 `entity_type` 与 `classification.class` 语义约束，并对未注册谓词执行严格校验。
- 图谱 Bundle 升级为 1.1，内嵌所使用的 Predicate Registry，保证导出数据可以独立解释。
- 新增 `ckb predicate-audit` 与 `ckb graph`；`ckb validate` 现在同时校验实体、目录、来源、关系和谓词。
- 新增 Predicate Registry JSON Schema、规范文档及反向、对称、传递、未知谓词和端点类型测试。
- 同步项目包、运行时和 README 版本为 1.5.1。

## 1.5.0

- 将 Relationship 提升为带独立 ID、来源、审核状态、置信度和限定条件的一等知识对象。
- 新增 `KnowledgeGraph`，支持出入边索引、邻居查询、最短有向路径和关系完整性校验。
- 新增独立 Relationship JSON Schema 与 `data/relationships` 数据目录。
- 将首批苏联坦克发展关系迁移为可独立审校的图谱关系记录。
- 新增 `tools/build_graph.py`，可输出同时包含实体与关系的统一图谱 Bundle。
- 新增关系端点、置信度、邻居查询和路径查询测试。
- 同步项目包版本与运行时版本为 1.5.0。

## 1.4.1

- 扩展苏联坦克专题，新增 BT-2、BT-5、KV-2、KV-1S、IS-1、IS-3 和 T-55。
- 启动德国装甲车辆专题，新增一号、二号、三号、四号、虎式、虎王和象式。
- 增加黑豹 D、A、G 三个主要生产型，并连接既有黑豹家族实体。
- 建立 BT、KV/IS、T-54/T-55、Panzer、Tiger 和 Panther 等发展与型号关系。
- 本批新增 16 个 Canonical 实体，继续保持来源、审核、玩法和版权状态字段完整。

## 1.4.0

- 正式进入按专题扩展 Canonical 主库的内容建设阶段。
- 新增首个专题包：苏联坦克发展线，共 10 个规范实体。
- 覆盖 T-18、T-26、BT-7、T-28、T-35、KV-1、T-34 1940年型、IS-2、T-44 和 T-54。
- 为轻型、快速、中型、重型和早期主战坦克建立统一分类。
- 新增发展前后继、同期装备和技术影响关系，并与现有 T-34-85 实体连接。
- 所有新增内容保留来源记录、审核状态、游戏配置状态和版权状态。

## 1.3.3

- 新增从批量匹配结果生成 Canonical 晋级提案的流水线。
- 每个提案保留 Candidate ID、建议正式 ID、外部 ID、来源、置信度和阻塞项。
- 自动区分 `promotion_ready` 与 `review_required`，歧义候选不能直接晋级。
- 新增 `tools/build_promotions.py` 命令与晋级 Bundle。
- 新增正式晋级、歧义阻塞和输出清单测试。

## 1.3.2

- 新增类别关键词、排除关键词与时代年份窗口等结构化匹配约束。
- 新增约束调整分、冲突原因、检测年份和最终决策。
- 新增基于本地搜索缓存的批量解析流水线。
- 新增 `batch-resolve-cache` 和 `--constraints` 参数。
- 批量输出接受、人工审核、拒绝和缺失缓存队列。
- 新增 12 个跨时代规范实体，使主库开始从工具骨架转向真实内容。
- 新增结构化约束和批量解析测试及 CI 门禁。

## 1.3.1

- 新增外部搜索结果统一匹配评分器。
- 综合名称相似度、词元重合、别名、领域和类别上下文进行排序。
- 新增 `auto_accept`、`human_review` 和 `reject` 三段决策。
- 歧义目录候选禁止自动接受。
- 新增家族、舰艇级别、改进型、原型和具体型号的范围判断。
- 新增 Canonical ID 建议和分项评分理由。
- 新增搜索结果 JSON 缓存与内容哈希清单。
- 新增 `resolve-fixture` 和 `resolve-one` 命令。
- 新增离线 T-34 测试样本、解析测试和 CI 门禁。

## 1.3.0

- 为全部目录项生成带目录命名空间的稳定 Candidate ID。
- 新增 Unicode 名称标准化和候选 Slug 规则。
- 新增跨目录同名歧义队列，避免错误合并同名不同物。
- 新增按目录组推断领域、类别和时代的初步分类。
- 新增 `candidates` 和 `ambiguity-report` 命令。
- 新增人工 CSV 导入、来源记录和外部 ID 保留机制。
- 新增 Wikidata 与 MediaWiki 搜索适配器，解析逻辑可离线测试。
- 新增 CSV 模板、v1.3 实体解析文档和 CI 验证。

## 1.2.0

- 新增 MkDocs Material 知识库网站。
- 新增规范实体详情页、领域索引、时代索引和全量目录页面。
- 新增 `ckb site` 命令。
- 新增 GitHub Pages 自动构建与部署工作流。
- 新增网站生成测试。

## 1.1.0

- 增加 502 条目录候选的加载、统计、重复和状态审计。
- 增加来源登记表审计。
- 增加按项目 Profile 裁剪的 JSON Bundle 与内容哈希。
- 增加 `catalog-audit`、`source-audit` 和 `build --profile` 命令。
- 增加目录、来源和《destory》Bundle 测试。

## 1.0.0-bootstrap

- 初始化独立 CKB 仓库。
- 固化用户批准的范围和信息边界。
- 建立核心实体、体验模型和来源模型。
- 建立全时代建设目录。
- 建立 JSON 校验、SQLite、Markdown 和项目裁剪输出。
- 建立首批种子实体和自动测试。
