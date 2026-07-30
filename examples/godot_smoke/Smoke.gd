extends Control

const RuntimeBundleScript = preload("res://CKBRuntimeBundle.gd")
const CHALLENGER_ID := "ckb:platform:ground:challenger_2"
const SHERMAN_ID := "ckb:platform:ground:m4_sherman"
const BUNDLE_PATH := "res://data/ckb_destory_runtime.json"
const LOCK_PATH := "res://data/ckb-lock.json"
const SCREENSHOT_PATH := "res://artifacts/godot_runtime_smoke.png"
const REPORT_PATH := "res://artifacts/godot_runtime_smoke.json"

var _content: VBoxContainer
var _status_label: Label
var _detail_labels: Array[Label] = []


func _ready() -> void:
    _build_ui()
    call_deferred("_run_smoke")


func _build_ui() -> void:
    var background: ColorRect = ColorRect.new()
    background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    background.color = Color(0.025, 0.032, 0.05, 1.0)
    add_child(background)

    var accent: ColorRect = ColorRect.new()
    accent.position = Vector2(0, 0)
    accent.size = Vector2(18, 720)
    accent.color = Color(0.16, 0.73, 0.48, 1.0)
    add_child(accent)

    var margin: MarginContainer = MarginContainer.new()
    margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
    margin.add_theme_constant_override("margin_left", 62)
    margin.add_theme_constant_override("margin_right", 62)
    margin.add_theme_constant_override("margin_top", 42)
    margin.add_theme_constant_override("margin_bottom", 38)
    add_child(margin)

    _content = VBoxContainer.new()
    _content.add_theme_constant_override("separation", 11)
    margin.add_child(_content)

    _add_text("CKB / DESTORY", 22, Color(0.48, 0.88, 0.69))
    _add_text("GODOT LINUX RUNTIME SMOKE TEST", 38, Color(0.95, 0.97, 1.0))
    _add_text("Actual engine execution · locked Bundle · explicit configuration queries", 18, Color(0.62, 0.68, 0.78))

    var separator: HSeparator = HSeparator.new()
    separator.custom_minimum_size.y = 18
    _content.add_child(separator)

    _status_label = _add_text("RUNNING…", 30, Color(1.0, 0.78, 0.28))
    for _index in range(9):
        _detail_labels.append(_add_text("", 18, Color(0.82, 0.86, 0.93)))

    var footer: Label = Label.new()
    footer.text = "The loader does not choose a default, newest, or best configuration."
    footer.add_theme_font_size_override("font_size", 16)
    footer.add_theme_color_override("font_color", Color(0.56, 0.62, 0.72))
    footer.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
    footer.size_flags_vertical = Control.SIZE_EXPAND_FILL
    _content.add_child(footer)


func _add_text(value: String, font_size: int, color: Color) -> Label:
    var label: Label = Label.new()
    label.text = value
    label.add_theme_font_size_override("font_size", font_size)
    label.add_theme_color_override("font_color", color)
    label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
    _content.add_child(label)
    return label


