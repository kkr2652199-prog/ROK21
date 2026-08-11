# K-REFEREE-BY-BRAIN-WIRE

시각: 2026-08-11T15:59:51+09:00
## 판정 **WIRE_OK**

failed=[]

## knobs
```json
{
  "stat": {
    "role_ko": "과거학습감독",
    "gain": 2.5,
    "baseline": 0.8,
    "floor": 0.15,
    "set_scale": 0.75
  },
  "markov": {
    "role_ko": "선호번호감독",
    "gain": 2.5,
    "baseline": 0.8,
    "floor": 0.15,
    "set_scale": 0.75
  },
  "review": {
    "role_ko": "금액뇌감독",
    "gain": 2.5,
    "baseline": 0.8,
    "floor": 0.15,
    "set_scale": 0.75
  }
}
```

## checks
```json
{
  "engines_import": {
    "pass": true,
    "tags": [
      "stat",
      "markov",
      "review"
    ]
  },
  "cross_brain_independence": {
    "pass": true,
    "stat_score_before": 0.575,
    "stat_score_after_markov_change": 0.575
  },
  "stat_engine_local": {
    "pass": true,
    "score": 0.575
  },
  "quota_reacts_to_peer": {
    "pass": true,
    "q0": {
      "stat": 0.4166666666666667,
      "markov": 0.24999999999999992,
      "review": 0.3333333333333333
    },
    "q1": {
      "stat": 0.33557046979865773,
      "markov": 0.3959731543624161,
      "review": 0.2684563758389262
    },
    "note": "quota는 상대화 OK · set_score는 불변이어야 함"
  },
  "empty_equal": {
    "pass": true,
    "weights": {
      "stat": 0.3333333333333333,
      "markov": 0.3333333333333333,
      "review": 0.3333333333333333
    }
  },
  "kj_mirror_sync": {
    "pass": true,
    "live": {
      "stat": 0.3333333333333333,
      "markov": 0.3333333333333333,
      "review": 0.3333333333333333
    },
    "db": {
      "markov": 0.3333333333333333,
      "review": 0.3333333333333333,
      "stat": 0.3333333333333333
    }
  },
  "aux_score_set_range": {
    "pass": true,
    "score": 0.5
  }
}
```
