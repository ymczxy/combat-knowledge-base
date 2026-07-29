from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import re


_PREDICATE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_ALLOWED_STATUSES = {"active", "experimental", "deprecated"}


@dataclass(frozen=True, slots=True)
class PredicateDefinition:
    name: str
    labels: dict[str, str] = field(default_factory=dict)
    description: dict[str, str] = field(default_factory=dict)
    inverse: str | None = None
    symmetric: bool = False
    transitive: bool = False
    source_entity_types: tuple[str, ...] = ()
    target_entity_types: tuple[str, ...] = ()
    source_classes: tuple[str, ...] = ()
    target_classes: tuple[str, ...] = ()
    status: str = "active"

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "PredicateDefinition":
        inverse = data.get("inverse")
        return cls(
            name=str(data["name"]),
            labels={str(key): str(value) for key, value in dict(data.get("labels", {})).items()},
            description={str(key): str(value) for key, value in dict(data.get("description", {})).items()},
            inverse=str(inverse) if inverse is not None else None,
            symmetric=bool(data.get("symmetric", False)),
            transitive=bool(data.get("transitive", False)),
            source_entity_types=tuple(str(value) for value in data.get("source_entity_types", [])),
            target_entity_types=tuple(str(value) for value in data.get("target_entity_types", [])),
            source_classes=tuple(str(value) for value in data.get("source_classes", [])),
            target_classes=tuple(str(value) for value in data.get("target_classes", [])),
            status=str(data.get("status", "active")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "labels": self.labels,
            "description": self.description,
            "inverse": self.inverse,
            "symmetric": self.symmetric,
            "transitive": self.transitive,
            "source_entity_types": list(self.source_entity_types),
            "target_entity_types": list(self.target_entity_types),
            "source_classes": list(self.source_classes),
            "target_classes": list(self.target_classes),
            "status": self.status,
        }


class PredicateRegistry:
    def __init__(self, definitions: Iterable[PredicateDefinition], version: str = "1.0"):
        self.version = version
        self.rows = list(definitions)
        self.definitions: dict[str, PredicateDefinition] = {}
        self.duplicate_names: set[str] = set()
        for definition in self.rows:
            if definition.name in self.definitions:
                self.duplicate_names.add(definition.name)
            else:
                self.definitions[definition.name] = definition

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any] | list[Mapping[str, Any]]) -> "PredicateRegistry":
        if isinstance(payload, list):
            rows = payload
            version = "1.0"
        else:
            rows = payload.get("predicates", [])
            version = str(payload.get("registry_version", "1.0"))
        return cls((PredicateDefinition.from_dict(row) for row in rows), version=version)

    def get(self, name: str) -> PredicateDefinition | None:
        return self.definitions.get(name)

    def inverse_of(self, name: str) -> str | None:
        definition = self.get(name)
        if definition is None:
            return None
        if definition.symmetric:
            return definition.name
        return definition.inverse

    def validate(self) -> list[str]:
        errors: list[str] = []
        for name in sorted(self.duplicate_names):
            errors.append(f"predicate:{name}: duplicate definition")

        for definition in self.rows:
            prefix = f"predicate:{definition.name}"
            if not _PREDICATE_PATTERN.fullmatch(definition.name):
                errors.append(f"{prefix}: invalid predicate name")
            if definition.status not in _ALLOWED_STATUSES:
                errors.append(f"{prefix}: invalid status {definition.status}")
            if not definition.labels.get("en") or not definition.labels.get("zh"):
                errors.append(f"{prefix}: labels.en and labels.zh are required")
            if definition.symmetric and definition.inverse not in {None, definition.name}:
                errors.append(f"{prefix}: symmetric predicate cannot use a different inverse")
            if definition.inverse is not None:
                inverse = self.get(definition.inverse)
                if inverse is None:
                    errors.append(f"{prefix}: missing inverse predicate {definition.inverse}")
                elif inverse.inverse != definition.name and not (
                    definition.symmetric and inverse.name == definition.name
                ):
                    errors.append(
                        f"{prefix}: inverse {definition.inverse} does not point back to {definition.name}"
                    )
        return errors

    def validate_relationship(
        self,
        relationship: Any,
        entities: Mapping[str, Any],
        *,
        strict_unknown: bool = True,
    ) -> list[str]:
        definition = self.get(str(relationship.predicate))
        if definition is None:
            return (
                [f"{relationship.id}: unknown predicate {relationship.predicate}"]
                if strict_unknown
                else []
            )

        errors: list[str] = []
        source = entities.get(str(relationship.source_id))
        target = entities.get(str(relationship.target_id))
        if source is None or target is None:
            return errors

        if definition.source_entity_types and source.entity_type not in definition.source_entity_types:
            errors.append(
                f"{relationship.id}: predicate {definition.name} rejects source entity_type "
                f"{source.entity_type}; expected one of {list(definition.source_entity_types)}"
            )
        if definition.target_entity_types and target.entity_type not in definition.target_entity_types:
            errors.append(
                f"{relationship.id}: predicate {definition.name} rejects target entity_type "
                f"{target.entity_type}; expected one of {list(definition.target_entity_types)}"
            )

        source_class = str(source.classification.get("class", ""))
        target_class = str(target.classification.get("class", ""))
        if definition.source_classes and source_class not in definition.source_classes:
            errors.append(
                f"{relationship.id}: predicate {definition.name} rejects source class "
                f"{source_class}; expected one of {list(definition.source_classes)}"
            )
        if definition.target_classes and target_class not in definition.target_classes:
            errors.append(
                f"{relationship.id}: predicate {definition.name} rejects target class "
                f"{target_class}; expected one of {list(definition.target_classes)}"
            )
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "registry_version": self.version,
            "predicate_count": len(self.definitions),
            "predicates": [definition.to_dict() for definition in self.rows],
        }


def load_predicate_registry(path: Path) -> PredicateRegistry:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, (dict, list)):
        raise ValueError(f"Predicate registry must be an object or array: {path}")
    return PredicateRegistry.from_dict(payload)
