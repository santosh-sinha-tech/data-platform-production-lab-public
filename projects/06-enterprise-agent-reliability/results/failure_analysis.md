# Failure injection outcomes

All fixtures are synthetic. See scenario_comparison.csv for expected and executed outcomes.

- A: Successful multi-step; expected succeeded; 60/60 matched.
- B: Unauthorized tool; expected denied; 60/60 matched.
- C: Approval granted; expected succeeded; 60/60 matched.
- D: Approval rejected; expected failed; 60/60 matched.
- E: Approval expired; expected failed; 60/60 matched.
- F: Duplicate delivery; expected succeeded; 60/60 matched.
- G: Tool timeout; expected failed; 60/60 matched.
- H: Transient recovery; expected succeeded; 60/60 matched.
- I: Uncertain write reconciliation; expected succeeded; 60/60 matched.
- J: Process restart; expected succeeded; 60/60 matched.
- K: Cost budget; expected failed; 60/60 matched.
- L: Malicious tool output; expected succeeded; 60/60 matched.
- M: Cross-tenant approval; expected denied; 60/60 matched.
- N: Invalid response; expected failed; 60/60 matched.
- O: Partial workflow failure; expected failed; 60/60 matched.
- P: Permanent failure; expected failed; 60/60 matched.

J closes and reopens SQLite after an injected exception at the effect/receipt boundary. The subprocess kill test separately exercises real abrupt process death. I never repeats the rerun: reconciliation reads the simulator ledger. G exhausts two retries; K fails on retry cost admission. O compensates only the completed reversible ticket. Failure does not imply automatic rollback of all effects.
