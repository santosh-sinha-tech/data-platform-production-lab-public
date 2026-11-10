# Executed SLO report

See architecture SLO definitions. Window is this complete experiment; traffic is synthetic.

```json
{
  "objectives": {
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
