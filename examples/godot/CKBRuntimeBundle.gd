class_name CKBRuntimeBundle
extends RefCounted

const SUPPORTED_BUNDLE_FORMAT: String = "ckb.godot.runtime"
const SUPPORTED_FORMAT_VERSION: int = 1
const SUPPORTED_SCHEMA_VERSION: String = "1.0"
const SUPPORTED_LOCK_VERSION: int = 1

var manifest: Dictionary = {}
var source_table: Array = []
var entities: Array = []
var relationships: Array = []

var _entity_index: Dictionary = {}
var _configuration_index: Dictionary = {}
var _source_index: Dictionary = {}


static func load_locked(bundle_path: String, lock_path: String):
    var lock_result: Dictionary = _read_json_object(lock_path)
    if not bool(lock_result.get("ok", false)):
        push_error(str(lock_result.get("error", "Unable to read CKB lock file.")))
        return null

    var bundle_result: Dictionary = _read_json_object(bundle_path)
    if not bool(bundle_result.get("ok", false)):
        push_error(str(bundle_result.get("error", "Unable to read CKB runtime Bundle.")))
        return null

    var lock: Dictionary = lock_result["data"]
    var bundle: Dictionary = bundle_result["data"]
    var verification_error := _verify_file_and_versions(bundle_path, bundle, lock)
    if not verification_error.is_empty():
        push_error(verification_error)
        return null

    var runtime = new()
    var initialization_error := runtime._initialize(bundle, lock)
    if not initialization_error.is_empty():
        push_error(initialization_error)
        return null
    return runtime


static func _read_json_object(path: String) -> Dictionary:
    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        return {"ok": false, "error": "Unable to open JSON file: %s" % path}
    var parsed: Variant = JSON.parse_string(file.get_as_text())
    if parsed == null or typeof(parsed) != TYPE_DICTIONARY:
        return {"ok": false, "error": "JSON root is not an object: %s" % path}
    return {"ok": true, "data": parsed}


static func _verify_file_and_versions(
    bundle_path: String,
    bundle: Dictionary,
    lock: Dictionary,
) -> String:
    if int(lock.get("lock_version", -1)) != SUPPORTED_LOCK_VERSION:
        return "Unsupported CKB lock version."

    var manifest_value: Variant = bundle.get("manifest", {})
    if typeof(manifest_value) != TYPE_DICTIONARY:
        return "CKB runtime Bundle manifest is missing or invalid."
    var bundle_manifest: Dictionary = manifest_value

    if str(bundle_manifest.get("bundle_format", "")) != SUPPORTED_BUNDLE_FORMAT:
        return "Unsupported CKB Bundle format."
    if int(bundle_manifest.get("format_version", -1)) != SUPPORTED_FORMAT_VERSION:
        return "Unsupported CKB Bundle format version."
    if str(bundle_manifest.get("schema_version", "")) != SUPPORTED_SCHEMA_VERSION:
        return "Unsupported CKB Bundle schema version."

    var mirrored_fields := [
        "profile_id",
        "bundle_id",
        "bundle_format",
        "format_version",
        "schema_version",
        "content_sha256",
    ]
    for field_name in mirrored_fields:
        if lock.get(field_name) != bundle_manifest.get(field_name):
            return "CKB lock field does not match Bundle manifest: %s" % field_name

    if str(lock.get("bundle_filename", "")) != bundle_path.get_file():
        return "CKB lock Bundle filename does not match the loaded file."

    var file_sha256 := FileAccess.get_sha256(bundle_path)
    if file_sha256.is_empty():
        return "Unable to calculate CKB runtime Bundle SHA-256."
    if file_sha256 != str(lock.get("bundle_file_sha256", "")):
        return "CKB runtime Bundle SHA-256 does not match the lock file."

    var resources_value: Variant = lock.get("resource_manifest", [])
    if typeof(resources_value) != TYPE_ARRAY or resources_value.size() != 1:
        return "CKB lock resource manifest must contain exactly one Bundle row."
    var resource_value: Variant = resources_value[0]
    if typeof(resource_value) != TYPE_DICTIONARY:
        return "CKB lock resource manifest row is invalid."
    var resource: Dictionary = resource_value
    if str(resource.get("path", "")) != bundle_path.get_file():
        return "CKB lock resource path does not match the loaded Bundle."
    if str(resource.get("sha256", "")) != file_sha256:
        return "CKB lock resource hash does not match the loaded Bundle."
    return ""


