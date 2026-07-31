# v2.0 Migration and Compatibility Rules

v2.0 freezes the canonical entity envelope, predicate endpoint semantics, technical normalization contract, and `ckb.godot.runtime` Bundle/Lock contract.

Compatibility rules:

- Existing `ckb.godot.runtime` format version 1 and schema version 1.0 remain readable.
- Legacy Bundles without `relationships` are interpreted as containing an empty relationship list; new Bundles always emit the field and lock its order.
- Embedded entity relationships are not silently promoted. They require an explicit independent assertion with provenance and review status.
- Unknown source fields are preserved during migration and never used to infer a new canonical fact.
- Rollback means restoring the previous Bundle/Lock pair and release snapshot as a pair; locked artifacts are never overwritten in place.

The machine-readable policy is exposed by `ckb.compatibility.migration_policy()`.
