# Pre-publication review: repeatability, scale, fairness and cost

Review date: 22 October 2026. The original single-run example remains historical evidence. This review adds five independent quick runs and five independent medium runs; no timed samples were excluded. Nothing has been pushed or published.

## 1. Repeatability

Each repetition starts a fresh Python process and JVM and regenerates both layouts. Runs were sequential, with no intentional concurrent benchmark/build workload. The quick configuration retains one warmup and five measured rounds; medium uses two warmups and five measured rounds, for each query/layout. In total: 300 measured query executions plus 90 warmup executions across ten independent applications. Fresh JVMs do not clear filesystem caches or guarantee complete JIT steady state. Additional bucket audits occur before warmups, so use the new batch for repeatability conclusions rather than treating the historical single-run report as the same complete protocol.

The tables summarize independent run medians, not a pool of all iteration samples. CV = sample standard deviation / mean of the five per-run medians. Within-run IQRs and every paired median/saving are retained in CSV; original reports retain every timed sample. A positive saving favors compaction. Five applications provide descriptive evidence, not a significance test or confidence interval.

### Quick: five independent applications

| Query | Fragmented median of run medians s [min–max]; CV | Compacted median of run medians s [min–max]; CV | Median paired saving s [min–max] | Compaction favored |
|---|---|---|---|---|
| full_aggregation | 0.222184 [0.210778–0.262690]; 9.3% | 0.171406 [0.143062–0.180419]; 8.8% | 0.053230 [0.030359–0.101108] | 5/5 |
| selective | 0.235738 [0.211302–0.262137]; 9.2% | 0.150683 [0.137673–0.173902]; 11.2% | 0.087475 [0.063973–0.109395] | 5/5 |
| partition_pruned | 0.134099 [0.131366–0.137137]; 1.6% | 0.114735 [0.108830–0.122978]; 4.6% | 0.017111 [0.011121–0.028307] | 5/5 |

[Aggregate JSON](repeatability-quick/summary.json), [run medians and within-run IQRs](repeatability-quick/run-medians.csv), and [full summary](repeatability-quick/summary.md). Each repetition directory preserves its config, report JSON/Markdown, raw samples and plans, including complete executed scan metadata.

### Medium: five independent applications

| Query | Fragmented median of run medians s [min–max]; CV | Compacted median of run medians s [min–max]; CV | Median paired saving s [min–max] | Compaction favored |
|---|---|---|---|---|
| full_aggregation | 1.203422 [1.130572–1.216982]; 3.3% | 0.797380 [0.711435–0.815057]; 6.8% | 0.409342 [0.388365–0.428917] | 5/5 |
| selective | 0.972250 [0.937171–0.988070]; 2.2% | 0.561558 [0.499460–0.569901]; 5.2% | 0.411420 [0.396365–0.437711] | 5/5 |
| partition_pruned | 0.375059 [0.365888–0.377952]; 1.3% | 0.232615 [0.226834–0.238487]; 2.4% | 0.140663 [0.134351–0.147915] | 5/5 |

[Aggregate JSON](repeatability-medium/summary.json), [run medians and within-run IQRs](repeatability-medium/run-medians.csv), and [full summary](repeatability-medium/summary.md). Each repetition directory preserves its config, report JSON/Markdown, raw samples and plans, including complete executed scan metadata.

Interpretation: compaction had a lower median in every query/run in these two batches. Quick-run absolute savings remain small and variable; the original single-run millisecond differences should not be presented as stable constants. The medium batch shows the same direction at hundreds-of-MB scale. This supports the observed local layout effect, without establishing a universal benefit or isolating file count as the only cause.

## 2. Actual achieved scale and resources

| Workload | Rows per layout | Fragmented files | Compacted files | Fragmented Parquet bytes | Compacted Parquet bytes |
|---|---:|---:|---:|---:|---:|
| Quick | 60,000 | 48 | 4 | 1587154 | 1498477–1498500 |
| Medium | 12,000,000 | 256 | 16 | 311016365 | 293014730 |

The medium workload achieved approximately 311 MB fragmented and 293 MB compacted (decimal MB), per layout, about 6.1% different in total bytes. This meets the hundreds-of-MB validation goal without changing compression or schema. File lengths are filesystem measurements, not runtime I/O counters. Small compacted-byte variations across quick runs reflect physical write-order/encoding variability; logical checksums remain identical.

