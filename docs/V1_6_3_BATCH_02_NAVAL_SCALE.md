# v1.6.3 Batch 02 — scaled naval class/vessel/system graph

The batch expands the original Arleigh Burke slice into three independently
source-checked naval class graphs:

- Arleigh Burke class with SPY-1D and Mk 41;
- Daring/Type 45 class with HMS Daring, WR-21, SAMPSON, Sea Viper and Royal Navy;
- Virginia class with USS Virginia, public nuclear-propulsion summary,
  AN/BPS-16(V)4, Tomahawk and U.S. Navy.

`member_of_class` / `has_vessel` is a dedicated, typed predicate pair. It
prevents named-vessel service facts from being pooled into class-level
specifications.
