from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json

@dataclass(slots=True)
class Entity:
    id: str
    entity_type: str
    identity: dict[str, Any]
    classification: dict[str, Any]
    provenance: dict[str, Any]
    relationships: list[dict[str, Any]] = field(default_factory=list)
    technical: dict[str, Any] | None = None
    experience_profile: dict[str, Any] | None = None
    gameplay: dict[str, Any] | None = None
    rights: dict[str, Any] | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def name_en(self) -> str: return str(self.identity.get("canonical_name_en", ""))
    @property
    def name_zh(self) -> str: return str(self.identity.get("canonical_name_zh", ""))
    @property
    def aliases(self) -> list[str]: return [str(x) for x in self.identity.get("aliases", [])]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Entity":
        return cls(id=data["id"], entity_type=data["entity_type"], identity=data["identity"],
            classification=data["classification"], provenance=data["provenance"],
            relationships=data.get("relationships", []), technical=data.get("technical"),
            experience_profile=data.get("experience_profile"), gameplay=data.get("gameplay"),
            rights=data.get("rights"), raw=data)

def load_entities(root: Path) -> list[Entity]:
    entities=[]
    for path in sorted(root.rglob("*.json")):
        data=json.loads(path.read_text(encoding="utf-8"))
        rows=data if isinstance(data,list) else [data]
        for item in rows:
            if isinstance(item,dict) and "id" in item and "entity_type" in item:
                entities.append(Entity.from_dict(item))
    return entities