Environment: Apple Silicon Mac16,1 with 16 GiB host RAM; Docker Engine 28.3.2/Linux aarch64. Container limits: 2 CPU equivalents and 4 GiB RAM; Spark local[2], 1 GiB driver heap, Python 3.11.11, Spark 3.5.8, Java 17.0.20.1. All ten reports record matching runtime/resource settings. One medium-run Docker sample showed 1.034 GiB / 4 GiB memory and 153.52% CPU; this is a point-in-time sample, not measured peak memory. All five medium runs completed without OOM. Five medium repetitions retain roughly 3 GB of data plus small logs; generated data remain ignored. Docker bind-mounted local storage and OS caches are part of this environment.

The medium config is 12 million rows with nominal 256/16 files. The previous 5-million-row large example was superseded by an optional 40-million-row large config so workload naming remains ordered; the 40-million-row config was not executed and needs a separate resource review. Quick defaults are unchanged.

## 3. Fair-comparison audit

All ten runs passed source-to-layout row counts, integer cents totals and two salted row-hash sums, plus identical schema, bucket row counts, bucket directory names, query checksums, runtime versions, resource limits and relevant Spark settings. Fingerprints remain probabilistic, not exact multiset proof. Both layouts use four event_bucket partitions and Snappy Parquet. Full and selective queries share the same predicates/aggregations in code; the pruning query selects event_bucket=0, with 15,000 quick / 3,000,000 medium rows per bucket.

Complete logical/physical explain structures match within each layout pair after generated expression/plan IDs and input file URIs are normalized. All five runs within each workload also share the same normalized plan hash per query. Read schemas, filters, exchanges and partition expressions are preserved. Original plan text and untruncated event-log scan metadata are archived.

An initial medium aggregate audit correctly stopped because Spark truncated the displayed DataFilters string at different characters as expression IDs grew (for example, confirmed appeared as con... versus c...). Full Spark event metadata retained the complete identical filter. The corrected auditor compares complete scan metadata for every warmup/measured execution and restores that field only for text comparison. Regression tests confirm changed filter values still fail. Both five-run audits then passed on the original reports/logs; no benchmark timings were changed or rerun to select a better result.

| Workload / query | Fragmented scan-partition proxy | Compacted scan-partition proxy |
|---|---:|---:|
| Quick / full_aggregation | 2 | 2 |
| Quick / selective | 2 | 2 |
| Quick / partition_pruned | 2 | 1 |
| Medium / full_aggregation | 11 | 3 |
| Medium / selective | 11 | 3 |
| Medium / partition_pruned | 3 | 2 |

These are planned scan RDD partitions, not executed task counts. Matching operator plans do not imply identical scan work. Quick full/selective queries both have two planned scan partitions despite a 12-fold file-count difference; scheduling extra scan partitions cannot explain all of that difference. The medium layout changes scan packing substantially. More generally, file opens/footer work, bytes, compression/encoding, row ordering and row-group statistics, partition pruning, scheduling and shuffle costs may all contribute. No per-query causal decomposition was measured. Keep the conclusion at physical-layout effects rather than file count alone.

## 4. Processing-time break-even boundary

The model amortizes one rewrite processing time C against future per-query processing-time savings S: ceil(C/S), only when S > 0. It assumes stable future savings and equal compute capacity. Its supplied hourly rate is a simple time-to-currency conversion; default zero yields no monetary conclusion. It does not yet account for deployment infrastructure pricing/billing, object-store requests, idle/shared capacity or recurring compaction costs. It is not a cloud profitability model.

| Workload | Measured one-rewrite time range s |
|---|---:|
| Quick | 1.194918–1.494752 |
| Medium | 14.276823–16.068048 |

For recurring maintenance, sum all rewrite costs over an explicit horizon and compare them with frequency-weighted savings across the actual read workload, then apply actual infrastructure/request pricing and billing granularity separately. A single-run break-even count is not a maintenance recommendation. The repeatability evidence qualifies any original single-run threshold.

## Verification and reproduction

Final Docker build: PASS. Expanded pytest suite: **37 passed in 12.70 seconds**. Corrected audit of all original quick and medium reports in the pinned container: PASS. Median/CSV and plan-hash cross-checks: PASS. Project 01 remains unchanged.

```bash
cd projects/02-small-files-performance-lab
docker compose build
docker compose run --rm lab python -m pytest -q
docker compose run --rm lab python -m small_files.repeatability --config config/quick.json --repeats 5
docker compose run --rm lab python -m small_files.repeatability --config config/medium.json --repeats 5
```

Cold-cache experiments, host-activity isolation, more independent runs, randomized query order, query-level runtime-metric attribution, distributed/cloud/object-store validation and recurring-maintenance billing analysis remain unexecuted. The optional 40-million-row large config remains unexecuted. No push or publication was performed.
