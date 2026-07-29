# 1군 벤치 심화 검토 · ROK21 적용 아이디어

📅 2026-07-29 · READ-ONLY(1군) · ROK21 문서·아이디어만  
📌 1군 SSOT: `D:\MONEY lol\My_Library\` · ROK21: `D:\ROK21`  
📌 선행: `20260729_MONEY1GUN_ROK21_LESSONS.md` · POSTHOC 무신호 · V2 pin 유지

---

## §1 심화 발견 (1군)

### 1.1 postmortem_engine.py — 사후 분석 파이프라인

- **분리 원칙:** `lotto.db`는 `PRAGMA query_only=ON` · 결과만 `lotto_patterns.db` `postmortem_draw`에 UPSERT.
- **핵심 지표(회차당):**
  - `pool_cover` / `pool_missed` — 5뇌(stat·markov·llm·lstm·fusion) 합집합이 main6 중 몇 개 커버
  - `lead1_pack` / `pack_gap` — lead1 5세트 합집합 커버 vs 5뇌가 잡았으나 lead1이 놓친 번호(`pack_gap_brains`)
  - `brain_summary` JSON — 뇌별 union_hit·best_set_hit·misses
  - `winning_stats` / `lead1_union_stats` — 홀짝·구간·연번·합계 (`combo_stats`)
- **자동 훅:** `maybe_build_postmortem_after_scoring(scored_draw_no)` — 채점 후 1회차 빌드, 예측 파이프라인 격리(실패 전파 없음).
- **실측:** `postmortem_draw` **1115행** · 최근(1234): pool_cover=**6** · lead1_pack=**4** · pack_gap=**2** · lead1_best_hit=**2**.

**ROK21 대비:** hyodo에 동일 엔진 복제(`app/hyodo/postmortem_engine.py`) · testlotto에는 **미배선**. ROK21는 BENCH SSOT(review100 mean) + POSTHOC 역추적 축.

### 1.2 pattern_store.py + lotto_patterns.db

| 테이블 | 행수(실측) | 역할 |
|--------|-----------|------|
| `brain_number_pick` | **131,774** | draw×brain×number · `k_brains`(5뇌 합의수)·`is_winning` |
| `draw_combo_summary` | **1,200** | 5뇌 union_win·best_raw_hit·consensus_top6·`ktier_win_json` |
| `combo_result` | **3,600** | strategy별(consensus_top6/oracle_best/best_raw) 6번호·hit_count |
| `postmortem_draw` | **1,115** | §1.1 |

- `get_consensus_numbers(draw, min_k=3)` — k≥3 합의 번호(8뇌 재료용).
- `get_ktier_winners(draw)` — k별 당첨 번호 수(`v_ktier_win`).
- **READ-ONLY 전용** — `lotto.db`·6뇌 생성 로직 미접근.

**ge3+ 샘플(draw_combo_summary):** 1219 union_win=6·best_raw_hit=**5** · ktier `{"2":1,"3":2,"4":1,"5":2}`.

### 1.3 predict_brain7.py (lead1) — F1_V2_STRICT wheel

- **입력:** 5뇌 25세트 READ-ONLY · hyena 제외.
- **가중:** `k × mean(reliability)` — reliability는 `target_draw_no < ?` walk-forward 라플라스 정밀도.
- **합성:** popavoid(인기패널티) 25후보 → **wheel greedy**(커버리지↑·세트간 중복↓) → 5세트.
- **카피 방지:** `COPY_OVERLAP=5` — 단일 뇌 세트와 5개 이상 겹치면 폐기.
- **confidence:** F1 가중합×10 (max 99.9) — **set_no와 무관**.

**ROK21 WIRE-V2 대비:** coordinator `apply_markov_wire_quota` — markov3+stat1+review1 **set_no 오름차순** 쿼터 · confidence 1차 정렬 **없음** · remainder만 confidence 보충.

### 1.4 fusion.py — 금지 사례 (재확인)

- L77: `VECTOR_WEIGHTS = _load_brain_weights_from_db()` — **target 컷오ff 없음**.
- feedback L159-162: `get_feedback_summary(last_n=20)` — draw_no `< target` 필터 **없음**.
- ROK21 K-D: fusion 미호출 · as_of 필수(K-S).

### 1.5 UI — tier-wins · hall-of-fame · dashboard-summary

| UI/API | 소스 | 표시 방식 |
|--------|------|-----------|
| `/predictions/draw/{n}/tier-wins` | `lotto_predictions` stored | matched≥3만 · 1~5등 섹션 분리 · 뇌별+번호볼 |
| `/brain/hall-of-fame` | stored TOP 적중 | 역대 하이라이트 |
| `/dashboard-summary` `brain_power` | stored 집계 | 뇌별 r1~r5 누적 · 라벨(최강/강함/우수…) |

**주의:** 전부 **stored DB** — WF clean·review100과 혼용 시 1군 lstm 1.92 vs 0.77 부풀림 재현(BENCH §2 금지 패턴).

---

## §2 ROK21 적용 아이디어 (5건)

| ID | 아이디어 | 1군 근거 | ROK21 적용 | 리스크 | 우선 | RO survey |
|----|----------|----------|------------|--------|------|-----------|
| **K-BENCH-01** | WF 회차별 postmortem형 진단 로그(커버·갭·뇌별 best) | `postmortem_engine.py` pool_cover/pack_gap/brain_summary | `tools/_k_posthoc` 또는 신규 `_k_draw_postmortem_survey.py` · review100 JSON 입력만 · `reports/`+`docs/benchmarks/` 산출 | stored pred 혼입 금지 · 예측 코드 미수정 | **MED** | **가능** |
| **K-BENCH-02** | 발권: set_no 쿼터 vs AUX/confidence 정렬 A/B | `predict_brain7.py` wheel+confidence · CAP2 SEL4/V3 | 벤치 스크립트에서 `apply_markov_wire_quota` OFF vs confidence-top5 **오프라인** 재집계 · coordinator **동결** | V2 pin 0.1447 변경 금지 · 형 GO 전 코드 패치 없음 | **MED** | **가능** |
| **K-BENCH-03** | tier-wins 개념 → 벤치 리포트 1~5등 분리 표 | `lotto.js` tier-wins · `routes.py` tier-wins API | WF JSON 후처리: 뇌×등수(r1~r5) 피벗 · `BENCH_PROTOCOL` §5 null·출처 병기 템플릿 | pred UI(1149–1179 갭) 혼용 **절대 금지** | **HIGH** | **가능** |
| **K-BENCH-04** | draw 특성(홀짝·합·ktier) 조건부 ge3 재분석 | `pattern_store` ktier_win_json · postmortem `winning_stats` | POSTHOC 50×50 결과를 draw_stats bin별 stratify · signal=false 전제 유지 | 다중비교·小표본 · POSTHOC 이미 p=0.109 | **LOW** | **가능** |
| **K-BENCH-05** | stat/markov **이론 baseline 0.8** 고정 행 | 1군 1131~1231 stored 0.8277/0.8218 ≈ 0.8 | 모든 WF 마크다운/JSON에 `E[적중]=0.8`·null-check 행 **템플릿화** · `BENCH_PROTOCOL` §0 | 없음(문서·템플릿만) | **HIGH** | **가능** |

---

## §3 젠스파크에 물어볼 질문 (3개)

1. **POSTHOC 무신호**(best ge3=0.18·p=0.109) 전제에서 **K-BENCH-04**(draw 특성 bin별 ge3) 추가 탐색이 통계적으로 의미 있나, 아니면 HOLD가 맞나?
2. **WIRE-V2 pin**(ge3=0.1447) 유지 전제에서 **K-BENCH-02**(set_no 쿼터 vs AUX/confidence 정렬) 중 어느 축을 **READ-ONLY survey 우선**으로 둘 것인가?
3. **K-BENCH-03**(tier-wins 표)를 벤치 리포트에 넣을 때, review100 WF만 쓰고 pred stored를 분리 표기하는 **현재 BENCH §2**로 UI 착시(1군 dashboard-summary류) 재발을 충분히 막을 수 있는가?

---

## §4 팩트체크

| 항목 | SSOT | 값 |
|------|------|-----|
| 1군 brain_number_pick 행 | `lotto_patterns.db` | **131,774** |
| 1군 draw_combo_summary 행 | 동상 | **1,200** |
| 1군 postmortem_draw 행 | 동상 | **1,115** |
| 1군 postmortem 1234회 | 동상 | pool_cover=**6** · lead1_pack=**4** · pack_gap=**2** |
| ROK21 WIRE-V2 ge3 | `20260729_KMARKOV_WIRE_V2_verify.json` | **0.1447** |
| ROK21 POSTHOC best ge3/p | `20260729_KPOSTHOC_analysis.json` | **0.18 / 0.108945** |
| POSTHOC signal | 동상 | **false** |
| 1군 stat/markov 1131~1231 avg | `20260710_STEP1` | **0.8277 / 0.8218** |
| fusion 가중 로드 | `fusion.py:77` | `_load_brain_weights_from_db()` target 무관 |

---

## Verdict

- **즉시(문서·survey):** K-BENCH-03 · K-BENCH-05 — 예측 코드·pin 무관
- **형 GO 후 survey:** K-BENCH-01 · K-BENCH-02 — coordinator/fusion **미수정**
- **보류:** K-BENCH-04 — POSTHOC 무신호 · LOW 우선
- **NEXT:** K-ATTACK-HOLD 유지 · GenSpark 아이디어별 가져갈/버릴/우선순위 자문

*본 문서는 READ-ONLY 조사·아이디어 초안. predict/coordinator 동결 규칙 준수.*
