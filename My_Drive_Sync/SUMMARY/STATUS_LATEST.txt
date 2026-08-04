# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-08-04 KST  
📌 사유: **K-REPACK-HYBRID-WIRE** — stat/review hy_p45_r123 live · PASS

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| **K-REPACK-HYBRID-WIRE** | **PASS** — signal_pool wire · schema=2 · ge3 stat**0.165**/markov**0.130**/review**0.135** (=ablation) · smoke assemble OK · `docs/benchmarks/20260804_KREPACK_HYBRID_WIRE.json` |
| **K-REPACK-HYBRID** | **DONE** — n200 · hy_p45_r123: stat ge3 **0.165**(+0.04) · review **0.135**(+0.03) · markov baseline **0.130**(동률) · `docs/benchmarks/20260804_KREPACK_HYBRID_survey.json` |
| **K-REPACK-ANALYSIS** | **DONE** — PER_BRAIN+DECOMPOSE · oracle gap · lift 전부 음수 |
| **K-PIN-GAP-DIAG** | **DONE** — early ge3=**0.099** 최악 · mid붕괴 기각 · N100 seed42=0.15 vs 0/7=0.10 · K-M≈0 · K-N low_indirect · `docs/benchmarks/20260804_KPIN_GAP_DIAG.json` |
| **K-PIN-GAP-DIAG-REVIEW** | **DOC** — FULL thirds n=394 · mid붕괴 오인 정정 · READ-ONLY≠revalidate reset · 종료5종 보강 · `reports/20260804_GENSPARK_COMPRESS_RESUME.md` |
| **K-IMPROVE-ROADMAP** | **DONE** — I1 pin진단 1순위 · I3 B1 병행 · ultra wire 기각 · `reports/20260804_IMPROVEMENT_INVESTIGATION_ROADMAP.md` |
| **K-GS-FACTCHECK** | **DONE** — 젠스파크 대체로 PASS · 복귀 HEAD=`53decde` 정정 · pin갭≠collapse 구분 · `reports/20260804_GENSPARK_FACTCHECK_KRARE.md` |
| **K-RARE-NESTED** | **DONE** — L0~L3 · 실측연속쌍0.517·3홀3짝0.334 · 역이용=mild구조+비인기EV+covering · `reports/20260803_KRARE_NESTED_BREAKTHROUGH.md` |
| **K-RARE-APPLY-ANAL** | **DONE** — 구조희귀≠당첨확률 · ultra wire HOLD · A1 UI / A4 pin갭 권고 · `reports/20260803_KRARE_APPLY_ANALYSIS.md` |
| **K-RARE-BUNDLE** | **DONE** — catalog 213 · ultra 183 · hits 1235 · API live · `796c92c` |
| **K-BENCH-NULL-BY-EVAL** | **DONE** — `null_for_eval_mode` · enrich_metrics(eval_mode) · BENCH §0.1 · signal_repack ge3=0.275 vs null15=0.3036 **FAIL** · combined 0.145 vs null5 **PASS** |
| **K-BT-PRECISION-BENCH** | **DONE** — WIRE n100→FULL 붕괴 · signal_repack은 best_of_15(null≈0.304) · combined 0.145≈경계 · `reports/20260803_BT200_PRECISION_BENCHMARK.md` · canvas |
| **K-DB-RESET-BT200** | **DONE** — lotto_testlotto 런타임 reset · WF 1035~1234 · pool 201 · 1210·1235 cached 10+5 |
| **K-UI-BT-PRELOAD** | **DONE** — `/backtest/draw-index` n=200 · JS `20260803b` · 탭진입 즉시적용 |
| **K-UI-BT-INSTANT** | **DONE** — pool GET=캐시/backtest_only 즉시 · compute만 WF · revalidate pool보존 |
| **K-FUTURE-WIRE-REVAL** | QUICK**0.1350**(27/200) · FULL**0.1184**(140/1182) · patch PASS · enrich/pin **FAIL** · collapse n100→FULL −0.0316 |
| **K-FUTURE-WIRE** | **PASS** — n=100 ge3=**0.1500** (15/100) · vs V2 +0.06 · per-brain seed+aux_hint **live** |
| **K-FUSION-INNOVATION** | **FAIL** — n=100 ge3=**0.0900** · vs V2 +0 · INNOVATION 롤백 |
| **K-FUSION-DYNAMIC-V2** | **FAIL(1bp)** — solo×ref quota ge3=**0.0900** · plan 4/0/1 · FUTURE-WIRE에 흡수 |
| **K-SIGNAL-BACKTEST-TAIL100** | **DONE** — tail n=100 seed=42 · repack ge3=**0.23**(23) run_id=**3** · combined ge3=**0.15**(15) run_id=**4** · 기존 backtest 2건 유지 |
| **TESTLOTTO UI+DB** | **DONE** — 「🎯 3뇌 예측」단일 · backtest 회차 pool auto-WF · `PATCH_PINS.md` |
| K-SIGNAL-REPACK-01 | **DONE** — 신호 몰아주기 **3등 1회(r3=1)** · top5 ge3=**0.085** · combined=**0.145** · **5장 공정 FAIL** |
| K-SIGNAL-SELECT-01 | **QUICK PASS** — combined ge3=**0.145** p=0.102 · tail n=200 |
| **K-COMBO-V2** | **FAIL** — combo_v2 ge3=**0.125** · baseline=0.145 · B3_cov=100% |
| **K-COMBO-SIGNAL-01** | hollow PASS — AB=0% · baseline only |
| **K-EXCLUDE-SURVEY** | **FAIL** — QUICK n=200 · λ sweep · best exclude ge3=**0.145**=baseline |
| **K-SIGNAL-SELECT-FULL** | **FAIL** — combined ge3=**0.1218** p=0.201 · n=1182 · wire HOLD |
| **K-MARKOV-LEARN-SURVEY** | **FAIL** — wired ge3=**0.105** p=0.683 · stored old=**0.165** · K-F 롤백 |
| **세션 정리 20260801** | tier·3+4·pool·뇌패키지 — ARCHITECTURE_NOTES | **DOC** |
| **K-BRAIN-TUNE-SURVEY** | P0/P1/P2 FULL n=1182 sweep · aux_hint_top5=0.1091 · best_combo=0.1032 · APPLY HOLD | **SURVEY OK** · live_baseline 미달 |
| **K-NEW-ENGINE-STAT-A1** | stat_brain engine v2 dual-window+cycle gap · solo n=200 · baseline/v2 ge3=**0.1350** | **PASS** · delta=0 · ENGINE_V2=False |
| **K-BACKTEST-FULL-C** | C package production stack FULL n=1182 · ge3=**0.1015** · QUICK 0.125 collapse | **FAIL** · live_baseline 0.1218 미달 |
| **K-WIRE-SELECT-FULL-SURVEY** | wire strategy FULL n=1182 · conf_global_top5 ge3=**0.1117** p=0.600 · QUICK collapse | **SURVEY OK** · wire HOLD |
| **K-QUOTA-GAP-SURVEY** | set_no_asc vs conf/aux_hint wire alt · quota_gap=43.0% · conf_global_top5 ge3=**0.135** | **SURVEY OK** · wire GO-WAIT |
| **K-BRAIN-PACKAGE-COMPLETE** | C package core Phase0~7 consolidated · ge3=0.125 n=200 | **PASS** · wire/repack 미변경 |
| **K-BRAIN-PACKAGE-PHASE7** | shared/referee + coordinator aux 1:1 · FULL ge3 A/B | **PASS** · 0.125≥0.125 · AUX_1TO1=True |
| **K-BRAIN-PACKAGE-PHASE6** | markov learn apply_learn_boost · engine 배선 · FULL ge3 A/B | **PASS** · 0.125≥0.125 · LEARN_WIRED=True |
| **K-BRAIN-PACKAGE-PHASE5** | aux 1:1 hint re-rank · coordinator FULL n=200 · ge3 0.115→0.125 | **PASS** · hint_weight=0.15 |
| **K-BRAIN-PACKAGE-PHASE4** | coordinator 3뇌 패키지 배선 · deprecated→brain 동치 n=200 | **PASS** · 3/3 · nums 600/600 |
| **K-BRAIN-PACKAGE-PHASE3** | review_brain 구현 · predict_review_king 동치 n=200 | **PASS** · nums 200/200 |
| **K-BRAIN-PACKAGE-PHASE2** | markov_brain 구현 · predict_flow_shaman 동치 n=200 | **PASS** · nums 200/200 |
| **K-BRAIN-PACKAGE-PHASE1** | stat_brain 구현 · predict_stat_fairy 동치 n=200 | **PASS** · nums 200/200 |
| **K-BRAIN-PACKAGE-C** | 3뇌 A/B/C · 뇌+전용보조 패키지 설계 — HOLD | **DOC** |
| **K-EXCLUDE-HIST-01** | **DONE** — 1~1234 패턴 catalog · 2연속+ 51.7% · LEAKAGE_POLICY |
| K-QUICK-GATE-01 | **DONE** — BENCH §9 · bench_quick_gate.py · `--n-eval` |
| K-WINDOW-SIGNAL-01 | **FAIL** — best w4_zone_mix@α=0.1 ge3=**0.1328** p=0.023 |
| WIRE-V2 pin | ge3=**0.1447** · mean=**1.7504** (stored) |
| 권고 | **K-NEW-ENGINE-MARKOV-A1 형 GO 대기** — STAT v2 uplift 없음 · ENGINE_V2=False 유지 |

