extends Control

const QueryScript = preload("res://CKBQuery.gd")
const BUNDLE_PATH := "res://data/ckb_destory_runtime.json"
const LOCK_PATH := "res://data/ckb-lock.json"
const REPORT_PATH := "res://artifacts/destory_integration.json"

func _ready() -> void:
    call_deferred("_run_integration")

func _run_integration() -> void:
    var checks: Array[String] = []
    var runtime: Variant = CKBRuntimeCache.load_locked(BUNDLE_PATH, LOCK_PATH)
    if runtime == null:
        checks.append("CKB Bundle/Lock rejected by the integrated cache.")
    else:
        var query = QueryScript.new(runtime)
        var sherman: Array = query.search("Sherman", "platform", "WWII", 10)
        if sherman.size() != 1:
            checks.append("Integrated query did not resolve exactly one Sherman entity.")
        if CKBRuntimeCache.cached_bundle_count() != 1:
            checks.append("Integrated cache did not retain exactly one locked Bundle.")
        var configurations: Array = runtime.list_configurations("ckb:platform:ground:m4_sherman")
        if configurations.is_empty():
            checks.append("Integrated configuration query returned no Sherman configurations.")
    var report := {
        "passed": checks.is_empty(),
        "checks": checks,
        "bundle_path": BUNDLE_PATH,
        "lock_path": LOCK_PATH,
        "cache_entries": CKBRuntimeCache.cached_bundle_count(),
        "engine": Engine.get_version_info(),
    }
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://artifacts"))
    FileAccess.open(REPORT_PATH, FileAccess.WRITE).store_string(JSON.stringify(report, "  "))
    print("CKB_DESTORY_INTEGRATION_RESULT=%s" % ("PASS" if checks.is_empty() else "FAIL"))
    get_tree().quit(0 if checks.is_empty() else 1)
