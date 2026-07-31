# v1.6.1 Batch 09 - Magazine model design audit

## Decision

Magazine is modeled as a `component` entity type, not as a new top-level weapon or ammunition type. The ontology already uses `component` as a relationship endpoint for engines, and a magazine is a physical feeding component with its own identity, source boundary and lifecycle.

The concrete class is `Magazine`, with subclasses such as `BoxMagazine`, `DrumMagazine`, `Clip` and `Belt` reserved for evidence-backed distinctions.

## Boundary decisions

- A cartridge is the ammunition entity; a magazine is a physical feeding component that holds or presents cartridges.
- A clip, belt or drum is not silently collapsed into a box magazine.
- `ammunition_capacity` remains a weapon claim when the source publishes a weapon-level capacity. A component profile may also carry its own capacity when the source describes that component. The two claims are not automatically merged.
- A named interface relation is directional: `weapon --accepts_magazine--> component`. Its inverse is `magazine_accepted_by`; it is not symmetric and not transitive.
- Compatibility requires an explicit named-interface or model-specific source statement. Same calibre, similar dimensions or visual similarity alone does not create the relation.
- The first sample is a Thompson wartime box-magazine pattern, linked to the existing Thompson M1A1 entity using the National Army Museum's explicit wartime box-magazine and capacity statement. The qualifier preserves the family-level scope.

## Rejected alternatives

- A symmetric generic `compatible_with` predicate was rejected because it would permit unsupported component-to-weapon and component-to-component edges.
- A top-level `magazine` entity type was rejected because it would duplicate the physical-component boundary and require parallel endpoint rules.
- Automatic compatibility from `caliber_designation` or `ammunition_capacity` was rejected; these are descriptive claims, not interface proofs.

## Safety boundary

This batch models public identification and compatibility metadata only. It does not describe loading procedures, manufacturing, ammunition construction, attack operation or gameplay balance.
