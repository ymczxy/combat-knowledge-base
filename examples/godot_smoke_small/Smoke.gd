extends Control

const RuntimeBundleScript = preload("res://CKBRuntimeBundle.gd")
const BUNDLE_PATH := "res://data/ckb_destory_small_arms_runtime.json"
const LOCK_PATH := "res://data/ckb-small-arms-lock.json"
const SCREENSHOT_PATH := "res://artifacts/godot_small_arms_smoke.png"
const REPORT_PATH := "res://artifacts/godot_small_arms_smoke.json"

var _status_label: Label


func _ready() -> void:
    _status_label = Label.new()
    _status_label.position = Vector2(60, 60)
    _status_label.add_theme_font_size_override("font_size", 28)
    add_child(_status_label)
    call_deferred("_run_smoke")


func _run_smoke() -> void:
    var errors: Array[String] = []
    var runtime: Variant = RuntimeBundleScript.load_locked(BUNDLE_PATH, LOCK_PATH)
    if runtime == null:
        errors.append("small-arms Bundle and Lock could not be loaded")
    else:
        var ids: PackedStringArray = runtime.entity_ids()
        _expect(ids.size() == 5, "expected 5 entities, got %d" % ids.size(), errors)
        _expect(int(runtime.manifest.get("technical_claim_count", -1)) == 32, "expected 32 technical claims", errors)
        _expect(int(runtime.manifest.get("derived_metric_count", -1)) == 0, "expected 0 derived metrics", errors)
        var m2_configurations: Array = runtime.list_configurations("ckb:weapon:firearm:m2_browning")
        var ammo_configurations: Array = runtime.list_configurations("ckb:ammunition:cartridge:12_7x99")
        _expect(m2_configurations.size() > 0, "M2 configuration list is empty", errors)
        _expect(ammo_configurations.size() > 0, "12.7 x 99 configuration list is empty", errors)
        var m2_configuration_id := str(m2_configurations[0].get("configuration_id", "")) if m2_configurations.size() > 0 else ""
        var ammo_configuration_id := str(ammo_configurations[0].get("configuration_id", "")) if ammo_configurations.size() > 0 else ""
        var m2_claims: Array = runtime.get_claims_for_configuration("ckb:weapon:firearm:m2_browning", m2_configuration_id)
        var ammo_claims: Array = runtime.get_claims_for_configuration("ckb:ammunition:cartridge:12_7x99", ammo_configuration_id)
        _expect(m2_claims.size() > 0, "M2 claim query returned no rows", errors)
        _expect(ammo_claims.size() > 0, "12.7 x 99 claim query returned no rows", errors)
        if m2_claims.size() > 0:
            _expect(runtime.resolve_source_refs(m2_claims[0].get("source_refs", [])).size() > 0, "M2 source resolution failed", errors)
    var passed := errors.is_empty()
    _status_label.text = "CKB SMALL ARMS RUNTIME: PASS" if passed else "CKB SMALL ARMS RUNTIME: FAIL"
    _status_label.add_theme_color_override("font_color", Color(0.3, 0.9, 0.6) if passed else Color(1.0, 0.3, 0.3))
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://artifacts"))
    var report := {"passed": passed, "errors": errors, "entity_ids": runtime.entity_ids() if runtime != null else []}
    var report_file := FileAccess.open(REPORT_PATH, FileAccess.WRITE)
    if report_file != null:
        report_file.store_string(JSON.stringify(report, "  "))
    await RenderingServer.frame_post_draw
    var image: Image = get_viewport().get_texture().get_image()
    if image.save_png(SCREENSHOT_PATH) != OK:
        passed = false
    print("CKB_GODOT_SMALL_ARMS_SMOKE_RESULT=", "PASS" if passed else "FAIL")
    get_tree().quit(0 if passed else 1)


func _expect(condition: bool, message: String, errors: Array[String]) -> void:
    if not condition:
        errors.append(message)
