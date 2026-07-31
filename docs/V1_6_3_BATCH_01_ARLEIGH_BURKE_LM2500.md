# v1.6.3 Batch 01 — Arleigh Burke / LM2500 vertical slice

This batch starts the naval expansion with a guided-missile destroyer and propulsion component:

- `ckb:platform:naval:arleigh_burke_class`
- `ckb:component:engine:ge_lm2500_marine`
- an independent, configuration-qualified `uses_engine` assertion

The platform record keeps Aegis and SPY-1 as public system-identification claims. The engine relation is class-scoped because DDG 51 flight-specific propulsion details should not be flattened into a universal claim.
