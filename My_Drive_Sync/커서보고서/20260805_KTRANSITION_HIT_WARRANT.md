# K-TRANSITION-HIT-WARRANT — D_N→D_{N+1} 적중 명분 카탈로그 (2026-08-05)

> READ-ONLY · wire=False · **당첨확률↑ 클레임 금지** · 설명 라벨 비율만

- **판정:** `CATALOG`
- range N=101~1234 · n_draws=**1134** · n_numbers=**6804**
- transition_log rows=**1134** (sim_k=2)

## 라벨 정의

| 라벨 | 의미 |
|------|------|
| carry | ∈ D_N ∩ D_{N+1} |
| trans_top15 | ∈ transition top15 (유사≥2 next-freq) |
| struct_consec | D_{N+1} 내 연속쌍 소속 |
| struct_zone_*/odd/even | 소속 속성 (단독으로는 explained 아님) |
| unexplained | primary 명분 없음 |

## 전수 비율 (번호 단위)

- explained_any_primary=**0.545121** (3709/6804)
- unexplained=**0.454879** (3095)
- carry=**0.13639**
- trans_top15=**0.333039** (null≈0.333333)
- struct_consec=**0.210758**

## primary 조합 (explained 내부)

- `trans_top15`: count=1519 · share=0.409544
- `struct_consec`: count=873 · share=0.235373
- `carry`: count=469 · share=0.126449
- `struct_consec|trans_top15`: count=389 · share=0.10488
- `carry|trans_top15`: count=287 · share=0.077379
- `carry|struct_consec`: count=101 · share=0.027231
- `carry|struct_consec|trans_top15`: count=71 · share=0.019143

## 구간별 explained_rate

- early/mid/late = 0.533069 / 0.563933 / 0.53836
- max_gap=**0.030864** · stable=**True**

## spot 1234→1235

- D_N=`[1, 15, 19, 31, 35, 43]`
- D_N1=`[6, 7, 11, 15, 39, 43]`
- carry=`[15, 43]`
- 6: ['struct_consec', 'struct_zone_L', 'struct_even']
- 7: ['trans_top15', 'struct_consec', 'struct_zone_L', 'struct_odd'] rank=14
- 11: ['struct_zone_L', 'struct_odd', 'unexplained']
- 15: ['carry', 'trans_top15', 'struct_zone_L', 'struct_odd'] rank=7
- 39: ['struct_zone_H', 'struct_odd', 'unexplained']
- 43: ['carry', 'struct_zone_H', 'struct_odd']

## 해석 (과장 금지)

- 본 카탈로그는 「다음 회 번호가 어떤 서술로 붙는가」비율이다.
- trans_top15 비율이 null(15/45)과 비슷하면 **전이 top15는 배포 예측력이 없다** (COLLECT mean≈2.0과 정합).
- carry/consec는 세트 구조·이월 서술 — WARRANT.md 뇌 성적과 별개.
- 패치 대비: 라벨을 **학습 로그·설명 문자열**에 붙이는 쪽부터 · 발권 가중은 형 GO.

- tool: `tools/_k_transition_hit_warrant.py`
- JSON: `docs/benchmarks/20260805_KTRANSITION_HIT_WARRANT.json`
