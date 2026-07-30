# v1.6.1 Release

## Release scope

v1.6.1 extends the CKB content layer from the armored-vehicle baseline into source-checked small arms, ammunition, feed components and explicit variant/family boundaries.

The release includes:

- 95 Canonical Entities and 54 independent Relationship Assertions;
- 20 new content batches after the original v1.6.0 baseline, with 21 total content batches in the repository snapshot;
- M2 Browning and 12.7 x 99 mm / .50 BMG source-checked records;
- a component-based Magazine model with directional `accepts_magazine` / `magazine_accepted_by` constraints;
- explicit `variant_of` / `has_variant` endpoint constraints;
- a separate 5-entity small-arms Godot Runtime Bundle and Lock;
- preservation of the locked 8-entity armored runtime profile.

## Verification

- 157 local unit tests passed;
- CKB CI workflow run 389 passed;
- Godot Linux Runtime Smoke workflow run 29 passed on Ubuntu 24.04 Linux x86_64 with Godot 4.7.1-stable;
- both armored and small-arms Bundle/Lock contracts passed;
- the small-arms smoke scene queried a weapon and ammunition entity through explicit configuration IDs and resolved source references;
- no relationship conflicts, duplicate assertion groups or unsupported numeric claims were present.

## Boundaries

The release does not claim global small-arms coverage. It contains no loading recipes, propellant or primer specifications, manufacturing instructions, attack procedures, target-selection advice or gameplay balance values. The full relationship query surface and a complete Godot plugin remain later roadmap work.
