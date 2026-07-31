# v2.0.0 Stable Release

v2.0.0 closes the complete approved v1.6–v2.0 roadmap boundary. It freezes the core schema, predicate endpoint semantics, canonical entity envelope, technical normalization contract, query contract 1.1, and Godot runtime Bundle/Lock compatibility contract.

The frozen content snapshot contains 187 canonical entities, 135 independent relationship assertions, 35 content batches, 123 technical profiles, and 521 technical claims. All 96 numeric claims use supported normalized units; 425 descriptive claims preserve source meaning; embedded relationships and unsupported numeric units are both zero.

The release completes consumable domain closures for armored vehicles, small arms/ammunition, aviation, naval systems, and artillery/missile/air-defense/sensor systems. It also completes all nine v1.7 context entity types and the five required outputs: equipment timelines, battle-equipment graphs, industrial chains, factory locations, and unit-organization graphs.

The v1.8 website provides relationship panels, recursively expandable graphs, timelines, maps, development lineages, battle-equipment and industrial-chain views, advanced filters, a stable local query API, and fact → assertion → source evidence traversal.

The v1.9 consumption layer provides a formal Godot `.ckb` import plugin, cache and query services, compatibility rules, upgrade/rollback fixtures, and integration in the real `destory` project. Seven Runtime profiles are reproducibly locked by content and file SHA-256 values.

The requirements-to-evidence mapping is in `V1_6_TO_V2_0_ACCEPTANCE.md`. Final release acceptance requires the complete unittest/audit/site/runtime suite, `python -m ckb.stability_gate --fail-on-error`, official Godot 4.7.1 execution, default-branch merges, and green remote CI. This scope is the approved roadmap boundary; it is not a claim that every item in the long-term 502-entry catalog has been researched.
