# Executed failure analysis

Every row is measured synthetic traffic. Triggers are exact configuration values. Warm-up is excluded. No automatic production remediation is implemented.

## healthy

Trigger: `{"case": "supported", "delay": 0.008}`. Expected: 200 with supported answer.

Measured outcomes and changed metrics:
```json
{
  "requests": 90,
  "transport_success": 90,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.017162374999998065,
  "p95": 0.02058629199996176,
  "p99": 0.020903416999999536,
  "client_p50": 0.02415908299997227,
  "client_p95": 0.03079475000004095,
  "client_p99": 0.03163729199991394,
  "provider_p95": 0.015415791999998874,
  "retries": 0,
  "attempts": 90,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.014400000000000027,
  "input_tokens": 9000,
  "output_tokens": 2700,
  "slo": {
    "availability": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    },
    "latency": {
      "good": 90,
      "total": 90,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 0,
      "remaining": 4.5000000000000036,
      "consumption": 0.0
    },
    "quality": {
      "good": 90,
      "total": 90,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 0,
      "remaining": 4.5000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `10906a3d0e745721e4191e5b9b974592` in traces-run-0.json.

Operational response: Observe baseline.

## latency_spike

Trigger: `{"case": "supported", "delay": 0.09}`. Expected: 200 with provider latency above 80 ms.

Measured outcomes and changed metrics:
```json
{
  "requests": 90,
  "transport_success": 90,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.09927683400007936,
  "p95": 0.10671062500000517,
  "p99": 0.1079912919999515,
  "client_p50": 0.10785804199997528,
  "client_p95": 0.11502895900002841,
  "client_p99": 0.1164256250000335,
  "provider_p95": 0.10162962499998685,
  "retries": 0,
  "attempts": 90,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.014400000000000027,
  "input_tokens": 9000,
  "output_tokens": 2700,
  "slo": {
    "availability": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    },
    "latency": {
      "good": 0,
      "total": 90,
      "target": 0.95,
      "sli": 0.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 90,
      "remaining": -85.5,
      "consumption": 19.999999999999986
    },
    "quality": {
      "good": 90,
      "total": 90,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 0,
      "remaining": 4.5000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `a2ec814e0fe83b3ecccb39d3c5fe79a1` in traces-run-0.json.

Operational response: Inspect provider spans; reduce admission or route after cost review.

## timeout

Trigger: `{"case": "supported", "delay": 0.02, "timeouts": 3}`. Expected: 503 after three timed-out billed attempts.

Measured outcomes and changed metrics:
```json
{
  "requests": 90,
  "transport_success": 0,
  "error_rate": 1.0,
  "quality_failure_rate": null,
  "p50": 0.08230600000001687,
  "p95": 0.09159070800001246,
  "p99": 0.09764399999994566,
  "client_p50": 0.09089429200002996,
  "client_p95": 0.1046344589999535,
  "client_p99": 0.10882966600001964,
  "provider_p95": 0.08718008399989685,
  "retries": 180,
  "attempts": 270,
  "retry_amplification": 3.0,
  "fallbacks": 0,
  "cost": 0.02700000000000006,
  "input_tokens": 27000,
  "output_tokens": 0,
  "slo": {
    "availability": {
      "good": 0,
      "total": 90,
      "target": 0.99,
      "sli": 0.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 90,
      "remaining": -89.1,
      "consumption": 99.99999999999991
    },
    "latency": {
      "good": 4,
      "total": 90,
      "target": 0.95,
      "sli": 0.044444444444444446,
      "allowed_bad": 4.5000000000000036,
      "bad": 86,
      "remaining": -81.5,
      "consumption": 19.111111111111097
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
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `fb1c517a3cd1743395612b1245f06289` in traces-run-0.json.

Operational response: Inspect timeout attempts; avoid unlimited retries.

## retry_amplification

Trigger: `{"case": "supported", "delay": 0.012, "timeouts": 2}`. Expected: 200 after two timeouts.

Measured outcomes and changed metrics:
```json
{
  "requests": 90,
  "transport_success": 90,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.05318762500007779,
  "p95": 0.06160825000006298,
  "p99": 0.06219066699998166,
  "client_p50": 0.06343962500000089,
  "client_p95": 0.06987370899992129,
  "client_p99": 0.1191139170000497,
  "provider_p95": 0.056495125000083135,
  "retries": 180,
  "attempts": 270,
  "retry_amplification": 3.0,
  "fallbacks": 0,
  "cost": 0.03239999999999995,
  "input_tokens": 27000,
  "output_tokens": 2700,
  "slo": {
    "availability": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    },
    "latency": {
      "good": 86,
      "total": 90,
      "target": 0.95,
      "sli": 0.9555555555555556,
      "allowed_bad": 4.5000000000000036,
      "bad": 4,
      "remaining": 0.5000000000000036,
      "consumption": 0.8888888888888882
    },
    "quality": {
      "good": 90,
      "total": 90,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 0,
      "remaining": 4.5000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `e4b7565b21d0738777998e4469358782` in traces-run-0.json.

Operational response: Reduce retry budget; compare attempt cost.

## fallback

Trigger: `{"case": "supported", "delay": 0.02, "timeouts": 2, "fallback": true}`. Expected: 200 on third attempt using higher-priced fallback.

Measured outcomes and changed metrics:
```json
{
  "requests": 90,
  "transport_success": 90,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.09254479200001242,
  "p95": 0.10089279199996781,
  "p99": 0.10347987499994815,
  "client_p50": 0.100487249999901,
  "client_p95": 0.10884375000000546,
  "client_p99": 0.11434304199997314,
  "provider_p95": 0.09556804199985436,
  "retries": 90,
  "attempts": 270,
  "retry_amplification": 3.0,
  "fallbacks": 90,
  "cost": 0.07559999999999993,
  "input_tokens": 27000,
  "output_tokens": 2700,
  "slo": {
    "availability": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    },
    "latency": {
      "good": 0,
      "total": 90,
      "target": 0.95,
      "sli": 0.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 90,
      "remaining": -85.5,
      "consumption": 19.999999999999986
    },
    "quality": {
      "good": 90,
      "total": 90,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 0,
      "remaining": 4.5000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `c99e00292f11cac3c99ac9ea1812980b` in traces-run-0.json.

Operational response: Assess latency and cost before routing more traffic.

## unsupported

Trigger: `{"case": "unsupported", "delay": 0.008}`. Expected: 200 with quality failure.

Measured outcomes and changed metrics:
```json
{
  "requests": 90,
  "transport_success": 90,
  "error_rate": 0.0,
  "quality_failure_rate": 1.0,
  "p50": 0.015804125000045133,
  "p95": 0.01890679200005252,
  "p99": 0.01997766700003467,
  "client_p50": 0.021717958000067483,
  "client_p95": 0.02960425000003397,
  "client_p99": 0.032502874999977394,
  "provider_p95": 0.013575083999967319,
  "retries": 0,
  "attempts": 90,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.014400000000000027,
  "input_tokens": 9000,
  "output_tokens": 2700,
  "slo": {
    "availability": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    },
    "latency": {
      "good": 90,
      "total": 90,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 0,
      "remaining": 4.5000000000000036,
      "consumption": 0.0
    },
    "quality": {
      "good": 0,
      "total": 90,
      "target": 0.95,
      "sli": 0.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 90,
      "remaining": -85.5,
      "consumption": 19.999999999999986
    },
    "cost": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `044551cca65e3008e806a5982824b71c` in traces-run-0.json.

Operational response: Hold answer delivery and repair evidence policy.

## citation_degradation

Trigger: `{"case": "wrong_citation", "delay": 0.008}`. Expected: 200 with quality failure.

Measured outcomes and changed metrics:
```json
{
  "requests": 90,
  "transport_success": 90,
  "error_rate": 0.0,
  "quality_failure_rate": 1.0,
  "p50": 0.016254042000014124,
  "p95": 0.019242915999939214,
  "p99": 0.020109499999989566,
  "client_p50": 0.02299516699997639,
  "client_p95": 0.03472049999993487,
  "client_p99": 0.035468082999955186,
  "provider_p95": 0.015283958999930292,
  "retries": 0,
  "attempts": 90,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.014400000000000027,
  "input_tokens": 9000,
  "output_tokens": 2700,
  "slo": {
    "availability": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    },
    "latency": {
      "good": 90,
      "total": 90,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 0,
      "remaining": 4.5000000000000036,
      "consumption": 0.0
    },
    "quality": {
      "good": 0,
      "total": 90,
      "target": 0.95,
      "sli": 0.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 90,
      "remaining": -85.5,
      "consumption": 19.999999999999986
    },
    "cost": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `78d5d37c5ee8587fa759cccd71c4264f` in traces-run-0.json.

Operational response: Validate citations before response.

## tenant_cost_spike

Trigger: `{"case": "supported", "delay": 0.008, "tokens": 3000}`. Expected: higher primary input usage attributed to tenant-b.

Measured outcomes and changed metrics:
```json
{
  "requests": 90,
  "transport_success": 90,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.01581795900006,
  "p95": 0.02034466700001758,
  "p99": 0.020849875000067186,
  "client_p50": 0.021848166000040692,
  "client_p95": 0.02645258300003661,
  "client_p99": 0.027984000000060405,
  "provider_p95": 0.01410887500003355,
  "retries": 0,
  "attempts": 90,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.2754000000000002,
  "input_tokens": 270000,
  "output_tokens": 2700,
  "slo": {
    "availability": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    },
    "latency": {
      "good": 90,
      "total": 90,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 0,
      "remaining": 4.5000000000000036,
      "consumption": 0.0
    },
    "quality": {
      "good": 90,
      "total": 90,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 0,
      "remaining": 4.5000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 0,
      "total": 90,
      "target": 0.99,
      "sli": 0.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 90,
      "remaining": -89.1,
      "consumption": 99.99999999999991
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `687f9e8323d8050b12cd1e8ab4778807` in traces-run-0.json.

Operational response: Investigate tenant records; enforce a production quota.

## mixed_incident

Trigger: `{"case": "incorrect", "delay": 0.02, "mixed": true}`. Expected: even sequence 503; odd sequence 200 with quality failure.

Measured outcomes and changed metrics:
```json
{
  "requests": 90,
  "transport_success": 45,
  "error_rate": 0.5,
  "quality_failure_rate": 1.0,
  "p50": 0.03187908300003528,
  "p95": 0.08234079199996813,
  "p99": 0.09246891700001925,
  "client_p50": 0.03713712500007205,
  "client_p95": 0.08788512499995704,
  "client_p99": 0.09817483300003005,
  "provider_p95": 0.07790979199978665,
  "retries": 90,
  "attempts": 180,
  "retry_amplification": 2.0,
  "fallbacks": 0,
  "cost": 0.02070000000000003,
  "input_tokens": 18000,
  "output_tokens": 1350,
  "slo": {
    "availability": {
      "good": 45,
      "total": 90,
      "target": 0.99,
      "sli": 0.5,
      "allowed_bad": 0.9000000000000008,
      "bad": 45,
      "remaining": -44.1,
      "consumption": 49.99999999999996
    },
    "latency": {
      "good": 67,
      "total": 90,
      "target": 0.95,
      "sli": 0.7444444444444445,
      "allowed_bad": 4.5000000000000036,
      "bad": 23,
      "remaining": -18.499999999999996,
      "consumption": 5.111111111111107
    },
    "quality": {
      "good": 0,
      "total": 45,
      "target": 0.95,
      "sli": 0.0,
      "allowed_bad": 2.2500000000000018,
      "bad": 45,
      "remaining": -42.75,
      "consumption": 19.999999999999986
    },
    "cost": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `b4e5a3c5e5760b57bd0ac2bd4a3e7058` in traces-run-0.json.

Operational response: Correlate quality with availability; roll back the offending change.

## recovery

Trigger: `{"case": "supported", "delay": 0.008}`. Expected: healthy decisions resume; historical budget consumption remains.

Measured outcomes and changed metrics:
```json
{
  "requests": 90,
  "transport_success": 90,
  "error_rate": 0.0,
  "quality_failure_rate": 0.0,
  "p50": 0.015626582999971106,
  "p95": 0.020066833999976552,
  "p99": 0.0210570839999491,
  "client_p50": 0.021627125000009073,
  "client_p95": 0.03316679199997452,
  "client_p99": 0.0641409999999496,
  "provider_p95": 0.015811459000019568,
  "retries": 0,
  "attempts": 90,
  "retry_amplification": 1.0,
  "fallbacks": 0,
  "cost": 0.014400000000000027,
  "input_tokens": 9000,
  "output_tokens": 2700,
  "slo": {
    "availability": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    },
    "latency": {
      "good": 90,
      "total": 90,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 0,
      "remaining": 4.5000000000000036,
      "consumption": 0.0
    },
    "quality": {
      "good": 90,
      "total": 90,
      "target": 0.95,
      "sli": 1.0,
      "allowed_bad": 4.5000000000000036,
      "bad": 0,
      "remaining": 4.5000000000000036,
      "consumption": 0.0
    },
    "cost": {
      "good": 90,
      "total": 90,
      "target": 0.99,
      "sli": 1.0,
      "allowed_bad": 0.9000000000000008,
      "bad": 0,
      "remaining": 0.9000000000000008,
      "consumption": 0.0
    }
  }
}
```

Measured scenario throughput is in scenario_comparison.csv.

Trace: `53ed3ec908620173fc837dd28b77304a` in traces-run-0.json.

Operational response: Check trailing windows before resolving incident.
