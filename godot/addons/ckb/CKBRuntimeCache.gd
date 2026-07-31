extends Node

const RuntimeBundleScript = preload("res://CKBRuntimeBundle.gd")
var _bundles: Dictionary = {}

func load_locked(bundle_path: String, lock_path: String) -> RefCounted:
    var cache_key := "%s|%s" % [bundle_path, lock_path]
    if _bundles.has(cache_key):
        return _bundles[cache_key]
    var runtime: Variant = RuntimeBundleScript.load_locked(bundle_path, lock_path)
    if runtime == null:
        return null
    _bundles[cache_key] = runtime
    return runtime

func invalidate(bundle_path: String = "", lock_path: String = "") -> void:
    if bundle_path.is_empty() and lock_path.is_empty():
        _bundles.clear()
        return
    _bundles.erase("%s|%s" % [bundle_path, lock_path])

func cached_bundle_count() -> int:
    return _bundles.size()
