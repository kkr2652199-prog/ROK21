# K-PAST-LEARN-TUNE-SOFT — SOFT 스윕 (2026-08-08)

- **판정:** `KEEP_BASE`
- 시드고정 base(w0.12/cap3.0): ge3=**0.12** mean=**1.78**
- WIRE참고(unseeded): ge3=0.14 mean=1.58
- 최적후보: w=**0.12** cap=**3.0** · ge3=**0.12** mean=**1.78**
- Δge3=**0.0** · Δmean=**0.0** (vs 시드고정 base)
- applied=`False` · ASSOC OFF · 상수적용·fusion n200 = 형 GO

## Top5 (ge3→mean)

| w | cap | ge3 | mean | Δge3 |
|---|-----|-----|------|------|
| 0.0 | 1.5 | 0.12 | 1.78 | 0.0 |
| 0.0 | 3.0 | 0.12 | 1.78 | 0.0 |
| 0.0 | 5.0 | 0.12 | 1.78 | 0.0 |
| 0.06 | 1.5 | 0.12 | 1.78 | 0.0 |
| 0.06 | 3.0 | 0.12 | 1.78 | 0.0 |

## 발견

- 15셀 **전부 동일** (ge3 0.12 / mean 1.78) → soft conf 노브는 시드고정 n50에서 **발권 번호 변경 없음**
- 1차 unseeded “w0.06/cap5.0 ge3=0.18” 는 **RNG 잡음** (엔진 `random.choices` · 동결 미수정)
- env 튜닝키: `K_PAST_LEARN_SOFT_WEIGHT` / `K_PAST_LEARN_SOFT_CAP` (상수 미변경)
- 다음 튜닝축: **engine 생성단**(윈도우/가중) — soft rerank만으로는 부족

- tool: `tools/_k_past_learn_tune_soft.py`