---

## 1) 최근 완료

| ID | 요지 | 게이트 |
|----|------|--------|
| **K-REPACK-HYBRID-WIRE** | signal_pool hy_p45 · cache schema2 · markov baseline | **PASS** · ref match |
| **K-REPACK-HYBRID** | pool4+5+몰1~3 ablation · markov 유지 · wire 없음 | **DONE** · stat+0.04 · review+0.03 |
| **K-REPACK-ANALYSIS** | PER_BRAIN+DECOMPOSE · oracle/lift | **DONE** |
| **K-PIN-GAP-DIAG** | FULL thirds·뇌기여·seed스윕·K-M/N · wire 없음 | **DONE** · early/−0.0457 · seed range 0.05 |
| **K-PIN-GAP-DIAG-REVIEW** | 젠스파크 I1 지시서 vs FULL JSON 구조대조 · 수정3건 · 압축복구 §6 | **DOC** |
| **K-IMPROVE-ROADMAP** | 대폭개선 조사·리스크·I1+I3 권고 · ultra HOLD | **DONE** |
| **K-UI-BT-PRELOAD** | 200회 draw-index 프리로드 · init 재진입 갱신 · JS 20260803b | **DONE** · index≈119ms |
| **K-UI-BT-INSTANT** | 백테 저장분 페이지 즉시 표시 · GET 자동WF 금지 · JS backtest_only | **DONE** · 1100≈86ms |
| **K-FUTURE-WIRE-REVAL** | 리셋 WF · QUICK200 + FULL1182 · draws 유지·pred/learn 재기입 | patch **PASS** · pin FULL **FAIL** · ge3 0.135/0.1184 |
| **K-FUTURE-WIRE** | 독립뇌 RNG isolate + aux_hint_native · V2 quota 유지 · n=100 | **PASS** · ge3=**0.1500** (+0.06) |
| **K-NEW-ENGINE-STAT-A1** | stat_brain engine v2 dual-window+cycle gap · solo n=200 A/B | **PASS** · ge3 0.1350=0.1350 · ENGINE_V2=False |
| **K-BRAIN-TUNE-SURVEY** | P0 wire · P1 look_back · P2 hint_weight FULL n=1182 · best_combo | **SURVEY OK** · ge3=0.1032 · HOLD |
| **K-BACKTEST-FULL-C** | C package production stack FULL n=1182 · by_brain · by_period · QUICK vs FULL | **FAIL** · ge3=0.1015 · collapse −0.0235 |
| **K-WIRE-SELECT-FULL-SURVEY** | wire strategy FULL n=1182 · QUICK vs FULL compare · quota_gap 43.1% | **SURVEY OK** · conf_global_top5 0.1117 · wire HOLD |
| **K-QUOTA-GAP-SURVEY** | set_no_asc vs conf/aux_hint wire alt · quota_gap 43.0% · oracle ge3=0.290 | **SURVEY OK** · conf_global_top5 0.135 · wire GO-WAIT |
| **K-BRAIN-PACKAGE-COMPLETE** | C package core Phase0~7 · consolidated bench · ge3=0.125 | **PASS** · wire/repack HOLD |
| **K-BRAIN-PACKAGE-PHASE7** | shared/referee · coordinator aux 1:1 · FULL ge3 A/B | **PASS** · 0.125≥0.125 |
| **K-BRAIN-PACKAGE-PHASE6** | markov learn apply_learn_boost · engine 배선 · FULL ge3 A/B | **PASS** · 0.125≥0.125 |
| **K-BRAIN-PACKAGE-PHASE5** | shared/aux_hint rerank · stat/markov/review hint · FULL ge3 A/B | **PASS** · 0.125≥0.115 |
| **K-BRAIN-PACKAGE-PHASE4** | coordinator PREDICT_MODULES→3뇌 패키지 · predict_sets 어댑터 · 동치 n=200 | **PASS** · 3/3 |
| **20260801 세션 정리** | ge3≠3등 · 3뇌/4보조/repack · 뇌코드 규모 · 8→7·패키지 제안 | **DOC** |
| **K-MARKOV-LEARN-SURVEY** | markov learn_state 배선 QUICK · stored vs live wired | **FAIL** · wired ge3=0.105 · 롤백 |
| **K-EXCLUDE-SURVEY** | combined+배제 λ sweep · WF as_of catalog · 3패턴 · QUICK n=200 | **FAIL** · ge3=0.145=baseline |
| **K-SIGNAL-SELECT-FULL** | 10pool 선별 combined · live WF n=1182 · pin+p 게이트 | **FAIL** · ge3=0.1218 |
| **K-EXCLUDE-HIST-01** | 1~1234 당첨 패턴 catalog · 배제 준비 · as_of WF 정책 | **DONE** |
| **TESTLOTTO UI accordion** | all 모드 탭바 제거 · 3뇌 아코디언 단일 · policy/warrant 예측영역 숨김 · pool/repack 조건부 | **UI OK** · 1136 |
| **TESTLOTTO backtest pool PIN** | eval reset 후 cache miss → backtest draw auto-WF · import/backfill · 1136/1234/1030 QA | **PIN OK** |
| **K-SIGNAL-BACKTEST-TAIL100** | tail-100 WF · combined+repack · eval구간 pred/cache reset · backtest 4건 DB | repack **ge3=0.23 PASS** · combined ge3=0.15 FAIL |
| **TESTLOTTO click-predict** | startup prewarm 제거 · cache-only GET · 「3뇌 예측」 단일 · 회차전환 auto WF 금지 | **QA PASS** 1214/1232/1235 |
| **TESTLOTTO tier-match** | hero·모달·pool 카드 SSOT 통일 · detail/lotto_predictions 이중집계 제거 · 1235 미추첨 | **QA PASS** 1214/1234/1200/1235 |
| **TESTLOTTO NO-LOADING** | SQLite pool-view 캐시 · startup prewarm · accordion+sub-tabs · 12~31s→~4ms | **LOAD OK** · WF SSOT 유지 |
| **TESTLOTTO UI/UX** | B-04 로딩·스켈레톤 · sticky탭·카드여백 · chevron · GenSpark UI 라운드 | **UI OK** · 기능무변경 |
| **TESTLOTTO UI+DB** | 10+5 pool API · backtest_runs/draw_results · 7021 한국어 UI · import_k_signal_backtest | **DONE** · WF only |
| **K-SIGNAL-REPACK-01** | 10pool→번호 몰아주기→5×3뇌=15장 · QUICK n=200 | **5장 FAIL** · r3=1 |
| **K-SIGNAL-SELECT-01** | 10pool/brain×3뇌 → 통합5 선별 · overlap/bin/jaccard/combined · QUICK n=200 | **QUICK PASS** · combined ge3=0.145 |
| **K-QUICK-GATE-01** | BENCH §9 · tail-200 · bench_quick_gate.py · window survey `--n-eval` | **DONE** |
| **K-WINDOW-SIGNAL-01** | DHLOTTERY 4/8/12/52/all×4signal hint inject · 61 variants · n=1182 seed=42 | **FAIL** · best ge3=0.1328 |
| **K-POSTMORTEM-SIGNAL-02** | ge3+ draw_features bin stratification · READ-ONLY | **DONE** · lift 미약 |
| **K-AUX-SIGNAL-01** | 4보조 hint inject live WF · 5 variants×α · n=1182 seed=42 | **FAIL** · best ge3=0.1303 |
| **DHLOTTERY-AUDIT** | 동행복권 lt645 추첨·통계·판매점 READ-ONLY · K-AUX 3아이디어 | **AUDIT OK** |
| **K-BENCH-01** | postmortem WF n=1182 · tier·쿼터갭·AUX상관 · seed=42 | **SIGNAL_FOUND** |
| **4AUX_FEEDBACK_REVIEW** | 4보조=채점·set_no_asc면 컷없음·피드백 부분구현 · GenSpark 일치 | **REVIEW OK** |
| **K-BENCH-02** | confidence/AUX 5축 live WF · set_no_asc vs confidence/quota | **FAIL** · baseline 최고 |
| K-BENCH-05·03 | BENCH_PROTOCOL §6·§7 · BENCH_REPORT_TEMPLATE | **PROTOCOL OK** |
| K-POSTHOC-ANALYSIS | 50시드×50회 역추적 | **무신호** |

