from pathlib import Path
import json
from .model import Entity

def render_entity(e:Entity)->str:
    exp=json.dumps(e.experience_profile,ensure_ascii=False,indent=2) if e.experience_profile else "尚未建立"
    return f"""# {e.name_zh}

- CKB ID：`{e.id}`
- 英文名：{e.name_en}
- 类别：{e.classification.get('domain')} / {e.classification.get('class')} / {e.classification.get('subclass') or '未标注'}
- 时代：{', '.join(e.classification.get('eras',[])) or '未标注'}
- 审核：{e.provenance.get('review_status')}

## 体验配置

```json
{exp}
```

> 自动生成，请勿直接编辑。
"""

def build_markdown(entities:list[Entity],output:Path)->None:
    output.mkdir(parents=True,exist_ok=True); index=["# CKB 实体索引",""]
    for e in sorted(entities,key=lambda x:(x.classification.get('domain',''),x.name_en.lower())):
        fn=e.id.replace(':','__')+'.md'; (output/fn).write_text(render_entity(e),encoding='utf-8'); index.append(f"- [{e.name_zh}]({fn}) — `{e.id}`")
    (output/'README.md').write_text('\n'.join(index)+'\n',encoding='utf-8')
