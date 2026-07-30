# v1.6.0 Batch 09：Godot 运行时 Bundle

## 目标

将 Batch 07 的标准化技术声明与 Batch 08 的可追溯派生指标打包为《destory》可直接加载的紧凑 JSON，而不把完整 CKB 主数据、审核记录或游戏平衡字段带入运行时。

## 构建

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

## Bundle 内容

运行时 Bundle 包含：

- 版本化 manifest；
- 明确排序的实体白名单；
- 实体显示名和最小分类信息；
- 配置 ID；
- 标准化数值声明与描述性声明；
- claim 引用；
- 去重后的来源 URL 索引表；
- 派生指标及其输入 claim 引用；
- 明确标记为非平衡值的体验派生档案。

不会包含：

- 完整 canonical 原始实体；
- `provenance` 审核结构；
- `rights`；
- `gameplay` 平衡字段；
- 独立来源文档正文；
- 任意自动猜测的配置合并。

## 配置与来源

每条技术声明和派生指标都带 `configuration_id`。配置标签来自声明或指标的明确 `qualifiers.configuration`；没有配置标签的声明进入实体的 `default` 配置。

来源 URL 在顶层 `source_table` 中去重，声明只保存整数 `source_refs`。派生指标保存 `input_claim_refs`，因此 Godot 侧可以从指标回溯到参与计算的技术声明，而不需要加载完整研究数据。

## Lock 文件

`ckb-lock.json` 固定：

- Profile ID；
- Bundle ID、格式与 Schema 版本；
- Bundle 文件名；
- Payload SHA-256；
- 实际 Bundle 文件 SHA-256；
- 精确实体顺序；
- 资源清单。

同一输入必须生成完全相同的 Bundle 和 Lock。任何实体、声明、单位转换、派生指标或来源索引变化都会改变哈希。

## 门禁

CI 要求：

- 8 个白名单实体全部存在；
- 实体审核状态属于 `source_checked`、`cross_checked` 或 `expert_reviewed`；
- 71 条技术声明全部进入 Bundle；
- 55 条数值声明全部标准化；
- 16 条描述性声明保留；
- 5 条派生指标全部生成；
- 所有来源引用、配置引用和输入 claim 引用有效；
- Bundle 不包含 `provenance`、`rights`、`gameplay` 或原始实体结构；
- Payload 哈希、文件哈希和 Lock 一致；
- 未知数值单位或派生指标错误直接阻断构建。

## 边界

运行时技术值仍然是公开声明或其单位换算。派生功重比不是来源原文，也不代表加速、越野能力、战斗效能或游戏平衡。游戏侧必须单独维护 `balance_data`，不得反向写入 CKB 技术事实层。