---

## 2) K-BENCH-01 핵심

| 지표 | 값 | 비고 |
|------|-----|------|
| n_eval | **1182** | draw 53~1234 · seed=42 |
| ge3_rate (selected best-of-5) | **0.11** | mean=1.7191 · pin 미달(진단) |
| 쿼터 갭 | **43.6%** (516/1182) | 15중 best > 선택5 best · avg gap=1.188 |
| markov 15중 best | **52.5%** | stat 29.9% · review 17.5% |
| AUX↔hit spearman | **~0** | miss/referee constant · pattern/balance 무상관 |
| tier (selected 5) | r4=7 · r5=132 | ge3=139/5910 sets |
| verdict | **SIGNAL_FOUND** | ge3 PASS/FAIL 아님 |

근거: `docs/benchmarks/20260729_KBENCH_POSTMORTEM.json`

---

## 3) K-BENCH-02 핵심

| variant | ge3_rate | mean | Δ vs pin | p (null) | verdict |
|---------|----------|------|----------|----------|---------|
| baseline_set_no_asc | **0.1100** | 1.7191 | −0.0347 | 0.669622 | FAIL |
| confidence_desc | 0.1024 | 1.6997 | −0.0423 | 0.899894 | FAIL |
| aux_quota | 0.1007 | 1.6878 | −0.0440 | 0.929290 | FAIL |
| confidence_quota | 0.0998 | 1.6760 | −0.0449 | 0.941286 | FAIL |
| aux_total_desc | 0.0990 | 1.6853 | −0.0457 | 0.951647 | FAIL |

