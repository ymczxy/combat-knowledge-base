# v1.6.0 Batch 10：Godot 加载器与运行时契约

## 目标

为 Batch 09 的 `ckb_destory_runtime.json` 与 `ckb-lock.json` 提供最小 Godot 4 加载器，并在进入游戏前验证版本、哈希、实体顺序和资源清单。

本批不实现游戏平衡、自动选型或现实性能推演。

## 文件

```text
examples/godot/CKBRuntimeBundle.gd
src/ckb/runtime_contract.py
```

## 构建与契约验证

```bash
PYTHONPATH=src python -m ckb.godot_bundle \
  --profile data/curated/destory/build_profile.json \
  --output exports/godot \
  --fail-on-error

PYTHONPATH=src python -m ckb.runtime_contract \
  --bundle exports/godot/ckb_destory_runtime.json \
  --lock exports/godot/ckb-lock.json \
  --fail-on-error
```

Python契约验证器检查：

- Lock版本；
- Bundle格式、格式版本和Schema版本；
- Lock与Bundle manifest镜像字段；
- Bundle文件名；
- 实际Bundle文件SHA-256；
- Payload SHA-256；
- 精确实体顺序；
- 单一资源清单项；
- Bundle内部来源、配置和输入claim引用。

## Godot 加载

```gdscript
var runtime := CKBRuntimeBundle.load_locked(
    "res://data/ckb_destory_runtime.json",
    "res://data/ckb-lock.json",
)
if runtime == null:
    return

for entity_id in runtime.entity_ids():
    var configurations := runtime.list_configurations(entity_id)
    for configuration in configurations:
        print(entity_id, " -> ", configuration)
```

查询某个配置：

```gdscript
var entity_id := "ckb:platform:ground:challenger_2"
var configurations := runtime.list_configurations(entity_id)
var configuration_id := str(configurations[0]["configuration_id"])
var claims := runtime.get_claims_for_configuration(entity_id, configuration_id)
var metrics := runtime.get_metrics_for_configuration(entity_id, configuration_id)
```

调用方必须明确传入`configuration_id`。加载器不会自动选择“默认”“最佳”“最新”或“最适合游戏”的配置。

## Godot 运行时门禁

`CKBRuntimeBundle.load_locked()`在建立索引前验证：

- JSON根节点为对象；
- Lock、格式和Schema版本受支持；
- Lock字段与Bundle manifest一致；
- Bundle实际文件SHA-256与Lock一致；
- 资源清单文件名和哈希一致；
- `entity_ids`顺序与Bundle实体顺序一致；
- 实体ID、配置ID和来源ref没有缺失或重复。

加载失败返回`null`并通过`push_error()`报告原因。

## 来源引用

技术声明和派生指标只保存整数`source_refs`。Godot侧通过：

```gdscript
var urls := runtime.resolve_source_refs(claim["source_refs"])
```

解析为URL列表。加载器不下载网页，不读取来源正文，也不在运行时重新解释研究材料。

## 当前验证边界

CI已经：

- 用Python生成真实Bundle与Lock；
- 对正确与篡改文件执行契约测试；
- 验证实体顺序、资源清单和版本门禁；
- 静态检查GDScript加载器暴露的方法和禁止的自动配置选择接口。

当前CI环境没有安装Godot可执行文件，因此本批不声称已完成Godot headless语法运行。后续应在实际《destory》Godot工程中增加headless加载冒烟测试。
