extends Node

const RuntimeBundleScript = preload("res://CKBRuntimeBundle.gd")
const QueryScript = preload("res://CKBQuery.gd")
const REPORT_PATH := "res://artifacts/godot_domain_runtime_smoke.json"

const CASES := [
    {
        "name": "aviation",
        "bundle": "res://data/aviation/ckb_destory_aviation_runtime.json",
        "lock": "res://data/aviation/ckb-aviation-lock.json",
        "entity_count": 9,
        "relationship_count": 7,
        "query": "Spitfire",
        "query_id": "ckb:platform:air:spitfire_mk_i",
        "relation_source": "ckb:platform:air:spitfire_mk_i",
        "relation_predicate": "uses_ammunition",
        "relation_target": "ckb:ammunition:cartridge:303_british",
    },
    {
        "name": "naval",
        "bundle": "res://data/naval/ckb_destory_naval_runtime.json",
        "lock": "res://data/naval/ckb-naval-lock.json",
        "entity_count": 20,
        "relationship_count": 17,
        "query": "AN/BQQ-10",
        "query_id": "ckb:component:sensor:an_bqq_10_arci",
        "relation_source": "ckb:weapon:naval:mk_45_mod_4_5_inch_gun",
        "relation_predicate": "uses_ammunition",
        "relation_target": "ckb:ammunition:naval:5_inch_62_conventional_round_family",
    },
    {
        "name": "integrated_systems",
        "bundle": "res://data/integrated/ckb_destory_integrated_systems_runtime.json",
        "lock": "res://data/integrated/ckb-integrated-systems-lock.json",
        "entity_count": 16,
        "relationship_count": 10,
        "query": "PATRIOT air and missile defense system",
        "query_id": "ckb:system:air_defense:patriot",
        "relation_source": "ckb:weapon:artillery:m777a2_howitzer",
        "relation_predicate": "uses_ammunition",
        "relation_target": "ckb:ammunition:artillery:m795_155mm_projectile",
    },
]


func _ready() -> void:
    var errors: Array[String] = []
    var reports: Array[Dictionary] = []
    for case_value in CASES:
        var case: Dictionary = case_value
        var report := _run_case(case, errors)
        reports.append(report)

    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://artifacts"))
    var payload := {
        "passed": errors.is_empty(),
        "engine": Engine.get_version_info(),
        "cases": reports,
        "errors": errors,
    }
    var report_file := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
    if report_file == null:
        errors.append("Unable to open domain-runtime report path.")
    else:
        report_file.store_string(JSON.stringify(payload, "  "))

    var passed := errors.is_empty()
    print("CKB_GODOT_DOMAIN_RUNTIME_SMOKE_RESULT=", "PASS" if passed else "FAIL")
    for error in errors:
        push_error(error)
    get_tree().quit(0 if passed else 1)


func _run_case(case: Dictionary, errors: Array[String]) -> Dictionary:
    var case_name := str(case["name"])
    var runtime: Variant = RuntimeBundleScript.load_locked(
        str(case["bundle"]),
        str(case["lock"]),
    )
    if runtime == null:
        errors.append("%s: locked Bundle could not be loaded." % case_name)
        return {"name": case_name, "passed": false}

    var manifest: Dictionary = runtime.manifest
    _expect(
        int(manifest.get("entity_count", -1)) == int(case["entity_count"]),
        "%s: entity count mismatch." % case_name,
        errors,
    )
    _expect(
        int(manifest.get("relationship_assertion_count", -1))
            == int(case["relationship_count"]),
        "%s: relationship count mismatch." % case_name,
        errors,
    )
    _expect(
        manifest.get("boundaries", {}).get("contains_game_balance", true) == false,
        "%s: gameplay balance boundary is not false." % case_name,
        errors,
    )

    var query = QueryScript.new(runtime)
    var search_results: Array = query.search(str(case["query"]), "", "", 10)
    _expect(search_results.size() == 1, "%s: expected one search result." % case_name, errors)
    if search_results.size() == 1:
        _expect(
            str(search_results[0].get("id", "")) == str(case["query_id"]),
            "%s: search returned the wrong entity." % case_name,
            errors,
        )

    var relation_results: Array = query.related(
        str(case["relation_source"]),
        str(case["relation_predicate"]),
        "out",
    )
    _expect(
        relation_results.size() == 1,
        "%s: expected one bounded relationship result." % case_name,
        errors,
    )
    if relation_results.size() == 1:
        _expect(
            str(relation_results[0].get("target_id", "")) == str(case["relation_target"]),
            "%s: relationship returned the wrong target." % case_name,
            errors,
        )
        _expect(
            relation_results[0].get("provenance", {}).get("sources", []).size() >= 2,
            "%s: relationship does not retain two source references." % case_name,
            errors,
        )

    var source_entity: Dictionary = query.get_entity(str(case["relation_source"]))
    var technical_claims: Array = source_entity.get("technical_claims", [])
    _expect(
        not technical_claims.is_empty(),
        "%s: source entity has no runtime technical claims." % case_name,
        errors,
    )
    var resolved_sources := PackedStringArray()
    if not technical_claims.is_empty():
        resolved_sources = query.resolve_source_refs(technical_claims[0].get("source_refs", []))
    _expect(
        not resolved_sources.is_empty(),
        "%s: technical evidence did not resolve to source URLs." % case_name,
        errors,
    )

    return {
        "name": case_name,
        "profile_id": manifest.get("profile_id", ""),
        "entity_count": manifest.get("entity_count", 0),
        "relationship_count": manifest.get("relationship_assertion_count", 0),
        "technical_claim_count": manifest.get("technical_claim_count", 0),
        "source_ref_count": manifest.get("source_ref_count", 0),
        "query_result_count": search_results.size(),
        "relation_result_count": relation_results.size(),
        "resolved_source_count": resolved_sources.size(),
    }


func _expect(condition: bool, message: String, errors: Array[String]) -> void:
    if not condition:
        errors.append(message)