| 항목 | 값 |
|------|-----|
| n_eval | **1182** (draw 53~1234) |
| pipeline | WF live · seed=42 · SETS_PER_PREDICT_BRAIN=5 |
| 관측 | confidence/AUX 정렬은 set_no_asc **대비 ge3 하락** (역효과) |
| coordinator | **미수정** · K-BENCH-02-WIRE **불필요** |

근거: `docs/benchmarks/20260729_KBENCH_CONFIDENCE_survey.json`

---

## 3e) K-SIGNAL-SELECT-01 핵심 (QUICK tail-200)

| selector | ge3_rate | mean | Δ vs pin | Δ vs null | p (null) | verdict |
|----------|----------|------|----------|-----------|----------|---------|
| **combined** | **0.145** | 1.715 | +0.0003 | +0.0313 | **0.102** | **QUICK PASS** |
| bin_match | 0.115 | 1.68 | −0.0297 | +0.0013 | 0.510 | FAIL |
| jaccard_div | 0.115 | 1.595 | −0.0297 | +0.0013 | 0.510 | FAIL |
| set_no_asc (control) | 0.08 | 1.68 | −0.0647 | −0.0337 | 0.952 | FAIL |
| window_overlap | 0.08 | 1.64 | −0.0647 | −0.0337 | 0.952 | FAIL |

