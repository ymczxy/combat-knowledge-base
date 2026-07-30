class_name CKBQuery
extends RefCounted

var _runtime: RefCounted


func _init(runtime: RefCounted) -> void:
    _runtime = runtime


func search(text: String = "", entity_type: String = "", era: String = "", limit: int = 50) -> Array:
    if limit < 1:
        return []
    var needle := text.strip_edges().to_lower()
    var rows: Array = []
    for value in _runtime.entities:
        if typeof(value) != TYPE_DICTIONARY:
            continue
        var entity: Dictionary = value
        var classification: Dictionary = entity.get("classification", {})
        if not entity_type.is_empty() and str(entity.get("entity_type", "")) != entity_type:
            continue
        if not era.is_empty() and era not in classification.get("eras", []):
            continue
        if not needle.is_empty() and not _matches_text(entity, needle):
            continue
        rows.append(entity.duplicate(true))
    rows.sort_custom(_sort_entities)
    return rows.slice(0, mini(limit, rows.size()))


func get_entity(entity_id: String) -> Dictionary:
    return _runtime.get_entity(entity_id)


func list_configurations(entity_id: String) -> Array:
    return _runtime.list_configurations(entity_id)


func get_claims_for_configuration(entity_id: String, configuration_id: String) -> Array:
    return _runtime.get_claims_for_configuration(entity_id, configuration_id)


func get_metrics_for_configuration(entity_id: String, configuration_id: String) -> Array:
    return _runtime.get_metrics_for_configuration(entity_id, configuration_id)


func resolve_source_refs(refs: Array) -> PackedStringArray:
    return _runtime.resolve_source_refs(refs)


func _matches_text(entity: Dictionary, needle: String) -> bool:
    var display_name: Dictionary = entity.get("display_name", {})
    var values := PackedStringArray([
        str(entity.get("id", "")),
        str(display_name.get("en", "")),
        str(display_name.get("zh", "")),
    ])
    var classification: Dictionary = entity.get("classification", {})
    for tag in classification.get("tags", []):
        values.append(str(tag))
    for value in values:
        if value.to_lower().contains(needle):
            return true
    return false


static func _sort_entities(left: Dictionary, right: Dictionary) -> bool:
    var left_name: Dictionary = left.get("display_name", {})
    var right_name: Dictionary = right.get("display_name", {})
    var left_text := str(left_name.get("en", left.get("id", ""))).to_lower()
    var right_text := str(right_name.get("en", right.get("id", ""))).to_lower()
    if left_text == right_text:
        return str(left.get("id", "")) < str(right.get("id", ""))
    return left_text < right_text
