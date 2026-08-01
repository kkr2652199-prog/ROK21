# K-ENGINE-UPGRADE — 전략 브리핑 (형 GO 전 의견)

📅 2026-08-01 · **코드 수정 없음** · READ-ONLY 조사  
HEAD `cf82516` · SSOT `D:\ROK21` · 포트 7021  
요청: 젠스파크 로드맵 PHASE 1~3 · Q1~Q6 의견 수렴

---

## Executive Summary

| 항목 | 커서 의견 |
|------|-----------|
| 젠스파크 진단 (입력 분포 불변) | **동의** — stat/markov/review 모두 전체·장기 평균 수렴 |
| PHASE 1 일괄 GO | **비권고** — 항목별 근거 갈림 |
| markov window=100 solo bench | **GO 가치 있음** (유일한 PHASE 1 후보) |
| stat ENGINE_V2=True | 백테 가능 · uplift **delta=0** → **보류** |
| review lookback=50 | 구현 1줄 · survey **열화** → **비권고** |
| B1 virtual draws | ge3=0.0600 FAIL → **PHASE 1 전 롤백 권고** |
| PHASE 2~3 | adj 배선 70% · auto_tune **미존재** · fusion ge3 0.06 선행 |

---

## 배경 (SSOT)

| 지표 | 값 | 출처 |
|------|-----|------|
| fused coordinator ge3 | **0.0600** | K-HIGHWAY / SIGNAL / B1 BACKTEST-100 |
| baseline ge3 | **0.1015** | PINNED_BASELINE |
| delta | **-0.0415** | |
| solo stat ge3 | **0.135** | K-HIGHWAY by_brain |
| solo markov ge3 | **0.13** | 동일 |
| solo review ge3 | **0.11** | 동일 |

**핵심:** solo brain > fused coordinator → 병목은 엔진 solo보다 **융합·쿼터·15→5 축소** 가능성 큼.

---

## Q1. PHASE 1 실현 가능성

### stat — `ENGINE_V2=True`

- **위치:** `app/testlotto/brains/stat_brain/engine.py` — `ENGINE_V2=False`, env `K_STAT_ENGINE_V2=1` 가능
- **동작:** v1 `exp(-0.02*age)` → dual-window (long decay 0.005 + short 52 decay 0.05) + cycle gap
- **백테:** `tools/_k_new_engine_stat_a1_bench.py` 존재 · `_get_draws_before` + `set_learn_as_of`
- **실측:** baseline/v2 ge3 **0.1350 = 0.1350** (`20260801_KNEW_ENGINE_STAT_A1.md`)
- **판정:** 즉시 백테 **가능** · GO uplift **없음**

### markov — 슬라이딩 100회

- **현재:** `build_transition_matrix(draws)` 전체 draws 순회 · window 파라미터 없음
- **수정:** `markov_brain/engine.py` — `draws[-100:]` 슬라이스 · `start_nums=draws[-1]` 유지
- **백테:** solo markov bench 패턴 복제 가능 · window=100 전용 벤치 **미작성**
- **판정:** 변경 작 · frozen 미침 · **solo n=200 벤치 GO 권고**

### review — lookback=50

- **API:** `repeat_rate_after_draw(draws, lookback=200)` — `draw_features.py` lookback 지원
- **호출:** `review_brain/engine.py` L17 — lookback 미전달 (default 200)
- **survey:** lookback=50 ge3=**0.1024** vs 전체 **0.1117** → **열화**
- **판정:** 구현 High · GO **비권고**

---

## Q2. 동결 토큰 충돌

| 동결 | PHASE 1 |
|------|---------|
| `random.choices` 라인 | ✅ 미변경 |
| `_get_draws_before` | ✅ 미변경 |
| `BOOST_CAPS` cap 값 | ❌ 변경 금지 |

**수정 가능:** window/decay/lookback — `stat_brain/engine.py`, `markov_brain/engine.py`, `review_brain/engine.py`, `features/draw_features.py`

**주의:** B1 `draws_with_signal`이 markov/stat/review 입력 오염 → window 실험 해석 불명확

---

## Q3. PHASE 2 학습→엔진

| 경로 | 상태 |
|------|------|
| stat `apply_learn_boost` | ✅ engine.build_weights 반영 |
| markov `apply_learn_boost` | ✅ LEARN_WIRED 시 반영 |
| review adj | ⚠️ carry_over_boost만 · ending/overdue 미소비 |
| Hedge → random.choices | ❌ 미연결 (젠스파크 지적 맞음) |

**adj 주입:** predict 껍데기 아님 — stat/markov `learn.py`, review `engine.generate(..., adj=adj)`

**gap:** `walkforward.py` raw draws만 · B1 `draws_with_signal` 미사용 → live parity 필요

---

## Q4. PHASE 3 auto_tune

- `_auto_feedback` — coordinator 매 회차 실행 **됨**
- `auto_tune_from_feedback()` — **미존재**
- 컨닝 방지: `set_learn_as_of` + `apply_feedback_pure` 인프라 **70%**
- walk-forward auto_tune — **설계 가능 · 미구현**

---

## Q5. B1 virtual draws

| | B1 | highway |
|---|---|---|
| ge3 | 0.0600 | 0.0600 |
| virtual_active | 100% | — |

**판정:** FAIL · **PHASE 1 전 롤백 강력 권고** (`coordinator.py` L368–373 제거)

---

## Q6. 추가 제안

| 우선 | 아이디어 |
|------|----------|
| 1 | B1 롤백 |
| 2 | Highway PHASE1 HOLD/롤백 (형 결정) |
| 3 | Quota/wire 재설계 (`aux_hint_top5` ge3=0.1091) |
| 4 | stat look_back=120 solo (ge3=0.1058) |
| 5 | markov window100 + decay grid solo bench |
| 6 | review ending/overdue learn wiring |
| 7 | walkforward ≡ live stack |
| ✗ | ENGINE_V2 enable (delta=0) |
| ✗ | review lookback=50 (survey 열화) |

---

## GO 전 체크리스트 (지시서 초안용)

```
[ ] B1 롤백 선행
[ ] Highway PHASE1 HOLD vs 고정쿼터 — 형 결정
[ ] PHASE 1 1차 = solo brain + _get_draws_before + set_learn_as_of
[ ] markov window100 solo n=200 — 유일 GO 후보
[ ] stat v2 · review lookback50 — GO 보류
[ ] walkforward ↔ coordinator parity (PHASE 2 전제)
[ ] frozen 3종 유지
[ ] auto_tune 신규 설계
[ ] fused ge3 gate 명시 (0.1015? 0.1218? pin 0.1447?)
```

---

## 커서 최종 한 줄

**markov window100 solo bench만 GO 가치 있음.** stat v2·review50은 근거 약함. **B1 롤백 후** fusion ge3 0.06→0.10+ 회복이 PHASE 2~3보다 선행.

---

_근거: 코드 READ-ONLY 조사 · `20260801_KNEW_ENGINE_STAT_A1` · `20260801_KBRAIN_SIGNAL_B1_BACKTEST_100` · K-HIGHWAY-BACKTEST-100 · tune survey JSON_
