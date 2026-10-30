# Failure analysis

Synthetic closed-world diagnostic tags; multiple tags may apply. A synthesis tag also includes incomplete reference-fact recall. Retrieval misses can be partial. Conflicts use authored relationships/category labels, not automatic semantic inference.

## Retrieval miss

Observed: 2 tagged rows. Engineering action: Inspect passage qrels; tune K/chunks and test dense/hybrid retrieval.

Examples: f04 (q11, fixture), f08 (q05, fixture)

## Relevant evidence retrieved but not used

Observed: 1 tagged rows. Engineering action: Audit evidence budget and selection; rerank with authority constraints.

Examples: bm25-q07 (q07, bm25)

## Incorrect answer synthesis

Observed: 33 tagged rows. Engineering action: Check reference-fact completeness and contradiction handling; expand independently reviewed claim coverage.

Examples: bm25-q01 (q01, bm25), bm25-q02 (q02, bm25), bm25-q04 (q04, bm25), bm25-q05 (q05, bm25), bm25-q06 (q06, bm25)

## Unsupported claim

Observed: 3 tagged rows. Engineering action: Require claim/evidence entailment review; abstain on unsupported additions.

Examples: f03 (q13, fixture), f04 (q11, fixture), f05 (q05, fixture)

## Incorrect citation

Observed: 3 tagged rows. Engineering action: Verify each cited passage is retrieved and supports its attached claim.

Examples: f02 (q05, fixture), f03 (q13, fixture), f05 (q05, fixture)

## Conflicting evidence

Observed: 3 tagged rows. Engineering action: Surface conflicting active sources; route to owner; abstain until resolved.

Examples: bm25-q07 (q07, bm25), f05 (q05, fixture), f07 (q12, fixture)

## Stale source

Observed: 2 tagged rows. Engineering action: Apply effective-date/status filters before retrieval, retain stale sources for adversarial tests.

Examples: f05 (q05, fixture), f08 (q05, fixture)

## Missing evidence / failure to abstain

Observed: 2 tagged rows. Engineering action: Add calibrated answerability checks and clarification for ambiguous questions.

Examples: f03 (q13, fixture), f07 (q12, fixture)