| 항목 | 값 |
|------|-----|
| n_eval | **200** (draw 1035~1234) · seed=42 · elapsed 18s |
| pool | 3뇌×10 (survey 2-pass) → 통합 5 신호셋트 |
| window hint | w4_zone_mix (K-WINDOW best) |
| QUICK gate | ge3>null AND p<0.15 → **PASS** (combined) |
| coordinator | **미수정** · wire **형 GO 전 금지** |

근거: `docs/benchmarks/20260730_KSIGNAL_SELECT_survey.json`

---

## 3c) K-WINDOW-SIGNAL-01 핵심

| variant | window | signal | α | ge3_rate | mean | Δ vs pin | p (null) | verdict |
|---------|--------|--------|--:|---------:|-----:|---------:|---------:|---------|
| **w4_zone_mix** | 4주 | zone_mix | 0.1 | **0.1328** | 1.7453 | −0.0119 | **0.0232** | FAIL (pin 미달) |
| w4_sum_band | 4주 | sum_band | 0.2 | 0.1311 | 1.72 | −0.0136 | 0.035 | FAIL |
| w8_miss_pattern | 8주 | miss_pattern | 0.2 | 0.1303 | 1.7081 | −0.0144 | 0.042 | FAIL |
| baseline (AUX score) | — | — | 0 | 0.1108 | 1.7318 | −0.0339 | 0.635 | FAIL |

| 항목 | 값 |
|------|-----|
| n_eval | **1182** · seed=42 · elapsed 7094s |
| variants | 61 (5 windows × 4 signals × 3 α + baseline) |
| PASS gate | ge3 > 0.1447 AND p < 0.05 → **FAIL** |
| coordinator | **미수정** · K-WINDOW-SIGNAL-WIRE **보류** |

