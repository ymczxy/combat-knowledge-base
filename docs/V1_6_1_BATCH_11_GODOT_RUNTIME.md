# v1.6.1 Batch 11 - Small-arms Godot Runtime sample

## Scope

This batch adds a separate `destory-small-arms` build profile, an explicit entity allow-list and a dedicated Bundle/Lock pair. It does not alter the v1.6.0 armored profile or its golden runtime snapshot.

## Runtime boundary

The sample exposes selected source-checked M2 Browning, 12.7 x 99 mm, Thompson M1A1, Thompson box-magazine and Thompson family records. Queries are limited to the entities and technical claims represented in the Bundle. Relationship structure is intentionally deferred until a later runtime contract expands it with dedicated tests.

The profile uses an empty derived-metric specification because no small-arms metric is needed for this first consumption sample. This is explicit configuration, not an implicit “best” or “latest” selection.

## Acceptance

- Bundle and Lock are generated from the small-arms profile.
- Bundle and Lock hashes validate through the runtime contract.
- Entity order is exactly the profile allow-list.
- At least one weapon and one ammunition record are queryable from the Bundle.
- The existing armored profile remains at 8 entities, 71 technical claims and 5 derived metrics.

## Safety boundary

The runtime contains public technical claims and provenance references only. It contains no loading instructions, manufacturing guidance, attack procedures or gameplay balance values.
