# K-REFEREE-BY-BRAIN — 뇌별 독립 감독관 + 예측버그감사

시각: 2026-08-11 · 형GO · 양산前 · **1237아님** · ge3 클레임 금지

## 순서

1. **감독관 패치** (이 문서) → 2. **번호예측 버그감사** (`KBRAIN_PREDICT_BUG_AUDIT`)

## 무엇을 바꿨나

| 항목 | 구 | 신 |
|------|----|----|
| 엔진 위치 | `aux_referee` 단일 | `stat/markov/review_brain/referee.py` + `shared/referee_by_brain.py` |
| `score_set` | 3뇌 **정규화 가중** → 타뇌 성적에 종속 | **해당 뇌 learn만** → 로컬 0~1 |
| quota | 단일 GAIN 식 | 뇌별 엔진 raw 후 Σ=1 (배분만 상대화) |
| DB 시드 | 1.5/1.0/1.2 | **1/3** + init 시 sync |

## 검증

- `K-REFEREE-BY-BRAIN-WIRE` → **WIRE_OK** (교차의존0 · 미러sync · empty균등)
- `K-BRAIN-PREDICT-BUG-AUDIT` → **AUDIT_OK** fails**0** (1226~1236 · pool10/RNG/hint/peek/quota)

## 원칙

- 공유=`lotto_draws` + **자기** learn_state만
- 감독 점수(set_score)는 뇌 간 독립
- 발권 장수 배분(quota)만 3뇌 raw를 모아 정규화

## 파일

- `app/testlotto/brains/shared/referee_by_brain.py`
- `app/testlotto/brains/{stat,markov,review}_brain/referee.py`
- `app/testlotto/brains/aux_referee.py` · `learn_state.py` · `models.py`
- 벤치: `docs/benchmarks/20260811_KREFEREE_BY_BRAIN_WIRE.json` · `..._KBRAIN_PREDICT_BUG_AUDIT.json`