근거: `docs/benchmarks/20260729_KWINDOW_SIGNAL_survey.json`

---

## 3d) K-POSTMORTEM-SIGNAL-02 핵심

| axis | best bin | ge3_rate | lift vs overall(0.11) |
|------|----------|---------:|----------------------:|
| odd_count | odd=2 | 0.1412 | +0.0312 |
| ac | ac>=9 | 0.1206 | +0.0106 |
| sum_band | mid(120-155) | 0.1137 | +0.0037 |

판정: bin lift **미약** — E3 hint 설계 시 단일 bin 의존 비권장.

근거: `docs/benchmarks/20260729_KPOSTMORTEM_SIGNAL02.json`

---

## 3b) K-AUX-SIGNAL-01 핵심

| variant | α | ge3_rate | mean | Δ vs pin | p (null) | verdict |
|---------|--:|---------:|-----:|---------:|---------:|---------|
| **miss_pattern** | 0.2 | **0.1303** | 1.7301 | −0.0144 | **0.042** | FAIL (pin 미달) |
| pattern_store_lite | 0.05 | 0.1235 | 1.7191 | −0.0212 | 0.154 | FAIL |
| baseline (AUX score) | 0 | 0.1218 | 1.7259 | −0.0229 | 0.201 | FAIL |
| balance_hint | 0.05 | 0.1024 | 1.6988 | −0.0423 | 0.900 | FAIL |

| 항목 | 값 |
|------|-----|
| n_eval | **1182** · seed=42 · elapsed 1504s |
| inject | survey `random.choices` wrapper · predict path only |
| PASS gate | ge3 > 0.1447 AND p < 0.05 → **FAIL** |
| coordinator | **미수정** · K-AUX-SIGNAL-WIRE **보류** |

근거: `docs/benchmarks/20260729_KAUX_SIGNAL_survey.json`

---

## 4) BENCH 프로토콜 (유지)

| 항목 | 값 |
|------|-----|
| theory mean | **0.8000** |
| theory ge3 (null) | **0.1137** |
| WF vs stored | **표 2개 또는 `pipeline` 컬럼** — 혼용 금지 |
| tier 규칙 | 1등=6 · 2등=5+bonus · 3등=5 · 4등=4 · 5등=3 |

---

## 4) 4보조·피드백 (형 가설 판정 · READ-ONLY)

| 질문 | 판정 |
|------|------|
| 4보조=검증된 심사? | **아님** (미입증·기각 명분) |
| DB 분업 분석? | **아님** — 15장 채점 |
| AUX 컷으로 신호 유실? | **현 배선(set_no_asc)에선 컷 없음** · confidence 정렬은 BENCH-02에서 더 나쁨 |
| 당첨/미당첨→피드백 축적 | **뼈대 있음·등수별 부족** · markov는 learn_state 미사용 |
| 형 vs 보수 | 형 감각 맞음 · AI측 “증명 전 배선 금지”로 보수 — **둘 다 맞음** |

근거: `reports/20260729_4AUX_FEEDBACK_REVIEW.md` · GenSpark 형6문 답변

---

## 5) 다음

**K-SIGNAL-SELECT-FULL** — QUICK PASS(combined ge3=0.145) → full n=1182 확인 · wire는 형 GO 전 금지.  
V2 pin ge3=0.1447 유지 · coordinator·predict_* **수정 금지**.

---

## 6) 산출물

- `tools/bench_quick_gate.py` · `tools/_k_signal_select_survey.py`
- `docs/benchmarks/20260730_KSIGNAL_SELECT_survey.json`
- `reports/20260730_KSIGNAL_SELECT_SURVEY.md`
- `My_Drive_Sync/SUMMARY/BENCH_PROTOCOL.md` §9 QUICK_GATE
- `tools/_k_window_signal_survey.py` (`--n-eval`)

## 팩트체크

| 항목 | JSON | 보고서 | STATUS |
|------|------|--------|--------|
| n_eval | 1182 | 1182 | 1182 |
| ge3_rate | 0.11 | 0.11 | 0.11 |
| quota_missed_rate | 0.4365 | 0.4365 | 0.4365 |
| verdict | SIGNAL_FOUND | SIGNAL_FOUND | SIGNAL_FOUND |
| recommended_next | K-BENCH-01-WIRE | K-BENCH-01-WIRE | K-BENCH-01-WIRE |
