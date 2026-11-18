# Executed synthetic provider benchmark

Mode: quick; runs: 2; requests: 80; concurrency: 4.

Measured with HTTPX ASGI transport in one Python process. No network or commercial model performance claims.

Each run has one excluded warm-up, then ten equally sized scenarios in lifecycle order. Seed shuffles sequence IDs within each scenario. Provider delays are in config/scenarios.json.

Client p50/p95/p99 measure the full HTTPX ASGI round trip including parsing and middleware, without a real network. Other latency is application execution time including semaphore wait, excluding HTTP parsing and middleware. Throughput uses measured client batch wall time. Nearest-rank percentiles; aggregate percentiles pool observations.

```json

{
  "requests": 80,
  "transport_success": 68,
  "error_rate": 0.15000000000000002,
  "quality_failure_rate": 0.29411764705882354,
  "p50": 0.02161545900003148,
  "p95": 0.10254704199996922,
  "p99": 0.1062776250000752,
  "throughput": 67.65761579702743,
  "client_p50": 0.03146020800011229,
  "client_p95": 0.10944179199998416,
  "client_p99": 0.11608770800000912,
  "provider_p95": 0.10016845799998464,
  "retries": 48,
  "attempts": 136,
  "retry_amplification": 1.7,
  "fallbacks": 8,
  "cost": 0.04472000000000003,
  "input_tokens": 36800,
  "output_tokens": 2040,
  "slo": {
    "availability": {
      "good": 68,
      "total": 80,
      "target": 0.99,
      "sli": 0.85,
      "allowed_bad": 0.8000000000000007,
      "bad": 12,
      "remaining": -11.2,
      "consumption": 14.999999999999988
    },
    "latency": {
      "good": 52,
      "total": 80,
      "target": 0.95,
      "sli": 0.65,
      "allowed_bad": 4.0000000000000036,
      "bad": 28,
      "remaining": -23.999999999999996,
      "consumption": 6.999999999999994
    },
    "quality": {
      "good": 48,
      "total": 68,
      "target": 0.95,
      "sli": 0.7058823529411765,
      "allowed_bad": 3.400000000000003,
      "bad": 20,
      "remaining": -16.599999999999998,
      "consumption": 5.882352941176466
    },
    "cost": {
      "good": 72,
      "total": 80,
      "target": 0.99,
      "sli": 0.9,
      "allowed_bad": 0.8000000000000007,
      "bad": 8,
      "remaining": -7.199999999999999,
      "consumption": 9.999999999999991
    }
  }
}

```

## Independent-run variability

```json

{
  "throughput": {
    "mean": 67.69559646027619,
    "stdev": 2.2676523774960615
  },
  "p95": {
    "mean": 0.10434727150004619,
    "stdev": 0.002589690197731279
  },
  "p99": {
    "mean": 0.10441233350002221,
    "stdev": 0.0026379205371541933
  }
}

```

## Environment

```json

{
  "python": "3.11.14",
  "os": "Linux",
  "machine": "aarch64"
}

```

## Offline labeled quality

case,correct,grounded,citation,abstention,passed
supported,True,True,True,True,True
incorrect,False,False,False,True,False
unsupported,True,False,False,False,False
wrong_citation,True,True,False,True,False
missing_evidence,True,False,False,False,False
contradictory,True,False,False,False,False
stale,True,False,False,False,False
abstention,True,True,True,True,True


## Simulated streaming

First scheduled token emission seconds: [0.01494383299996116, 0.013111958999957096]. ASGI buffers the stream; this is not client-observed TTFT.

## Constraints

Wall times vary with scheduler and host load. Fixture decisions, attempt counts, and costs are deterministic; IDs and timing are intentionally variable. Small samples do not establish production tail latency.
