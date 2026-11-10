# Executed failure analysis

Every row is measured synthetic traffic. Triggers are exact configuration values. Warm-up is excluded. No automatic production remediation is implemented.

## healthy

Trigger: `{"case": "supported", "delay": 0.008}`. Expected: 200 with supported answer.

Measured outcomes and changed metrics:
```json
{
  "requests": 8,
  "transport_success": 8,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.013361499999973603,
  "p95": 0.015919875000008687,
  "p99": 0.015919875000008687,
  "client_p50": 0.019355791000066347,
  "client_p95": 0.022341999999980544,
  "client_p99": 0.022341999999980544,
  "provider_p95": 0.012155291999988549,
  "retries": 0,
  "attempts": 8,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.00128,
  "input_tokens": 800,
  "output_tokens": 240,
  "slo": {
    "availability": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    },
    "latency": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "quality": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `2541b04c9592b898e127b24186b756a8` in traces-run-0.json.

Operational response: Observe baseline.

## latency_spike

Trigger: `{"case": "supported", "delay": 0.09}`. Expected: 200 with provider latency above 80 ms.

Measured outcomes and changed metrics:
```json
{
  "requests": 8,
  "transport_success": 8,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.10254704199996922,
  "p95": 0.1062776250000752,
  "p99": 0.1062776250000752,
  "client_p50": 0.10944179199998416,
  "client_p95": 0.11608770800000912,
  "client_p99": 0.11608770800000912,
  "provider_p95": 0.1018426250000175,
  "retries": 0,
  "attempts": 8,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.00128,
  "input_tokens": 800,
  "output_tokens": 240,
  "slo": {
    "availability": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    },
    "latency": {
      "good": 0,
      "total": 8,
      "target": 0.95,
      "sli": 0.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 8,
      "remaining": -7.6,
      "consumption": 19.999999999999982
    },
    "quality": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `52f8a654c55ee1e323b841f3ae642d91` in traces-run-0.json.

Operational response: Inspect provider spans; reduce admission or route after cost review.

## timeout

Trigger: `{"case": "supported", "delay": 0.02, "timeouts": 3}`. Expected: 503 after three timed-out billed attempts.

Measured outcomes and changed metrics:
```json
{
  "requests": 8,
  "transport_success": 0,
  "error_rate": 1.0,
  "quality_failure_rate": null,
  "p50": 0.07498625000005177,
  "p95": 0.08837883300009253,
  "p99": 0.08837883300009253,
  "client_p50": 0.08193412499997521,
  "client_p95": 0.09881791600002998,
  "client_p99": 0.09881791600002998,
  "provider_p95": 0.08235458399997242,
  "retries": 16,
  "attempts": 24,
  "retry_amplification": 3.0,
  "fallbacks": 0,
  "cost": 0.0024,
  "input_tokens": 2400,
  "output_tokens": 0,
  "slo": {
    "availability": {
      "good": 0,
      "total": 8,
      "target": 0.99,
      "sli": 0.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 8,
      "remaining": -7.92,
      "consumption": 99.99999999999991
    },
    "latency": {
      "good": 0,
      "total": 8,
      "target": 0.95,
      "sli": 0.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 8,
      "remaining": -7.6,
      "consumption": 19.999999999999982
    },
    "quality": {
      "good": 0,
      "total": 0,
      "target": 0.95,
      "sli": null,
      "allowed_bad": 0.0,
      "bad": 0,
      "remaining": 0.0,
      "consumption": null
    },
    "cost": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `2a8de2c38e40322c2e47390a9e45f3fe` in traces-run-0.json.

Operational response: Inspect timeout attempts; avoid unlimited retries.

## retry_amplification

Trigger: `{"case": "supported", "delay": 0.012, "timeouts": 2}`. Expected: 200 after two timeouts.

Measured outcomes and changed metrics:
```json
{
  "requests": 8,
  "transport_success": 8,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.04969537500005572,
  "p95": 0.05729337500008569,
  "p99": 0.05729337500008569,
  "client_p50": 0.06324574999996457,
  "client_p95": 0.06899879200000214,
  "client_p99": 0.06899879200000214,
  "provider_p95": 0.052536541999984365,
  "retries": 16,
  "attempts": 24,
  "retry_amplification": 3.0,
  "fallbacks": 0,
  "cost": 0.00288,
  "input_tokens": 2400,
  "output_tokens": 240,
  "slo": {
    "availability": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    },
    "latency": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "quality": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `2d393c5f27f8696a063c3803eb035b12` in traces-run-0.json.

Operational response: Reduce retry budget; compare attempt cost.

## fallback

Trigger: `{"case": "supported", "delay": 0.02, "timeouts": 2, "fallback": true}`. Expected: 200 on third attempt using higher-priced fallback.

Measured outcomes and changed metrics:
```json
{
  "requests": 8,
  "transport_success": 8,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.08995987499997682,
  "p95": 0.0929958340000212,
  "p99": 0.0929958340000212,
  "client_p50": 0.09935954200000197,
  "client_p95": 0.10487204200001088,
  "client_p99": 0.10487204200001088,
  "provider_p95": 0.08640670899978886,
  "retries": 8,
  "attempts": 24,
  "retry_amplification": 3.0,
  "fallbacks": 8,
  "cost": 0.006720000000000002,
  "input_tokens": 2400,
  "output_tokens": 240,
  "slo": {
    "availability": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    },
    "latency": {
      "good": 0,
      "total": 8,
      "target": 0.95,
      "sli": 0.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 8,
      "remaining": -7.6,
      "consumption": 19.999999999999982
    },
    "quality": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `6c847738355fa2e0b72441b076b8dcc2` in traces-run-0.json.

Operational response: Assess latency and cost before routing more traffic.

## unsupported

Trigger: `{"case": "unsupported", "delay": 0.008}`. Expected: 200 with quality failure.

Measured outcomes and changed metrics:
```json
{
  "requests": 8,
  "transport_success": 8,
  "error_rate": 0.0,
  "quality_failure_rate": 1.0,
  "p50": 0.015228958999955466,
  "p95": 0.02161545900003148,
  "p99": 0.02161545900003148,
  "client_p50": 0.02710154099997908,
  "client_p95": 0.03171216699990964,
  "client_p99": 0.03171216699990964,
  "provider_p95": 0.016675833000022067,
  "retries": 0,
  "attempts": 8,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.00128,
  "input_tokens": 800,
  "output_tokens": 240,
  "slo": {
    "availability": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    },
    "latency": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "quality": {
      "good": 0,
      "total": 8,
      "target": 0.95,
      "sli": 0.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 8,
      "remaining": -7.6,
      "consumption": 19.999999999999982
    },
    "cost": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `c89cfd82347c5e1306930db212598553` in traces-run-0.json.

Operational response: Hold answer delivery and repair evidence policy.

## citation_degradation

Trigger: `{"case": "wrong_citation", "delay": 0.008}`. Expected: 200 with quality failure.

Measured outcomes and changed metrics:
```json
{
  "requests": 8,
  "transport_success": 8,
  "error_rate": 0.0,
  "quality_failure_rate": 1.0,
  "p50": 0.016623958999957722,
  "p95": 0.017848959000048126,
  "p99": 0.017848959000048126,
  "client_p50": 0.024115833999985625,
  "client_p95": 0.02551474999995662,
  "client_p99": 0.02551474999995662,
  "provider_p95": 0.012864832999980536,
  "retries": 0,
  "attempts": 8,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.00128,
  "input_tokens": 800,
  "output_tokens": 240,
  "slo": {
    "availability": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    },
    "latency": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "quality": {
      "good": 0,
      "total": 8,
      "target": 0.95,
      "sli": 0.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 8,
      "remaining": -7.6,
      "consumption": 19.999999999999982
    },
    "cost": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `70d53b8ef2a97e1ef7f2eed9b70a9baa` in traces-run-0.json.

Operational response: Validate citations before response.

## tenant_cost_spike

Trigger: `{"case": "supported", "delay": 0.008, "tokens": 3000}`. Expected: higher primary input usage attributed to tenant-b.

Measured outcomes and changed metrics:
```json
{
  "requests": 8,
  "transport_success": 8,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.014997584000070674,
  "p95": 0.01611841600004027,
  "p99": 0.01611841600004027,
  "client_p50": 0.020245917000011104,
  "client_p95": 0.02418345900002805,
  "client_p99": 0.02418345900002805,
  "provider_p95": 0.011571708000019498,
  "retries": 0,
  "attempts": 8,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.02448,
  "input_tokens": 24000,
  "output_tokens": 240,
  "slo": {
    "availability": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    },
    "latency": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "quality": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 0,
      "total": 8,
      "target": 0.99,
      "sli": 0.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 8,
      "remaining": -7.92,
      "consumption": 99.99999999999991
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `1b1d2801662c605cb92a3fc2da603dc4` in traces-run-0.json.

Operational response: Investigate tenant records; enforce a production quota.

## mixed_incident

Trigger: `{"case": "incorrect", "delay": 0.02, "mixed": true}`. Expected: even sequence 503; odd sequence 200 with quality failure.

Measured outcomes and changed metrics:
```json
{
  "requests": 8,
  "transport_success": 4,
  "error_rate": 0.5,
  "quality_failure_rate": 1.0,
  "p50": 0.03155483299997286,
  "p95": 0.08880883300003006,
  "p99": 0.08880883300003006,
  "client_p50": 0.03629441599991878,
  "client_p95": 0.09438812500002314,
  "client_p99": 0.09438812500002314,
  "provider_p95": 0.08403950000013083,
  "retries": 8,
  "attempts": 16,
  "retry_amplification": 2.0,
  "fallbacks": 0,
  "cost": 0.00184,
  "input_tokens": 1600,
  "output_tokens": 120,
  "slo": {
    "availability": {
      "good": 4,
      "total": 8,
      "target": 0.99,
      "sli": 0.5,
      "allowed_bad": 0.08000000000000007,
      "bad": 4,
      "remaining": -3.92,
      "consumption": 49.99999999999996
    },
    "latency": {
      "good": 4,
      "total": 8,
      "target": 0.95,
      "sli": 0.5,
      "allowed_bad": 0.40000000000000036,
      "bad": 4,
      "remaining": -3.5999999999999996,
      "consumption": 9.999999999999991
    },
    "quality": {
      "good": 0,
      "total": 4,
      "target": 0.95,
      "sli": 0.0,
      "allowed_bad": 0.20000000000000018,
      "bad": 4,
      "remaining": -3.8,
      "consumption": 19.999999999999982
    },
    "cost": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `4f5f0de7a6caf5a7966cc881cebf134a` in traces-run-0.json.

Operational response: Correlate quality with availability; roll back the offending change.

## recovery

Trigger: `{"case": "supported", "delay": 0.008}`. Expected: healthy decisions resume; historical budget consumption remains.

Measured outcomes and changed metrics:
```json
{
  "requests": 8,
  "transport_success": 8,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.014654458999984854,
  "p95": 0.015071999999918262,
  "p99": 0.015071999999918262,
  "client_p50": 0.019434624999917105,
  "client_p95": 0.021181915999932244,
  "client_p99": 0.021181915999932244,
  "provider_p95": 0.011250458999938928,
  "retries": 0,
  "attempts": 8,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.00128,
  "input_tokens": 800,
  "output_tokens": 240,
  "slo": {
    "availability": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    },
    "latency": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "quality": {
      "good": 8,
      "total": 8,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 0.40000000000000036,
      "bad": 0,
      "remaining": 0.40000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 8,
      "total": 8,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.08000000000000007,
      "bad": 0,
      "remaining": 0.08000000000000007,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `cf5492aed42f7df42b2867e9bdf667f2` in traces-run-0.json.

Operational response: Check trailing windows before resolving incident.
