# K-PAST-LEARN-DETAIL-KEEP — decay KEEP_BASE 확정 (2026-08-08)

- **판정:** `KEEP_BASE` · 형 GO  
- 수치 SSOT: `docs/benchmarks/20260808_KPAST_LEARN_DETAIL_KEEP.json`

---

## 초보용

- **한 일:** “decay를 바꿀까?” → **아니오, 지금 그대로** 로 확정  
- **코드:** 원래 `0.005` / `0.05` 였고, 후보 `0.01` 은 **넣지 않음**  
- **이유:** 신뢰 유튜브도·우리 시험도 “바꿔서 이긴다” 근거가 약함  
- **틀은 유지:** 최근 26회를 80% 비중으로 보는 것(FRAME)은 그대로

---

## 확정 값

| 항목 | 값 |
|------|-----|
| LONG_DECAY | **0.005** |
| SHORT_DECAY | **0.05** |
| SHORT_WIN / MIX | **26** / **0.8** (프레임) |
| 기각 후보 | L0.01 / S0.05 |

## 정책

- tipster / LSTM / ASSOC **wire 금지** 유지

## 근거

- `20260808_KPAST_LEARN_DETAIL_TUNE.json`  
- `20260808_KPAST_LEARN_YT_BENCH.json`