func _initialize(bundle: Dictionary, lock: Dictionary) -> String:
    manifest = bundle.get("manifest", {})

    var source_value: Variant = bundle.get("source_table", [])
    if typeof(source_value) != TYPE_ARRAY:
        return "CKB source table must be an array."
    source_table = source_value
    for row_value in source_table:
        if typeof(row_value) != TYPE_DICTIONARY:
            return "CKB source table row must be an object."
        var row: Dictionary = row_value
        var source_ref := int(row.get("ref", -1))
        var source_url := str(row.get("url", ""))
        if source_ref < 0 or source_url.is_empty() or _source_index.has(source_ref):
            return "CKB source table contains an invalid or duplicate reference."
        _source_index[source_ref] = source_url

    var entities_value: Variant = bundle.get("entities", [])
    if typeof(entities_value) != TYPE_ARRAY:
        return "CKB entities must be an array."
    entities = entities_value

    var relationships_value: Variant = bundle.get("relationships", [])
    if typeof(relationships_value) != TYPE_ARRAY:
        return "CKB relationships must be an array."
    relationships = relationships_value
    var relationship_ids: Dictionary = {}
    for relationship_value in relationships:
        if typeof(relationship_value) != TYPE_DICTIONARY:
            return "CKB relationship row must be an object."
        var relationship: Dictionary = relationship_value
        var relationship_id := str(relationship.get("id", ""))
        if relationship_id.is_empty() or relationship_ids.has(relationship_id):
            return "CKB relationship ID is missing or duplicated."
        relationship_ids[relationship_id] = true
    var locked_relationship_ids_value: Variant = lock.get("relationship_ids", [])
    if typeof(locked_relationship_ids_value) != TYPE_ARRAY:
        return "CKB lock relationship_ids must be an array."
    var locked_relationship_ids: Array = locked_relationship_ids_value
    if locked_relationship_ids.size() != relationships.size():
        return "CKB lock relationship count does not match the Bundle."
    for index in range(relationships.size()):
        var relationship_row: Dictionary = relationships[index]
        if str(locked_relationship_ids[index]) != str(relationship_row.get("id", "")):
            return "CKB lock relationship order does not match the Bundle."

    var locked_ids_value: Variant = lock.get("entity_ids", [])
    if typeof(locked_ids_value) != TYPE_ARRAY:
        return "CKB lock entity_ids must be an array."
    var locked_ids: Array = locked_ids_value
    if locked_ids.size() != entities.size():
        return "CKB lock entity count does not match the Bundle."

    for index in range(entities.size()):
        var entity_value: Variant = entities[index]
        if typeof(entity_value) != TYPE_DICTIONARY:
            return "CKB entity row must be an object."
        var entity: Dictionary = entity_value
        var entity_id := str(entity.get("id", ""))
        if entity_id.is_empty() or _entity_index.has(entity_id):
            return "CKB entity ID is missing or duplicated."
        if str(locked_ids[index]) != entity_id:
            return "CKB lock entity order does not match the Bundle."
        _entity_index[entity_id] = entity

        var configurations_value: Variant = entity.get("configurations", [])
        if typeof(configurations_value) != TYPE_ARRAY:
            return "CKB entity configurations must be an array: %s" % entity_id
        var configuration_map: Dictionary = {}
        for configuration_value in configurations_value:
            if typeof(configuration_value) != TYPE_DICTIONARY:
                return "CKB configuration row must be an object: %s" % entity_id
            var configuration: Dictionary = configuration_value
            var configuration_id := str(configuration.get("configuration_id", ""))
            if configuration_id.is_empty() or configuration_map.has(configuration_id):
                return "CKB configuration ID is missing or duplicated: %s" % entity_id
            configuration_map[configuration_id] = configuration
        _configuration_index[entity_id] = configuration_map
    return ""


func entity_ids() -> PackedStringArray:
    var result := PackedStringArray()
    for entity_value in entities:
        var entity: Dictionary = entity_value
        result.append(str(entity.get("id", "")))
    return result


func get_entity(entity_id: String) -> Dictionary:
    var value: Variant = _entity_index.get(entity_id, {})
    return value if typeof(value) == TYPE_DICTIONARY else {}


func list_configurations(entity_id: String) -> Array:
    var entity := get_entity(entity_id)
    var value: Variant = entity.get("configurations", [])
    return value.duplicate(true) if typeof(value) == TYPE_ARRAY else []


func get_claims_for_configuration(
    entity_id: String,
    configuration_id: String,
) -> Array:
    return _rows_for_configuration(entity_id, "technical_claims", configuration_id)


func get_metrics_for_configuration(
    entity_id: String,
    configuration_id: String,
) -> Array:
    return _rows_for_configuration(entity_id, "derived_metrics", configuration_id)


func resolve_source_refs(refs: Array) -> PackedStringArray:
    var result := PackedStringArray()
    for value in refs:
        var source_ref := int(value)
        if _source_index.has(source_ref):
            result.append(str(_source_index[source_ref]))
    return result


func related(entity_id: String, predicate: String = "", direction: String = "both") -> Array:
    if direction not in ["out", "in", "both"]:
        return []
    var result: Array = []
    for relationship_value in relationships:
        if typeof(relationship_value) != TYPE_DICTIONARY:
            continue
        var relationship: Dictionary = relationship_value
        var is_out := str(relationship.get("source_id", "")) == entity_id
        var is_in := str(relationship.get("target_id", "")) == entity_id
        if (direction == "out" and not is_out) or (direction == "in" and not is_in) or (direction == "both" and not (is_out or is_in)):
            continue
        if not predicate.is_empty() and str(relationship.get("predicate", "")) != predicate:
            continue
        result.append(relationship.duplicate(true))
    return result


func _rows_for_configuration(
    entity_id: String,
    key: String,
    configuration_id: String,
) -> Array:
    if configuration_id.is_empty() or not _configuration_index.has(entity_id):
        return []
    var configuration_map: Dictionary = _configuration_index[entity_id]
    if not configuration_map.has(configuration_id):
        return []
    var entity := get_entity(entity_id)
    var rows_value: Variant = entity.get(key, [])
    if typeof(rows_value) != TYPE_ARRAY:
        return []
    var result: Array = []
    for row_value in rows_value:
        if typeof(row_value) == TYPE_DICTIONARY:
            var row: Dictionary = row_value
            if str(row.get("configuration_id", "")) == configuration_id:
                result.append(row.duplicate(true))
    return result
