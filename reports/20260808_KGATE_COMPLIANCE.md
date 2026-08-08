# K-GATE-COMPLIANCE — R38 판정 게이트 준수 검사

- 날짜: 2026-08-08 · **판정: COMPLIANT**
- 자기검증 통과 · 위반 없음 (게이트 기록 5건)
- 정책: READ-ONLY · 벤치 원본 무수정 · DB 미접촉

## 1. 게이트 모듈 자기검증

**전부 통과** (8개 검사)

| 검사 | 계산값 | 기대값 | 통과 |
|---|---|---|---|
| null_ge3(5) vs 20260730 측정 | 0.11362355 | 0.1137 | O |
| null_ge3(15) vs 20260730 측정 | 0.30360662 | 0.3036 | O |
| p_single_ge3 해석값 | 0.02383408 | 0.02383408 | O |
| pmf 합 = 1 | 1.0 | 1.0 | O |
| n50 SE | 0.044881 | 0.044881 | O |
| n50 단일 MDD | 0.124403 | 0.124403 | O |
| n50·K10 선택보정 p95 | 0.16 | 0.16 | O |
| win26/mix0.8 재판정 | NOISE_SELECTION_CONFIRMED | NOISE_SELECTION_CONFIRMED | O |

자기검증이 하는 일: null 을 초기하분포로 계산한 값이 2026-07-30 몬테카를로
측정치와 일치하는지, 눈금 수치가 재현되는지, 그리고 **적용상수 win26/mix0.8 이
다시 넣어도 `NOISE_SELECTION_CONFIRMED` 로 판정되는지** 확인한다.
이 중 하나라도 깨지면 게이트를 쓰는 모든 판정을 신뢰할 수 없다.

## 2. 벤치마크 준수 현황

- 검사 파일: **192**개 (읽기 성공 192)
- 비교·선택 주장 포함: **138**개
- `decision_gate` 기록됨: **5**개
- legacy 면제(오늘 스냅샷): **132**개
- **위반: 0개**

위반 없음.

## 3. R38 요약

모든 튜닝·비교 도구는 판정 전에 다음을 호출하고 결과를 벤치 JSON 의
`decision_gate` 키에 넣는다.

```python
from tools.k_gate import gate_block

payload["decision_gate"] = gate_block(
    n=200, k_cells=9, delta=0.012, metric="ge3",
    holdout_value=0.118, label="short_decay 스윕",
)
```

`actionable` 이 False 면 그 판정은 **차이 없음**으로 보고한다. 등급은 네 가지다.

| 등급 | 뜻 |
|---|---|
| DECIDABLE | 선택보정 임계를 넘음 → 차이 주장 가능 |
| SELECTION_SUSPECT | K셀 탐색 잡음 범위 안 → 근거 불충분 |
| UNDECIDABLE | 단일비교 최소검출차 미달 → 주장 불가 |
| NOISE_SELECTION_CONFIRMED | 홀드아웃이 null 구간으로 붕괴 → 폐기 |

## 4. 한계

- 비교성 판정은 **키 이름 기반 휴리스틱**이다. 이름이 특이한 벤치는 놓칠 수 있다.
  현재 탐지 단서: delta, vs_base, vs_null, vs_baseline, vs_pin, best, candidate, grid, n_cells, sweep, holdout, tune_, improve
- 원자료 덤프(`*_raw.json` · `bench_id` 가 `-RAW` 로 끝남 · `raw_data:true`)는 면제한다.
  아무것도 주장하지 않는 측정치 저장소이기 때문이다.
- legacy 면제는 최초 실행 시점의 스냅샷이다. 면제된 벤치의 과거 주장은
  `reports/20260808_KSTAT_DECISION_GATE.md` 의 소급감사를 참고하라.
- 이 도구는 게이트 기록 **유무**만 본다. 기록된 `n`·`k_cells` 가 정직한지는
  검증하지 않는다. 특히 `k_cells` 를 실제 탐색량보다 작게 적으면 임계가 느슨해진다.

근거 원본: `docs/benchmarks/20260808_KGATE_COMPLIANCE.json`
