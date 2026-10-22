# Independent-run repeatability validation

5 fresh Python/JVM applications. Each run generates and validates its own layouts before timing. No concurrent benchmark processes.

| Query | Fragmented median of run medians s [min–max]; CV | Compacted median of run medians s [min–max]; CV | Paired saving median s [min–max] | Runs favoring compaction |
|---|---|---|---|---|
| full_aggregation | 0.222184 [0.210778–0.262690]; 9.3% | 0.171406 [0.143062–0.180419]; 8.8% | 0.053230 [0.030359–0.101108] | 5/5 |
| selective | 0.235738 [0.211302–0.262137]; 9.2% | 0.150683 [0.137673–0.173902]; 11.2% | 0.087475 [0.063973–0.109395] | 5/5 |
| partition_pruned | 0.134099 [0.131366–0.137137]; 1.6% | 0.114735 [0.108830–0.122978]; 4.6% | 0.017111 [0.011121–0.028307] | 5/5 |

CV is sample standard deviation / mean across independent run medians. Within-run IQRs and all paired results are in run-medians.csv; individual reports preserve every raw sample. Negative savings mean compaction was slower. These are descriptive statistics, not confidence intervals.

## Fairness checks

All runs pass identical row counts, cents totals, two independent row-hash sums, schema, bucket row counts, bucket directory names, query-output checksums, relevant Spark settings and runtime/resource configuration. Hash sums remain probabilistic. Explain plans match across layouts after removing expression IDs, plan IDs and input file URIs and restoring display-truncated DataFilters from complete Spark event metadata. All executed scan metadata are compared across layouts/iterations; scan-metadata.json preserves these fields. The normalized plan check preserves operators, columns, filters, exchanges, read schemas and partition strategy; it does not claim equal physical work. Actual scan partition proxies and bytes/files are retained in summary.json.

## Interpretation and cost boundary

Layout is the intervention: file count, file sizes, row ordering, compression/encoding, footer overhead, scan packing and row-group pruning can change together. Do not attribute all elapsed-time differences solely to file count. This is a warm-storage local experiment; fresh JVMs do not clear OS caches. Host activity, JIT and fixed query order remain limitations. No significance claim or cloud extrapolation.

Break-even amortizes the processing time of one measured rewrite against assumed stable future per-query savings. It excludes cloud infrastructure pricing/billing, object-store requests, idle/shared capacity and recurring compaction cycles. A supplied hourly rate is only a compute-time conversion. Repeated maintenance must be evaluated over a horizon including every rewrite and actual workload/billing data.
