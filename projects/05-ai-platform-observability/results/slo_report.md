# Executed SLO report

See architecture SLO definitions. Window is this complete experiment; traffic is synthetic.

```json
{
  "objectives": {
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
  },
  "incident": {
    "rates": {
      "5": 99.99999999999991,
      "30": 99.99999999999991,
      "60": 99.99999999999991,
      "360": 16.66666666666665
    },
    "page": true,
    "ticket": true
  },
  "recovery": {
    "rates": {
      "5": 0.0,
      "30": 0.0,
      "60": 0.0,
      "360": 0.0
    },
    "page": false,
    "ticket": false
  }
}
```
