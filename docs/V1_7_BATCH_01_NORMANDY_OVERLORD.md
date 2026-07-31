# v1.7 Batch 01 — Normandy / Overlord context graph

This batch introduces the first time-place-organization-battle context graph:

- Normandy place
- Operation Overlord event
- D-Day battle
- U.S. 1st Infantry Division organization

It adds explicit `located_in`, `part_of`, and constrained `participated_in` / `organized_by` vocabulary. A deliberately rejected `organized_by` inference remains in the independent assertion store so the governance layer records why participation must not be promoted to command or organization.
