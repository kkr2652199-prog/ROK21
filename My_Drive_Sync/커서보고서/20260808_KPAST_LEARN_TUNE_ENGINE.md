# K-PAST-LEARN-TUNE-ENGINE — engine v2 스윕 (2026-08-08)

- **판정:** `CANDIDATE`
- 시드고정 base(v2 win52/mix0.6): ge3=**0.12** mean=**1.78**
- 최적: v2=`True` win=`26` mix=`0.8` · ge3=**0.28** mean=**1.88**
- Δge3=**0.16** · Δmean=**0.1**
- applied=False · ASSOC OFF · `random.choices` 미수정

## Top6

| v2 | win | mix | ge3 | mean | Δge3 |
|----|-----|-----|-----|------|------|
| True | 26 | 0.8 | 0.28 | 1.88 | 0.16 |
| True | 52 | 0.6 | 0.12 | 1.78 | 0.0 |
| True | 78 | 0.6 | 0.12 | 1.74 | 0.0 |
| True | 52 | 0.8 | 0.12 | 1.72 | 0.0 |
| True | 26 | 0.6 | 0.1 | 1.72 | -0.02 |
| True | 78 | 0.8 | 0.08 | 1.64 | -0.04 |

## 발견

- base(v2 win52/mix0.6) = TUNE-SOFT 시드값과 동일 (ge3 0.12 / mean 1.78) → 재현 OK
- **후보1안:** `short_win=26` · `short_mix=0.8` · ge3 **0.28** (Δ**+0.16**) mean **1.88**
- v1 control: ge3 **0.04** ≪ v2 base → v2 유지 근거
- 상수 미적용 · n50 과적합 가능 → **형 GO** 후 상수반영·(선택) fusion n200
- env: `K_STAT_ENG_SHORT_WIN=26` `K_STAT_ENG_SHORT_MIX=0.8`

- tool: `tools/_k_past_learn_tune_engine.py`
