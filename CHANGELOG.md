# Changelog

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