func _run_smoke() -> void:
    var checks: Array[String] = []
    var details: Array[String] = []
    var runtime: Variant = RuntimeBundleScript.load_locked(BUNDLE_PATH, LOCK_PATH)
    if runtime == null:
        checks.append("Bundle and lock could not be loaded by CKBRuntimeBundle.")
        await _finish(false, details, checks)
        return

    var engine_version: String = str(Engine.get_version_info().get("string", "unknown"))
    var manifest: Dictionary = runtime.manifest
    var ids: PackedStringArray = runtime.entity_ids()

    _expect(ids.size() == 8, "Expected 8 entities, got %d." % ids.size(), checks)
    _expect(int(manifest.get("technical_claim_count", -1)) == 71, "Expected 71 technical claims.", checks)
    _expect(int(manifest.get("derived_metric_count", -1)) == 5, "Expected 5 derived metrics.", checks)
    _expect(int(manifest.get("source_ref_count", -1)) == 14, "Expected 14 source references.", checks)

    var challenger_configs: Array = runtime.list_configurations(CHALLENGER_ID)
    var challenger_baseline: Dictionary = _find_configuration(challenger_configs, "baseline")
    var challenger_armour: Dictionary = _find_configuration(challenger_configs, "with add-on armour modules")
    _expect(not challenger_baseline.is_empty(), "Challenger 2 baseline configuration is missing.", checks)
    _expect(not challenger_armour.is_empty(), "Challenger 2 add-on armour configuration is missing.", checks)

    var baseline_metrics: Array = []
    var armour_metrics: Array = []
    if not challenger_baseline.is_empty():
        baseline_metrics = runtime.get_metrics_for_configuration(
            CHALLENGER_ID,
            str(challenger_baseline.get("configuration_id", "")),
        )
    if not challenger_armour.is_empty():
        armour_metrics = runtime.get_metrics_for_configuration(
            CHALLENGER_ID,
            str(challenger_armour.get("configuration_id", "")),
        )
    _expect(baseline_metrics.size() == 1, "Challenger 2 baseline metric query failed.", checks)
    _expect(armour_metrics.size() == 1, "Challenger 2 add-on armour metric query failed.", checks)

    var sherman_configs: Array = runtime.list_configurations(SHERMAN_ID)
    var sherman_e8: Dictionary = _find_configuration(sherman_configs, "M4A2E8 Sherman")
    var sherman_firefly: Dictionary = _find_configuration(sherman_configs, "M4A4 Sherman Firefly")
    _expect(not sherman_e8.is_empty(), "M4A2E8 configuration is missing.", checks)
    _expect(not sherman_firefly.is_empty(), "M4A4 Sherman Firefly configuration is missing.", checks)

    var e8_claims: Array = []
    var firefly_claims: Array = []
    if not sherman_e8.is_empty():
        e8_claims = runtime.get_claims_for_configuration(
            SHERMAN_ID,
            str(sherman_e8.get("configuration_id", "")),
        )
    if not sherman_firefly.is_empty():
        firefly_claims = runtime.get_claims_for_configuration(
            SHERMAN_ID,
            str(sherman_firefly.get("configuration_id", "")),
        )
    _expect(e8_claims.size() > 0, "M4A2E8 explicit claim query returned no rows.", checks)
    _expect(firefly_claims.size() > 0, "M4A4 Firefly explicit claim query returned no rows.", checks)

    var resolved_sources: PackedStringArray = PackedStringArray()
    if e8_claims.size() > 0:
        var first_claim: Dictionary = e8_claims[0]
        resolved_sources = runtime.resolve_source_refs(first_claim.get("source_refs", []))
    _expect(resolved_sources.size() > 0, "Source reference resolution returned no URLs.", checks)

    var baseline_value: String = _first_metric_value(baseline_metrics)
    var armour_value: String = _first_metric_value(armour_metrics)
    details = [
        "ENGINE      Godot %s · Linux x86_64" % engine_version,
        "LOCK        SHA-256, versions, resource manifest and entity order verified",
        "BUNDLE      %d entities · %d configurations" % [ids.size(), int(manifest.get("configuration_count", 0))],
        "DATA        %d technical claims · %d derived metrics · %d source refs" % [
            int(manifest.get("technical_claim_count", 0)),
            int(manifest.get("derived_metric_count", 0)),
            int(manifest.get("source_ref_count", 0)),
        ],
        "CHALLENGER  baseline: %s kW/t" % baseline_value,
        "CHALLENGER  add-on armour: %s kW/t" % armour_value,
        "SHERMAN     M4A2E8: %d explicit claims" % e8_claims.size(),
        "SHERMAN     M4A4 Firefly: %d explicit claims" % firefly_claims.size(),
        "TRACE       first sampled claim resolved to %d source URL(s)" % resolved_sources.size(),
    ]
    await _finish(checks.is_empty(), details, checks)


func _expect(condition: bool, message: String, checks: Array[String]) -> void:
    if not condition:
        checks.append(message)


func _find_configuration(configurations: Array, wanted_label: String) -> Dictionary:
    for value in configurations:
        if typeof(value) == TYPE_DICTIONARY:
            var row: Dictionary = value
            if str(row.get("label", "")) == wanted_label:
                return row
    return {}


func _first_metric_value(rows: Array) -> String:
    if rows.is_empty() or typeof(rows[0]) != TYPE_DICTIONARY:
        return "missing"
    var row: Dictionary = rows[0]
    var value: Variant = row.get("value", "missing")
    if value is Array:
        var parts: PackedStringArray = PackedStringArray()
        for item in value:
            parts.append(str(item))
        return "–".join(parts)
    return str(value)


func _finish(passed: bool, details: Array[String], errors: Array[String]) -> void:
    _status_label.text = "PASS — RUNTIME CONTRACT VERIFIED" if passed else "FAIL — RUNTIME CONTRACT REJECTED"
    _status_label.add_theme_color_override(
        "font_color",
        Color(0.30, 0.92, 0.60) if passed else Color(1.0, 0.38, 0.38),
    )

    var rendered_lines: Array[String] = []
    rendered_lines.append_array(details)
    if not errors.is_empty():
        rendered_lines.append("ERRORS      %s" % " | ".join(errors))
    for index in range(_detail_labels.size()):
        _detail_labels[index].text = rendered_lines[index] if index < rendered_lines.size() else ""

    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://artifacts"))
    var report: Dictionary = {
        "passed": passed,
        "engine": Engine.get_version_info(),
        "details": details,
        "errors": errors,
        "bundle_path": BUNDLE_PATH,
        "lock_path": LOCK_PATH,
    }
    var report_file: FileAccess = FileAccess.open(REPORT_PATH, FileAccess.WRITE)
    if report_file != null:
        report_file.store_string(JSON.stringify(report, "  "))

    await get_tree().process_frame
    await get_tree().process_frame
    await RenderingServer.frame_post_draw
    var image: Image = get_viewport().get_texture().get_image()
    var screenshot_error: Error = image.save_png(SCREENSHOT_PATH)
    if screenshot_error != OK:
        push_error("Unable to save Godot smoke-test screenshot: %s" % error_string(screenshot_error))
        passed = false
    print("CKB_GODOT_SMOKE_RESULT=", "PASS" if passed else "FAIL")
    print("CKB_GODOT_SCREENSHOT=", ProjectSettings.globalize_path(SCREENSHOT_PATH))
    get_tree().quit(0 if passed else 1)
