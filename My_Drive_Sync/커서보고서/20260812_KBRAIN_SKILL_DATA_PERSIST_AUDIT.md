# 뇌별 과거분석·예측前 DATA 저장/활용 감사

시각: 2026-08-12 · SSOT=`D:\ROK21` · DB=`data/lotto_testlotto.db` · 양산前(마지막 확정=1236) · 1237아님

## 1) 한줄 결론

| 구분 | 저장? | 예측에 활용? | 스킬별 분리? |
|------|-------|--------------|--------------|
| 원천 `lotto_draws` | ✅ | ✅ (`_get_draws_before`) | 공유(원천) |
| `testlotto_brain_learn_state` | ✅ (뇌별 1행) | ✅ (CUTOFF/`load_learn_state`) | 스키마 동일·내용만 뇌별 |
| `testlotto_brain_weights` | ✅ | ✅ referee | 뇌별 |
| `testlotto_brain_review` | ✅ (WF 위주) | ✅ CUTOFF 재생 | 뇌×회차 |
| **live click/`_auto_feedback` → review** | ❌→**L9b WIRE** | CUTOFF 공백 위험 | — |
| pool hit ledger + scatter | ✅ (L3) | ✅ repack blend (L4) | 뇌×kind×set |
| hint 스킬표 (miss/prefer/prize) | ❌ 매예측 재계산 → **L9c WIRE** | 재계산=활용 · persist 없음이었음 | 코드축만 분리 |
| `RollingSignalLearner` EMA | ❌ 메모리만 | ✅ 프로세스 내 warm | 뇌별 테이블 |
| `lotto_analysis` | 스키마만 · **행0** | 구 `feedback.py` 경로 · 본선 미사용 | — |
| `testlotto_evolve_log` | 스키마 · **행0**(현 DB) | 중복가드용 | — |

## 2) 예측 N 직전 로드 경로 (실측)

1. `lotto_draws` where `draw_no < N` (`_get_draws_before`) — **컨닝 방지 SSOT**
2. `learn_state` — as_of 있으면 `brain_review` matched/missed 재생 (CUTOFF)
3. 원장 `ledger_signal_tables` — `draw_no < N`
4. hint: `build_hint_by_brain` ← 뇌별 `HINT_SPEC_BY_BRAIN`
   - **stat** → `miss_pattern` 창52
   - **markov** → `crowd_prefer`
   - **review** → `crowd_prize`
5. (선택) pool/predictions 캐시

## 3) 결과 확정 후 쓰기 경로

| 경로 | learn_state | brain_review | ledger | skill homework |
|------|-------------|--------------|--------|----------------|
| walkforward | ✅ | ✅ | (별도) | (본턴前 없음) |
| click_feedback | ✅(guard) | **L9b✅** | ✅ L3 | **L9c✅** |
| `_auto_feedback` | ✅(guard) | **L9b✅** | ✅ L3 | **L9c✅** |

## 4) 갭 → LIST 삽입

| ID | 갭 | 심각도 | 조치 |
|----|-----|--------|------|
| **L9b** | live 피드백이 `brain_review` 미기록 → CUTOFF≠live | HIGH | **WIRE_OK** (본턴) |
| **L9c** | 스킬 hint 숙제 테이블 없음 | HIGH | **WIRE_OK** (본턴) |
| **L9d** | EMA vs ledger SSOT 문서 미고정 | MED | DOC (본턴) |
| (후순위) | 발권5 vs pool10+5 이중저장 | HIGH→L12 | 형승인 |
| (후순위) | learn_state 스키마 뇌공통 | MED | 관찰 |

## 5) 근거 파일

- `app/testlotto/learn_state_cutoff.py` · `learn_state.py`
- `app/testlotto/signal_pool.py` (`HINT_SPEC_BY_BRAIN`, `RollingSignalLearner`)
- `app/testlotto/pool_hit_ledger.py`
- `app/testlotto/brain_review_mirror.py` (L9b)
- `app/testlotto/skill_homework.py` (L9c)
- 벤치: `docs/benchmarks/20260812_KLIVE_FEEDBACK_REVIEW_MIRROR.json` · `…_KSKILL_HOMEWORK_PERSIST.json`
