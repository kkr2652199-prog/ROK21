# 1군(MONEY lol) → ROK21 교훈 정리

📅 2026-07-29 · READ-ONLY · DB/코드 수정 없음  
📌 1군 SSOT: `D:\MONEY lol\My_Library\` · ROK21 SSOT: `D:\ROK21`  
📌 근거: 1군 `lotto.db` mode=ro · ROK21 `coordinator.py` · `BENCH_PROTOCOL.md` · `FINDINGS.md` · `20260729_KPOSTHOC_analysis.json`

---

## 1. 배울 점 (ROK21에 가져갈 것)

1군에서 **검증된 설계·관행**만 — 과대 성적(lstm/hyena/fusion DB)과 무관한 축.

| 항목 | 1군 근거 | ROK21 적용 상태 |
|------|----------|-----------------|
| **draws 컷오ff `draw_no < target`** | `_get_draws_before` SQL `WHERE draw_no < ?` — target 당첨번호 생성 미사용 (`20260718_1군_정밀현황` §1) | **동일** — `app/testlotto/data_service.py` `_get_draws_before` · coordinator L157 |
| **생성→채점 분리** | 5뇌 번호 생성 후 `actual_row` 조회·matched 계산·INSERT (`engine.py:428-472`) | coordinator L217-261 동일 패턴 |
| **백테 루프 순서** | predict → INSERT(채점) → feedback → `update_brain_weights` (`engine.py:579-609`) | walkforward 경로 유지 · K-N HOLD(학습입력=best) |
| **stat/markov 정직 baseline** | 1131~1231 DB avg_match **0.8277 / 0.8218** ≈ 이론 0.8 (`20260710_STEP1`) | BENCH_PROTOCOL E[적중]=0.8 · K-O mean 단독 서열 금지 |
| **lead1(F1 wheel) 메타합성** | 5뇌 READ-ONLY + walk-forward 신뢰도 + wheel 5세트 (`predict_brain7.py`) | WIRE-V2 **set_no 쿼터** markov3+stat1+review1 — confidence 정렬 대신 구조적 발권 (`coordinator.py` L36-79) |
| **회차별 예측 전량 API** | `GET /predictions/draw/{n}` — LIMIT 캐시로 과거 회차 누락 방지 (`routes.py:357`) | testlotto per-draw 조회·K-07 갭 정합 |
| **postmortem·pattern_store** | `lotto_patterns.db` 131k+ brain_number_pick — 사후 구조 분석 자산 | ROK21는 전제실증(BENCH §정당성) 축으로 대체 · pattern_store 미이식 |

---

## 2. 이미 갖춘 점 (ROK21이 1군보다 나은 것)

| 항목 | ROK21 상태 | 1군 대비 |
|------|------------|----------|
| **WIRE-V2 pin** | ge3=**0.1447** · mean=1.7504 · p=0.000679 (`20260729_KMARKOV_WIRE_V2_verify.json`) | 1군 1131~1231 **1~2등 0건** · 3등 15건만(hyena/fusion/lstm) |
| **BENCH_PROTOCOL SSOT** | review100 mean · pred=UI전용 · null 병기 · 표본 혼용 금지 | 1군 UI·명예의전당이 `lotto_predictions` stored 혼용 |
| **stored ≠ live 인식** | K-B PATCHED · pred 갭 1149–1179=31 명시 | 1군 DB lstm avg **1.92** vs WF clean **~0.77** (2.5× 부풀림, `20260710_STEP1`) |
| **_get_draws_before + as_of** | K-S: `set_learn_as_of(target)` **기본 ON** · feedback as_of 필수 | 1군 fusion `_load_brain_weights_from_db()` **target 무관** (`fusion.py:220`) |
| **fusion 경로 제거** | K-D: coordinator only · `fusion._vector_fusion_predict` **미호출** | 1군 fusion 7×1등(전역 DB 가중) · hyena 2×1등 |
| **3+4 뇌 체계** | stat/markov/review + AUX 0.25×4 · referee brain_w | 1군 7뇌 UI + llm HOLD + lstm fallback — **실질 4~5뇌** |
| **발권 dedup** | K-V: `ROK21_DEDUP` 기본 ON · E[k]=100 | 1군 중복 조합 낭비·회차 내 유일성 규칙 없음 |
| **POSTHOC 무신호 확정** | 50시드×50회 best ge3=0.18 p=0.109 · signal=false | 1군은 시드·stored 혼재로 역추적 신뢰도 낮음 |
| **명분·전제 실증** | WARRANT.md · K-T/K-AA pattern/balance→실증 | 1군 적중률·avg_match로 뇌 서열화 관행 |

---

## 3. 배우지 말아야 하는 점 (가져오면 안 되는 것)

| 금지 항목 | 1군 근거 (파일·수치) | ROK21 현재 상태 |
|-----------|---------------------|-----------------|
| **fusion 전역 DB 가중치** | `_load_brain_weights_from_db()` target 컷오ff 없음 · `last_updated_draw=1232` 상태로 과거 백테 시 미래 가중 역류 (`20260718` §3, `fusion.py:220`) | fusion **미배선**(K-D) · referee는 `get_referee_weights()` + as_of |
| **feedback target 무관** | `get_feedback_summary(last_n=20)` draw_no `< target` 필터 없음 → LLM/마르코프 프롬프트 오염 (`feedback.py:159-162`) | testlotto feedback **as_of 필수**(K-S) · 단발 클릭 미연결(K-K OPEN) |
| **예측 캐시 재생성 스킵** | DB 기존 행 있으면 `run_prediction` 재생성 생략 (`engine.py:244-287`) | coordinator 캐시 hit 시 반환하나 **brain_review≠pred** 분리(BENCH §2) |
| **hyena 2차 누수** | hyena=5뇌 meta · lstm DB inflated → fusion 가중 → hyena avg **2.24** (`20260710_STEP1`, STEP2 eta) | hyena **미이식** · 3뇌만 live |
| **일괄 백필 WF 혼용** | fusion 1등 7건은 순차 WF(`20260618`)이나 **재백테·캐시 hit** 시 stored≠live 혼재 · 3군 Jun-06 일괄 40행 대비 | BENCH §2 pred UI전용 · review100 WF SSOT |
| **lstm DB 성적 신뢰** | 1131~1231 lstm avg **1.9188** · 3등 4건 · WF clean **0.766~0.778** (`20260710_LSTM누수`) | hyodo LSTM **샌드박스 격리**(KP4) · testlotto 미배선 |
| **7뇌 동등 UI 착시** | llm `LOTTO_LLM_HOLD=True` · lstm uniform fallback 빈번 — UI는 7뇌 풀세트 표시 | 3예측+4보조 명시 · warrant 라벨 |
| **적중률 단독 뇌 서열** | hyena avg 2.24 > stat 0.83 순위 (`20260710_STEP1`) | K-O mean=0.8 상수 · K-P 5적중 기대≈3.5 · **전제실증** 축 |
| **stat/markov stored 1~3등 0 ≠ 무능** | 전체 DB stat/markov **1·2·3등 0건** · 1131~1231도 0건 — 정직 baseline | ROK21 stat K-A mean 0.760 — **패치 전 HOLD** · BENCH null-check |

---

## 4. 1131~1231 3등 15건 표

조건: `matched_count=5 AND bonus_matched=0` · SSOT=`D:\MONEY lol\My_Library\data\lotto.db` mode=ro

| draw_no | brain_tag | numbers | confidence | created_at |
|--------:|-----------|---------|----------:|------------|
| 1133 | hyena | 1,13,20,28,29,34 | 99.0 | 2026-04-26 23:59:40 |
| 1137 | hyena | 9,12,14,15,33,45 | 88.1 | 2026-04-27 00:02:28 |
| 1148 | hyena | 3,6,13,15,16,37 | 99.0 | 2026-04-27 00:10:11 |
| 1174 | lstm | 7,8,11,14,17,36 | 99.9 | 2026-04-27 00:27:58 |
| 1178 | fusion | 5,6,11,16,43,44 | 99.9 | 2026-04-27 00:30:45 |
| 1178 | hyena | 3,5,6,11,27,44 | 90.3 | 2026-04-27 00:30:45 |
| 1178 | lstm | 2,5,6,11,27,44 | 99.9 | 2026-04-27 00:30:45 |
| 1205 | fusion | 1,3,16,23,31,41 | 99.9 | 2026-04-27 11:39:11 |
| 1216 | lstm | 3,10,15,19,23,24 | 99.9 | 2026-04-27 11:51:19 |
| 1219 | fusion | 1,2,12,15,28,45 | 99.9 | 2026-04-27 11:53:32 |
| 1219 | hyena | 1,2,15,17,28,45 | 99.0 | 2026-04-27 11:53:32 |
| 1219 | hyena | 1,2,15,28,38,45 | 91.8 | 2026-04-27 11:53:32 |
| 1219 | hyena | 1,15,24,28,39,45 | 89.1 | 2026-04-27 11:53:32 |
| 1219 | lstm | 1,2,15,17,28,45 | 99.9 | 2026-04-27 11:53:32 |
| 1219 | lstm | 1,2,13,15,28,45 | 99.9 | 2026-04-27 11:53:32 |

**구간 요약 (1131~1231):** 1등 0 · 2등 0 · 3등 15 (hyena 7 · lstm 5 · fusion 3 · stat/markov/llm/lead1 0)

---

## 5. 팩트체크 (수치는 DB/JSON만)

| 항목 | SSOT | 값 |
|------|------|-----|
| 1군 1131~1231 1/2/3등 | `lotto.db` lotto_predictions | **0 / 0 / 15** |
| 1군 1131~1231 3등 by brain | 동상 | hyena **7** · lstm **5** · fusion **3** |
| 1군 전체 DB 1/2/3등 | 동상 | **10 / 3 / 171** (total rows matched≥0: 53975) |
| 1군 stat/markov 전체 1~3등 | 동상 | **0 / 0 / 0** (both tags) |
| 1군 fusion/hyena/lstm 1등 | 동상 | **7 / 2 / 1** |
| ROK21 WIRE-V2 ge3 | `20260729_KMARKOV_WIRE_V2_verify.json` | **0.1447** |
| ROK21 POSTHOC best ge3/p | `20260729_KPOSTHOC_analysis.json` | **0.18 / 0.108945** |
| POSTHOC signal_detected | 동상 | **false** |
| 1군 stat avg 1131~1231 | `20260710_STEP1` (DB stored) | **0.8277** |
| 1군 lstm avg 1131~1231 | 동상 | **1.9188** (WF clean ~0.77 별도 실험) |

---

## Verdict / NEXT

- **1군→ROK21 이식 금지:** fusion·hyena·lstm stored 경로 · 전역 가중 · 캐시 백필 혼용
- **ROK21 유지:** WIRE-V2 pin · BENCH SSOT · 3+4 coordinator · as_of 컷오ff
- **NEXT:** `K-ATTACK-HOLD` — POSTHOC 무신호 · V2 pin · 형 결정 대기

*본 문서는 READ-ONLY 정리. predict_statistical.py·coordinator.py 등 예측 코드 미수정.*
