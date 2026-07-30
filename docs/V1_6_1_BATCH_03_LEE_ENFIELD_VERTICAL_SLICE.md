# v1.6.1 Batch 03 — Lee-Enfield No. 4 Mk I and .303 British

## Scope

This batch adds a complete British Second World War rifle-to-ammunition vertical slice:

- `ckb:weapon:firearm:lee_enfield_no4_mk1`
- `ckb:ammunition:cartridge:303_british`
- independent `uses_ammunition` assertion between them

## Evidence boundary

The profile is based on public collection records from the National Army Museum and Imperial War Museums, plus the C.I.P. public homologation record for the cartridge designation and rimmed-cartridge classification.

Museum catalogue wording for effective and maximum range is retained as descriptive text. The batch does not infer game damage, penetration, lethality or balance values from those statements.

## Safety boundary

The ammunition profile intentionally excludes loading recipes, propellant charges, primer specifications, manufacturing tolerances and operational attack guidance.

## Quality gates

- two source-checked entities
- one independent source-checked relationship
- at least five technical claims per entity
- technical normalization with zero unsupported numeric units
- source registry coverage for both museum institutions
- full repository CI and Godot Linux runtime regression
