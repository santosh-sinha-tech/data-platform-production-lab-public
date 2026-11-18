# Executed synthetic provider benchmark

Mode: full; runs: 3; requests: 900; concurrency: 4.

Measured with HTTPX ASGI transport in one Python process. No network or commercial model performance claims.

Each run has one excluded warm-up, then ten equally sized scenarios in lifecycle order. Seed shuffles sequence IDs within each scenario. Provider delays are in config/scenarios.json.

Client p50/p95/p99 measure the full HTTPX ASGI round trip including parsing and middleware, without a real network. Other latency is application execution time including semaphore wait, excluding HTTP parsing and middleware. Throughput uses measured client batch wall time. Nearest-rank percentiles; aggregate percentiles pool observations.

```json

{
  "requests": 900,
  "transport_success": 765,
  "error_rate": 0.15000000000000002,
  "quality_failure_rate": 0.29411764705882354,
  "p50": 0.0210570839999491,
  "p95": 0.100134624999896,
  "p99": 0.10564445799991518,
  "throughput": 68.203862744985,
  "client_p50": 0.031016499999964253,
  "client_p95": 0.10884375000000546,
  "client_p99": 0.11452837500007718,
  "provider_p95": 0.0949876670000549,
  "retries": 540,
  "attempts": 1530,
  "retry_amplification": 1.7,
  "fallbacks": 90,
  "cost": 0.5031000000000013,
  "input_tokens": 414000,
  "output_tokens": 22950,
  "slo": {
    "availability": {
      "good": 765,
      "total": 900,
      "target": 0.99,
      "sli": 0.85,
      "allowed_bad": 9.000000000000007,
      "bad": 135,
      "remaining": -126.0,
      "consumption": 14.999999999999988
    },
    "latency": {
      "good": 607,
      "total": 900,
      "target": 0.95,
      "sli": 0.6744444444444444,
      "allowed_bad": 45.00000000000004,
      "bad": 293,
      "remaining": -247.99999999999994,
      "consumption": 6.511111111111105
    },
    "quality": {
      "good": 540,
      "total": 765,
      "target": 0.95,
      "sli": 0.7058823529411765,
      "allowed_bad": 38.250000000000036,
      "bad": 225,
      "remaining": -186.74999999999997,
      "consumption": 5.882352941176465
    },
    "cost": {
      "good": 810,
      "total": 900,
      "target": 0.99,
      "sli": 0.9,
      "allowed_bad": 9.000000000000007,
      "bad": 90,
      "remaining": -81.0,
      "consumption": 9.999999999999993
    }
  }
}

```

## Independent-run variability

```json

{
  "throughput": {
    "mean": 68.20708369858141,
    "stdev": 0.5727401338090653
  },
  "p95": {
    "mean": 0.10002856966665756,
    "stdev": 0.0011490134015220944
  },
  "p99": {
    "mean": 0.10356461100002434,
    "stdev": 0.00364053843426043
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

First scheduled token emission seconds: [0.015178708000007646, 0.011698165999973753, 0.01662008399989645]. ASGI buffers the stream; this is not client-observed TTFT.

## Constraints

Wall times vary with scheduler and host load. Fixture decisions, attempt counts, and costs are deterministic; IDs and timing are intentionally variable. Small samples do not establish production tail latency.
