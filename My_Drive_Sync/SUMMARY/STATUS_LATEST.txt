# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-08-11 KST  
📌 사유: **[CURSOR] K-REPACK-UNION** — P1/P2 signal_union **APPLY** · 강제BTv3

📌 직전: **[CURSOR] K-SEQ-FORCE-REPACK-KJ** — 강제BTv2 · 손실조사 · K-J PATCHED

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | kkr2652199-prog/ROK21 · **7021** |
| **프레임 (형 정정)** | **양산前 테스트**. DB결과 최신=**1236을 마지막 회차**로 본다. **1237은 준비 단계 아님·예측/양산 아님**. 1235·1234·이전으로 많이 테스트하며 **3뇌 신호 최고성능 튜닝**이 다음. (커서 오해: 1237예측을 다음으로 잡음 → 정정) |
| **뇌독립 원칙 (형 확인)** | **공유 허용=`lotto_draws`(과거 결과값)만**. 뇌별 예측 과정·BLEND/W_*/hint·몰아주기는 **공유 금지**. 튜닝도 뇌별 단독 → 합동 smoke는 마지막만. |
| **서버** | 2026-08-11 재가동 · `python run_v13.py` · http://127.0.0.1:7021/ · HTTP200 |
| **K-REPACK-UNION (형GO · P1/P2패치)** | **APPLY** — `ASSEMBLE_MODE=signal_union` · slots**2**+pool cap**4**+classic보충. 게이트 seed3×1137~1236: prefer **0.172→0.211** · prize **−0.039→−0.072** · stat_hit **0.265→0.255**(slack) · pool>repack모니터↓. 강제BTv3 재적재 mean**2.58** · 4등**6**/5등**47**(모니터) · 손실 재측정 **37/37/34**(구캐시45/41/39). ge3미클레임·1237아님. · `docs/benchmarks/20260811_KREPACK_UNION_GATE.json` · `20260811_KFORCE_POOL_BACKTEST_100_v3.json` · `20260811_KREPACK_LOSS_AUDIT_POST_UNION.json` · `reports/20260811_KREPACK_UNION_APPLY.md` · `tools/_k_repack_union_gate.py` |
| **K-SEQ-FORCE-REPACK-KJ (형GO · 순서①②③)** | **DONE** — ①강제BTv2: 리셋+1137~1236 · knobs cand_B·BLEND0.55/0.85 · pool300/bt100 · mean**2.59** · **4등6·5등48**(모니터) · deep_audit_v2 **NO_HARD_BUG**. ②repack손실: cause=`POOL_BEST_DROPPED_FROM_REPACK` · pool>repack stat**45**/markov**41**/review**39** · 손실시 pool_best∈repack**0** · slots**2** · 코드미적용 PROPOSE_HOLD(P1/P2). ③K-J **PATCHED**: SSOT=`get_referee_weights` · DB current_weight=미러(구식1+avg*0.1제거) · UI live표시 · tune_snapshot에 W_CROWD. ge3미클레임·1237아님. · `docs/benchmarks/20260811_KFORCE_POOL_BACKTEST_100_v2.json` · `20260811_KBT100_DEEP_AUDIT_v2.json` · `20260811_KREPACK_LOSS_AUDIT.json` · `reports/20260811_KSEQ_FORCE_REPACK_KJ.md` |
| **K-F-REDEFINE-JUDGE (젠스파크답+형GO)** | **NO_EFFECT_CLOSE** · FINDINGS K-F=**PATCHED** — Q1=B재료+효과 · Q2=A prefer1차 · Q3=C재료후측정 · Q4=A FINDINGS정정. 백업 backups/20260811_KF전_DB전체/ 24파일·358MB. markov-only feedback 1137~1236 n**100** · brain_review100 · independence_ok · adj/miss 누적(carry0.2/ending0.3…). A/B seed3: prefer OFF**0.292578**→ON**0.292283**(Δ**−0.000295**·미달) · prize **−0.110095** iso0 · mean_hits모니터 0.805→0.783. **LEARN_WIRED=True 유지**(경로정상·효과없음). ge3미사용. · docs/benchmarks/20260811_KF_재정의_판정.json · reports/20260811_KF_재정의_판정.md · tools/_k_f_markov_learn_redefine.py |
| **K-F-INSTRUCTION-FACTCHECK (형GO · 검토)** | **REJECT_REWRITE** · 실행**안함** — 형 「방향맞으면진행/틀리면젠스파크질문」. 방향(K-F후보)=OK · 지시서전제=틀림. 실측: `LEARN_WIRED=True`이미ON · live=`markov_brain`이미`apply_learn_boost` · learn_state**0**/adj**0**/evolve**0**→True/False A/B=noop · FINDINGS K-F인용`predict_flow_shaman`=DEPRECATED. 평균적중단독게이트=K-O/R38충돌가능. 젠스파크질문=`reports/20260811_KF_GENSPARK_QUESTIONS.md`. · `docs/benchmarks/20260811_KF_INSTRUCTION_FACTCHECK.json` · `reports/20260811_KF_INSTRUCTION_FACTCHECK.md` |
| **K-ANALYSIS-LOCK-CYCLE1 (형GO · 확정)** | **LOCKED** — 형 「지금까지 분석 확정+리스트 이어서」. 잠금: markovBLEND**0.55** · reviewBLEND**0.85** · statHINT**52** · JOINT SMOKE_OK · UI schema4 · FORCE BT REBUILT · SCORE cand_A(이후 retune으로 갱신). ge3클레임금지·1237아님. · `docs/benchmarks/20260811_KANALYSIS_LOCK_CYCLE1.json` · `reports/20260811_KANALYSIS_LOCK_CYCLE1.md` |
| **K-W-CROWD-BY-BRAIN-TUNE (리스트2)** | **APPLY** — W_CROWD 스윕{0.5…0.9}×seed3×1137~1236 · BLEND잠금. markov prefer base**0.243**→**0.9:0.282**(|Δ|≥0.01·prize_iso0) · review prize base**−0.074**→**0.9:−0.095**(|Δ|≥0.01·prefer_iso0). **`W_CROWD_BY_BRAIN` markov/review=0.90 · STRUCT=0.10**. ge3미사용. · `docs/benchmarks/20260811_KW_CROWD_BY_BRAIN_TUNE.json` · `reports/20260811_KW_CROWD_BY_BRAIN_TUNE.md` · `tools/_k_w_crowd_by_brain_tune.py` |
| **K-SCORE-WEIGHTS-RETUNE (리스트3)** | **APPLY** — W=0.9 전제 · cand_A vs B/C/D. cand_B hint↑ markov/review**(0.65,0.15,0.20)** · prefer**0.293**/prize**−0.110**/stat_hit**0.308**(비악화) 게이트PASS. C/D FAIL. **`SCORE_WEIGHTS_BY_BRAIN` cand_B 적용**. · `docs/benchmarks/20260811_KSCORE_WEIGHTS_RETUNE.json` · `reports/20260811_KSCORE_WEIGHTS_RETUNE.md` · `tools/_k_score_weights_retune.py` |
| **K-EVOLVE-FGJ-AUDIT (리스트4·5 · READ)** | **AUDIT_DONE** · wire=**False** — evolve_log**0**(강제리셋후) · weight_applied Phase1=0 · live referee **균등0.333** spread**0**(learn_state0) · DB brain_weights stat1.5/markov1.0/review1.2 ≠ live → **K-J DUAL_OPEN** · **K-F OPEN_LIKELY**(markov learn 미소비) · **K-G DORMANT**. 다음패치후보=합동smoke / K-F배선 / K-J SSOT. · `docs/benchmarks/20260811_KEVOLVE_FGJ_AUDIT.json` · `reports/20260811_KEVOLVE_FGJ_AUDIT.md` · `tools/_k_evolve_fgj_audit.py` |
| **K-FORCE-POOL-BACKTEST-100 (형GO · DB)** | **REBUILT_OK** — 형 「100회백테 미기록·리셋후 재백테=패치기능·강제리셋·컨닝금지」. 사전실측: `backtest_draw_results=0` · `lotto_predictions=0` · pool캐시**15**(1225~1236일부) · `brain_review=300`(구 K-M복습≠UI백테). **강제**: `_k_predict_reset` APPLY(복습300·pool15 등 삭제·draws보존) → 1137~1236 n**100** · `_get_draws_before` · peek가드(max_material&lt;target) · `expand_pool`+`build_hint_by_brain`+`repack_by_brain` · knobs markovBLEND**0.55**/review**0.85**/statHINT**52**. 후: pool_view_cache **300행/100회** schema4 · `backtest_runs` run_id**9** · draw_results**100** · API `draw-index` n_draws**100**. mean_hits**2.6**/ge3_rate**0.56**=**모니터만·클레임금지**. 캐시 hit면 구예측 재사용 가능→강제리셋필수. · `docs/benchmarks/20260811_KFORCE_POOL_BACKTEST_100.json` · `reports/20260811_KFORCE_POOL_BACKTEST_100.md` · `tools/_k_force_pool_backtest_100.py` |
| **K-UI-DETAIL-POOL10x5 (형GO · UI)** | **PATCHED** — 형 「tldSingleView 초창기→최신10+5·보기좋게」. 상세 ②=`pool-view` 뇌별**10+5** · knobs strip(markov0.55/review0.85/statHINT52) · 점프내비·요약칩·sticky탭·2열카드·적중하이라이트. 오답노트=③(구복습DB 별개 표기). 캐시 schema**4** · `tune_snapshot` API. 1236 refresh 실측 pool10/repack5. 메인 아코디언 카운트 `10+5`. · `docs/benchmarks/20260811_KUI_DETAIL_POOL10x5.json` · `reports/20260811_KUI_DETAIL_POOL10x5.md` |
| **K-BRAIN-JOINT-SMOKE (권장④)** | **SMOKE_OK** · wire=**False** — 형 「서버재가동·다음진행」. knobs 실측 markovBLEND**0.55**/review**0.85**/statHINT**52**. 1137~1236×seed3: prefer**+0.244449** · prize**−0.074379** · hit**0.319444** · split1.0 · cn1.0 · **단독대비 drift0**. ge3미사용. · `docs/benchmarks/20260811_KBRAIN_JOINT_SMOKE.json` · `reports/20260811_KBRAIN_JOINT_SMOKE.md` · `tools/_k_brain_joint_smoke.py` |
| **K-STAT-PATTERN-TUNE (권장③)** | **APPLY** — 형 「다음 진행」. knob=`HINT_SPEC_BY_BRAIN['stat'].weeks` · miss_pattern · 1137~1236 n100 · seed[0,42,123]. base@26 hit**0.306667** → **52: 0.319444** (|Δ|**0.012777**≥0.005) · 39도 PASS(0.316667). prefer/prize_drift**0**. markov/review HINT·BLEND 불변. decay/ASSOC/ge3 미사용. · `docs/benchmarks/20260810_KSTAT_PATTERN_TUNE.json` · `reports/20260810_KSTAT_PATTERN_TUNE.md` · `tools/_k_stat_pattern_hint_tune.py` |
| **K-BRAIN-INDEPENDENCE-BY-BRAIN (형GO · wire)** | **PATCHED** — `W_*_BY_BRAIN` · `BLEND_STRENGTH_BY_BRAIN` · `prefer_table/prize_table/blend_weights(brain=)`. 호출: markov/review engine · signal_pool hint. 기본값 markov/review 당시 0.55/0.55 → review만 후속 APPLY. · `docs/benchmarks/20260810_KBRAIN_INDEPENDENCE_BY_BRAIN.json` · `reports/20260810_KBRAIN_INDEPENDENCE_BY_BRAIN.md` |
| **K-MARKOV-PREFER-BLEND-TUNE (권장①)** | **NO_IMPROVE** · wire=**False**(측정) — 1137~1236 n100 · seed[0,42,123] · markov BLEND {0.40…0.85} · review고정. base prefer**+0.244449** · **전후보 prefer↓**(|Δ|≪0.01) · **prize_drift=0.000**(독립실측). best=null · **markov 0.55 HOLD**. · `docs/benchmarks/20260810_KMARKOV_PREFER_BLEND_TUNE.json` · `reports/20260810_KMARKOV_PREFER_BLEND_TUNE.md` · `tools/_k_markov_prefer_blend_tune.py` |
| **K-REVIEW-PRIZE-BLEND-TUNE (권장②)** | **APPLY** — 동구간·동seed · review BLEND만. base prize**−0.063355** → **0.85: −0.074379** (|Δ|**0.011024**≥0.01) · prefer_drift**0** · cn_rate**1.0**. **`BLEND_STRENGTH_BY_BRAIN['review']=0.85`** · markov**0.55** 불변. ge3미사용. · `docs/benchmarks/20260810_KREVIEW_PRIZE_BLEND_TUNE.json` · `reports/20260810_KREVIEW_PRIZE_BLEND_TUNE.md` · `tools/_k_review_prize_blend_tune.py` |
| **K-M-REFEREE-WEIGHT (형GO · 테스트단계)** | **PATCHED** — 형 「백테≈100·예측DB리셋후」. `get_referee_weights`: 구식`1+avg×0.15`→`1+GAIN×(avg−0.8)` GAIN**2.5**. 예측산출물 리셋(pred**0**/evolve**0** · draws**1236**보존). 복습 **1137~1236 n100** mean입력. avgs stat**0.867**/markov**0.70**/review**0.80** · spread legacy**0.007**→new**0.143** · quota5=**2/1/2**. FINDINGS K-M=**PATCHED**. · `docs/benchmarks/20260810_KM_REFEREE_WEIGHT.json` · `reports/20260810_KM_REFEREE_WEIGHT.md` |
| **K-N-MEAN-INPUT-FIX (형GO · 테스트단계)** | **PATCHED** — 형 「개발중·3뇌테스트·1237완료후 양산」→ K-N 진행. `walkforward._learn_match_from_sets` · `FEEDBACK_MATCH_MODE=mean` 공유. apply_feedback 입력=**mean** · best는 tier/표시/`best_matched`만. unit: best=3 vs learn=1 오인사례 차단. smoke1235 3뇌 mode=mean · learn≠best 실측. FINDINGS K-N=**PATCHED**. · `docs/benchmarks/20260810_KN_MEAN_INPUT_FIX.json` · `reports/20260810_KN_MEAN_INPUT_FIX.md` |
| **K-PROCESS-STRUCTURE-QUERY (형GO · READ)** | **DOC_OK** · wire=**False** · 코드/DB무수정. **예측**: UI`runPredict`→`routes.api_predict`→`engine.run_prediction`→`coordinator.run_coordinated_prediction` · 재료=`_get_draws_before(target)`=**target미만** · `set_learn_as_of(target)`. **채점**: `after_predict(N)`=**N-1** · `draw_result(N)`=**N** · 자동=예측클릭+_auto_feedback·fetch-latest. **실측**: max_draw1236 · pred1236=10 · pred1237=**0**. **evolve**: 예측만으론 안 쌓임 · evolve_auto/feedback마크 · weight_applied Phase1=**0고정**(K-M전). 젠스파크오해: after_predict(1236)≠1236채점. · `reports/20260810_KPROCESS_STRUCTURE.md` · `docs/benchmarks/20260810_KPROCESS_STRUCTURE.json` |
| **K-1236-FEEDBACK-VERIFY (형GO · READ)** | **VERIFY_OK** · wire=**False** — draw1236 nums=**[12,18,21,29,34,38]** bonus**10** first_winners**11**. 통합발권 quota로 stat0장→`brain_filter(stat)` 보충 후 3뇌 feedback. evolve 3뇌 `K-KK-FEEDBACK` · weight**0.0** · 중복SKIP OK. mean_hits 단건참고 stat**1.0**/markov**0**/review**0**(baseline0.8·서열화금지). hint∩actual review**3**/markov**2**(단건방향·클레임금지). API: `after_predict(1236)`=1235채점 · 1236채점=`apply_draw_result_feedback(1236)`. 다음=**K-N-MEAN-INPUT-FIX**. · `docs/benchmarks/20260810_K1236_FEEDBACK_VERIFY.json` · `reports/20260810_K1236_FEEDBACK_VERIFY.md` |
| **K-KK-FEEDBACK-WIRE (형GO · wire)** | **PATCHED** — K-K OPEN→연결. 신규 `click_feedback.py` · routes `POST /predict`·`/fetch-latest` 명시 호출. STEP0: routes 구미연결·coordinator `_auto_feedback` 기존재 · `apply_feedback(brain,draw,matched,missed)` · evolve 마크=`K-KK-FEEDBACK`. 검증: 1230~1235 **6회×3뇌=18행** · evolve 60→60(UPDATE) · weight_applied **0.0** · 중복SKIP·9999 SKIP · predict OK. FINDINGS K-K=**PATCHED** · K-M/K-N **HOLD**. · `docs/benchmarks/20260810_KKK_FEEDBACK_WIRE.json` · `reports/20260810_KKK_FEEDBACK_WIRE.md` |
| **K-BLEND-STRENGTH-SWEEP (형GO · READ)** | **NO_IMPROVE** · wire=**False** — 사전확인 BLEND=0.55·SCORE_WEIGHTS=cand_A·IDEA_CHECK pass OK. 스윕 {0.35…0.75}×seed5×1100~1235. base prize**−0.059526** / prefer**+0.245772** / cn=**1.0**. 개선후보 전원 **cond3 실패**(|Δprize|최대≈0.0037≪0.01). 0.40이 prize 최음수(−0.0614)나 |Δ|=0.0019 noise. **best=null · APPLY 금지 · 0.55 HOLD**. ROLLBACK 아님. · `docs/benchmarks/20260810_KBLEND_STRENGTH_SWEEP.json` · `reports/20260810_KBLEND_STRENGTH_SWEEP.md` · `tools/_k_blend_strength_sweep.py` |
| **K-GENSPARK-IDEA-CHECK (형GO · READ)** | **CHECK_DONE** · wire=**False** — 젠스파크 4안 실측. **①consistent_neg**: cand early seed5/5 전부음수·cn=True(안정) · SE≈0.009 · **조건부**(다seed 보조 동의·단독하드 비동의). **②W_CROWD/STRUCT**: 공유상수(0.7/0.3)·BLEND_STRENGTH 공용0.55 · 뇌별분리 **미구현·가능** · 의견=**단일 BLEND 먼저**. **③evolve/feedback**: `testlotto_evolve_log` stat weight_applied **전부0**(상수0.0) · referee **완전균등 0.333**(spread0·K-M) · routes `apply_feedback` 없음(K-K) → **stat튜닝 HOLD**. **④게이트**: cand_A 조건1·2·3 **PASS** · split 68/68 prefer+/+ · thr0.01 · 다seed cn_rate=1.0. **즉시**=단일BLEND+EV/prefer게이트+다seed cn보조 · **HOLD**=뇌별W·stat튜닝·cn단독하드. · `docs/benchmarks/20260810_KGENSPARK_IDEA_CHECK.json` · `reports/20260810_KGENSPARK_IDEA_CHECK.md` · `tools/_k_genspark_idea_check.py` |
| **K-NEXT-ROUTE-LIT-GITHUB-SURVEY (형GO · READ)** | **DOC_SURVEY** · wire=**False** — 형 「다음진행전 논문·미친개발자 GH 검토·배울점」. **채택문헌**: Thaler&Ziemba JEP1988(금액EV·Pwin불변) · Ziemba ARFE2023(luck-skill) · conscious selection(Chernoff/Cook-Clotfelter) · Significance2012 · Wang JdDM(생일1–31) · Stern&Cover JASA1989(**pick marginal 필요→우리 데이터 없어 적용否**) · Moffitt-Ziemba(신디케이트·소액발권과장금지) · Baker-Lee JRSS(조합shape·HOLD). **GH채택프로세스**: Hai4320/vietlot-suggestion(정직null·split-half) · lgpcarames/lottery_numbers(생일회피=몫EV) · kyr0/lotto-ai(fancy RNG 고백). **GH불신**: wiserguy opaque점수 · powerpredict DL. **결론**: 우리 3축(숙제/인기/몫EV)은 1티어와 정합 · 다음패치=①BLEND만·ge3금지 · Stern-Cover/LSTM/해외리스트/buy-the-pot **금지**. · `docs/benchmarks/20260810_KNEXT_ROUTE_LIT_GITHUB_SURVEY.json` · `reports/20260810_KNEXT_ROUTE_LIT_GITHUB_SURVEY.md` |
| **K-UI-TESTLOTTO-FOCUS-HOLD-OFF (형GO)** | **HOLD_OFF** — 형 「홀딩 챕 다시 풀어줘」. `lotto4.js` `ROK21_TESTLOTTO_FOCUS_HOLD=false` · 복원뷰=`predict`/`strategy-x`/`hyodo` · HOLD 배너 미표시 · 진입 시 예측 autoload 복원. 재홀딩=`true`. · **종료체크정정**: 보고서·벤치 파일명 `20260810_*`(구 `20260808_*` 오명 삭제). · `docs/benchmarks/20260810_KUI_TESTLOTTO_FOCUS_HOLD_OFF.json` · `reports/20260810_KUI_TESTLOTTO_FOCUS_HOLD_OFF.md` · 커서보고서 동기 |
| **K-UI-TESTLOTTO-FOCUS-HOLD** | **HOLD_OFF**(해제됨 · 원판정 HOLD_ON 기록 유지) — 구: 숨김 predict/strategy-x/hyodo · 기본 testlotto · autoload OFF |
| **K-BRAIN-INDEPENDENT-TUNE (형GO·패치승인후)** | **APPLY** — 형 「다음 진행·패치 잘됨」→ 뇌별 독립튜닝 1노브. **SCORE_WEIGHTS_BY_BRAIN** base 전뇌(0.40/0.25/0.35) → cand_A: stat**(0.25/0.35/0.40)** · markov/review**(0.55/0.20/0.25)**. 구간1100~1235 n136 seed42 · **축지표(ge3미사용)**: markov prefer_delta +0.226→**+0.249**(Δ+0.023) · review prize_delta −0.028→**−0.055**(Δ−0.027·더음수) · stat top15_hit 0.300→**0.305**. review 3구간 cand **전부음수**(base early는 양수였음). V1/V2 hint분리 유지. 롤백=전뇌(0.40/0.25/0.35). · `docs/benchmarks/20260808_KBRAIN_INDEPENDENT_TUNE.json` · `reports/20260808_KBRAIN_INDEPENDENT_TUNE.md` · `tools/_k_brain_independent_tune.py` |
| **K-BRAIN-INDEPENDENT-WIRE (형GO)** | **WIRE_CONFORMS** — 형 「3뇌 독립 · 공유=lotto_draws만 · 몰아주기도 뇌별」. **[A] hint 분리**: `HINT_SPEC_BY_BRAIN` stat=`(26,miss_pattern)` · markov=`(None,crowd_prefer)` · review=`(None,crowd_prize)` · `hint_shared=False` · probe1235 top5 전부 상이(stat15/28/31… · markov12/7/3… · review40/37/45…). V1~V5 **5/5**(dead_wire live · signal_top 뇌별 · RNG C7 · draws공유). pool `PREDICT_MODULES`→실뇌패키지(deprecated 래퍼 제거). **[B] EV게이트** 1100~1235 n136 · ge3미사용 · `prize_proxy_delta=−0.092741` → **MARGINAL** · early/mid/late 전부음수 `consistent=True` · STRONG 아님(과장금지). coordinator/`random.choices`/`_get_draws_before` 미접촉. 롤백 `K_CROWD_PREFER=0 K_PRIZE_EV=0`. · `docs/benchmarks/20260808_KBRAIN_INDEPENDENT_WIRE.json` · `reports/20260808_KBRAIN_INDEPENDENT_WIRE.md` · `tools/_k_brain_independent_wire.py` |
| **K-BRAIN-CROWD-RESTRUCTURE (형GO · 판단진행)** | **WIRE_SMOKE_OK** — 형 「과거학습 특성맞게 진행 · 흐름술사→선호번호 · 복습왕→금액뇌 · 엔진견고 · 학술벤치」. **역할**: `stat`=과거학습(당첨번호 숙제·패턴) 유지 · `markov`=**선호번호**(1등다수 회차+생일대 1~31) · `review`=**금액뇌**(저당첨자수·고번호·끝수0/8/9 비선호 → **당첨시 몫 EV**, P(win)↑ 비주장). **데이터한계**: 조합별 판매수 없음 → `first_winners`+`total_sales` 프록시 + 구조사전. **문헌**: Thaler&Ziemba JEP1988 · Ziemba ARFE2023 · Chernoff conscious selection. **배선**: `shared/crowd_signal.py` · 엔진 가중치만 `blend_weights`(STRENGTH0.55) · **`random.choices` 미수정** · `_get_draws_before` 유지. 롤백 `K_CROWD_PREFER=0`/`K_PRIZE_EV=0`. UI·registry·METHOD_TO_TAG(구명호환). 스모크 as_of1236: method 일치 · prefer_top≈저번호 · prize_top≈고번호. 과거학습 decay 튜닝은 게이트보류(이번 턴 범위 밖). · `docs/benchmarks/20260808_KBRAIN_CROWD_RESTRUCTURE.json` · `reports/20260808_KBRAIN_CROWD_RESTRUCTURE.md` |
| **K-STAT-HOMEWORK-FILL (형GO ①)** | **20/20 OK** · 회차 **1216~1235** · 298.3초 · 확정길(N숙제←1..N-1·채점N). **발견**: 발권 쿼터만 쓰면 **stat가 lotto_predictions 0장**일 수 있음 → 매회 `brain_filter=("stat",)` 로 숙제 5장 추가. 후: pred **200**(scored) · stat **100** · learn **3** · evolve **60** · pool **60** · warrant **20**. 명분예 1235 set5 적중3 · `1yHot/Cold`. 튜닝아님 · DB로컬만 · `docs/benchmarks/20260808_KSTAT_HOMEWORK_FILL.json` · `reports/20260808_KSTAT_HOMEWORK_FILL.md` · `tools/_k_stat_homework_fill.py` |
| **K-STAT-PASTLEARN-READY-CHECK (READ-ONLY)** | **방향 준비 · 기록 미준비** — 형 「확정 길로 패치 준비된 뇌인가?」 · **준비됨**: 워크포워드(`_get_draws_before` · target=`last+1`) · `ROK21_LEARN_CUTOFF`/`set_learn_as_of` 컨닝차단(미설정 시 learn 로드 `ValueError`) · 파이프 `transition(OFF)→engine(v2 ON via past_learn)→aux→past_learn soft→diversity` · `PAST_LEARN_WIRE=True` · ASSOC OFF · reasoning 문자열·`past_learn.tags` 존재(예 1235: `1yHot[…]`) · **미준비**: 리셋 후 `lotto_predictions=0` · `learn_state=0` · `hit_warrant_log=0` · `evolve_log=0` → 피드백·학습 boost·명분 누적 경로 무효(중립) · **확정 길 잠금**: N숙제 / 재료1..(N-1) / 채점 N / 깊은패턴=재료 · 다음=기록 채우기 먼저 · `reports/20260808_KSTAT_PASTLEARN_READY_CHECK.md` |
| **K-BRAIN-INDEPENDENCE-AUDIT (형GO · 버그사냥)** | **INDEPENDENCE_OK 14/14** (1216~1235 · READ-ONLY · DB 무기록) — 형 지시 「각 뇌별 독립적으로 예측번호 공유 X · 각 독립적으로 뇌별 몰아주기 · 각 뇌가 10세트 예측하는지 한번 더 버그를 찾아보자」 · **버그 2건 추가 발견·수정** — **⑥`brain_tag` 죽은 배선**: `repack_by_brain` 이 `number_scores(pool, hint, num_t, pos_t, ...)` 로 호출해 `brain_tag` 를 안 넘겼다 → `SCORE_WEIGHTS_BY_BRAIN.get(brain_tag or "", 기본값)` 이 항상 기본값으로 떨어져 **이번 턴에 만든 뇌별 가중치가 한 번도 조회되지 않았다**. 처음 hint 절제가 정확히 `+0.0000` 이던 것이 이 버그의 증상이었다(절제가 물리적으로 불가능). 다른 5개 호출부는 전부 `brain_tag` 를 넘기고 있었고 **발권 분석 경로 하나만** 빠져 있었다 → `brain_tag=tag` 추가 · **⑦hint 축 죽은 배선**: `HINT_SPEC_BY_BRAIN` 을 열었더니 B6 가 즉시 검출(호출자가 `hint_by_brain` 을 안 넘기면 무시) → `repack_by_brain` 이 spec 이 갈릴 때 **직접 만들게** 수정(3뇌 동일인 현재는 분기 미진입 = 비용·결과 무변화) · **죽은배선 탐지기 B6 신설**: 뇌별 dict 값을 바꿔 결과가 안 바뀌면 실패 처리 → 앞으로 같은 종류 버그를 자동 검출 · **실측 수치**: 3뇌 점수세트 번호 겹침 Jaccard **0.664~0.687**(공유 번호 14.2~14.5개) vs **무작위 기대 0.250** = 약 **2.7배** · hint 가중치를 0 으로 두면 **0.743 → 0.30**(−0.439) → **공유 hint 가 주원인 확정**(가중치 0.40) · 점수세트 번호의 자기 pool 출신 비율 markov 0.789 / stat 0.822 / review 0.794 = **약 20% 가 pool 밖에서 유입** · **깨지지 않은 것**: 뇌별 10세트 정확 · set_no 1~10 · 번호형식 · **pass0≠pass1**(내가 의심했던 「10세트가 실은 5세트」 버그는 없었다 · 3뇌 전부 난수 사용) · 뇌 간 동일세트 0건(pool·몰아주기 모두) · pool 슬롯 뇌별 2자리 확보 · RNG 독립 · 학습 교차오염 없음 · **hint 축 개방은 성적 무변화 실증**(`_k_hint_neutrality_check.py` — 공용 hint 결과 == 뇌별 hint 결과, 1233~1235 전부 일치) · `docs/benchmarks/20260808_KBRAIN_INDEP_AUDIT.json` |
| **K-BRAIN-RNG-INDEPENDENT (형GO · 배선수정)** | **WIRE_CONFORMS 9/9** (1216~1235 · 리셋 후 재검증) — 형 지시 「나머지 2뇌도 각 독립된 방법으로」 이행. **성적 주장 아님 → R38 게이트 대상 아님** · **결함④ RNG 오염**: `expand_pool` 이 `_live_candidates` 로 3뇌를 **한 난수 흐름에서 순차 호출** → 앞 뇌의 `random.choices` 소비량이 뒤 뇌 결과를 바꿨다(stat→markov). 발권경로 `coordinator._seed_independent_brain` 은 이미 뇌별 시드리셋이 되어 있었고 **pool 경로만 빠져 있었다** = 같은 뇌인데 경로에 따라 다른 세트. **수정**: `expand_pool` 이 `BRAIN_TAGS` 를 직접 돌며 뇌마다 `random.seed(_pass_seed(...))` · **결함⑤ pool·발권 불일치**: 구 pass0 은 `random.seed(seed)`(회차 무관)인데 coordinator 는 `42+draw_no` → pool 1~5 가 실제 발권 세트와 달랐다. **수정**: `_pass_seed(seed,draw_no,pass)=seed+draw_no+pass*10000` → **C8 검증으로 pool 앞 5세트 = 발권 5세트 일치 확인** · **뇌별 상수 구조 개방**: `POOL_SLOTS_BY_BRAIN` · `SCORE_WEIGHTS_BY_BRAIN` · `LEARN_EMA_BY_BRAIN` (**현재 값은 3뇌 전부 동일 = 성적 무변화** · 값 차별화는 게이트 통과 후) · **미해결(명시)**: `HINT_SHARED_ACROSS_BRAINS=True` — `_build_hint` 하나를 3뇌에 그대로 넘기며 `W_HINT=0.40` 이라 점수의 40%가 3뇌 동일. 뇌별 hint 는 「어느 신호가 어느 뇌에 맞는가」를 데이터로 정해야 하므로 성적 주장 = 범위 밖 · 검증 9/9: C1 뇌별분리 · C2 신호상위 · C2b 4·5이탈(**3뇌 전부 1.000**) · C3 3뇌동일 · C4 세트통째보존 · C5 결정성 · C6 미래참조없음 · **C7 뇌간RNG독립**(단독실행=합동실행) · **C8 pool1~5＝발권세트** · 동결 무접촉 · **발권경로 무변경** · `docs/benchmarks/20260808_KREPACK_SIGNAL_WIRE_VERIFY.json` |
| **K-PREDICT-RESET (형GO)** | **7,094행 삭제 · 원천데이터 보존** — 형 지시 「로또테스트에 백테스트한 모든 db 에 잇는 3뇌 예측을 삭제」 · 대상 `data/lotto_testlotto.db` **단독** · 백업 없음(형 지시) · 판정기준=스키마의 `brain_tag`/`brain` 컬럼 + 예측·백테스트 산출물 명시(추측 금지) · **삭제**: evolve_log 3549 · hit_warrant_log 1134 · lotto_predictions 1000 · backtest_draw_results 800 · pool_view_cache 600 · backtest_runs 4 · brain_learn_state 3 · brain_weights 3 · evolve_auto_state 1 · lotto_analysis 0 · brain_review 0 · **보존**: lotto_draws 1235 · draw_prize_tiers 6170 · draw_features 1234 · draw_detail 1234 · rare_bundle_catalog 213 · brain_page 3698(UI문구·brain_tag 있으나 예측 아님) · **rare_bundle_hits 1235 · transition_log 1134 = 회차 파생이라 3뇌 예측 아님 → 보존** · 삭제 후 `init` 이 brain_weights 3행·evolve_auto_state 1행을 **초기값으로 재삽입**(total_predictions=0 · last_updated_draw=0 · phase=idle → 학습·예측 내용 없음 확인) · DB 51.98MB · **레포 위생상 DB 커밋 안 함** · `docs/benchmarks/20260808_KPREDICT_RESET.json` · `reports/20260808_KPREDICT_RESET.md` |
| **K-REPACK-SIGNAL-WIRE (배선수정·형GO)** | **WIRE_CONFORMS 7/7** — 형 지시 「몰아주기가 정상 작동하게 패치」 이행. **성적을 올렸다는 주장이 아니라 「설계 의도와 코드가 어긋난 것」을 맞춘 수정** → R38 게이트 대상 아님(코드 판독으로 확정 가능) · **결함① 성적표 공유**: `RollingSignalLearner.update_from_pool` 이 `for _tag` 로 뇌 태그를 버리고 `pos_hit_ema`(1~10칸)·`num_hit_ema`(1~45칸) **한 장을 3뇌가 공유** → stat 3번 세트 성적에 markov·review 3번 세트 성적이 겹쳐 기록 = 뇌를 개선해도 신호가 전달 불가. **수정**: `dict[brain][slot]` 중첩 · `snapshot()` 도 중첩 반환 · `brain_signal(table, tag)` 해석기 신설(구형 단일표 통과·tag=None 이면 합산 호환) · **결함② 4·5 하드코딩**: `assemble_hybrid_p45_r123` 이 `for sn in (4, 5)` 로 **신호와 무관하게 set_no 4·5 를 항상** 집었다(4·5 는 20260804 백테스트 ablation 산물). **수정**: `signal_top_set_nos()` + `assemble_signal_top()` 신설 — 위치 EMA 상위 `POOL_SLOTS_PER_BRAIN=2` 개 선택(동점=set_no 작은 쪽·결정적) · 실측 **4·5 이탈률 markov 1.000 / review 1.000 / stat 0.900** → 신호가 4·5 를 가리키는 건 stat 20회 중 2회뿐이었음 · **결함③ markov 제외**: `HYBRID_P45_R123_BRAINS={stat,review}` 로 markov 만 pool 슬롯 0개 = 세트가 전부 번호로 녹음. **수정**: `SIGNAL_TOP_BRAINS=frozenset(BRAIN_TAGS)` 3뇌 동일 · **보존 슬롯 수(2)는 구 4·5 와 동수 유지** — 「몇 장 보존할지」는 성적 주장이 필요한 튜닝이라 범위 제외 · 검증 `tools/_k_repack_signal_wire_verify.py` 1216~1235(20회) **7/7**: C1 뇌별분리(3쌍 전부 non-identical·nonzero 슬롯 10/10/10) · C2 신호상위선택 · C2b 4·5이탈 · C3 3뇌 signal_top·슬롯[2] · C4 세트 통째보존(번호 완전일치) · C5 결정성 · C6 미래참조없음 · 부수: `build_pool_and_repack` 의 `hybrid` 메타가 구 상수를 보고하던 것 → `_assemble_meta()` 로 실배선 반영 · 동결(`random.choices`·`_get_draws_before`·boost상한) 무접촉 · **발권 경로(`coordinator`) 무변경** · `docs/benchmarks/20260808_KREPACK_SIGNAL_WIRE_VERIFY.json` · `reports/20260808_KREPACK_SIGNAL_WIRE_VERIFY.md` |
| **K-REPACK-SELECT-DIAG (stat 단독)** | **POOL_EQUALS_RANDOM · SELECT_SIGNAL_NOT_FOUND · REPACK_NET_LOSS(무효)** — 형GO(①고쳐놓고 나중 배선 · ①stat단독) · 회차 **53~1235(n=1183) × seed 5개 = 5915 표본** · walk **309.2초** · **⑴ 최상위 발견(전제 붕괴)**: `oracle_top5`(pool 10세트 중 실제 상위5) ge3 **0.215216** vs **무작위 10장** null **0.214337**(±0.023385) → **초과 False**. 몰아주기 5장 **0.119019** vs 무작위 5장 null **0.113624** → **초과 False**. ⇒ 20260804 DECOMPOSE 의 「pool최고 0.245 vs 몰아주기 0.125 = 좋은 세트를 놓침」은 **오독**이었고 실체는 **10장 vs 5장 장수 산수** · **⑵ 놓침률**: pool에 ge3 있던 회차 **1273**(0.2152) · 몰아주기가 낸 회차 **704**(0.1190) · 놓침 **871** / 구제 **302** / 순 **−569** · pool최고−몰최고 평균격차 **0.319696** — 단 ⑴ 때문에 **결함 아님**(10장 중 5장만 발권하는 산수) · **⑶ 선별력 전무**: 사전특성 11개(score_sum·score_rank_mean·dup_count·hint_sum·numema_sum·pos_ema·confidence·sum_nums·odd_cnt·zones·max_consec) **Spearman 최대 |0.0088|**(hint_sum) · 나머지 전부 <0.008 · 특성 상위5 선별 전략 **11개 모두 몰아주기 이하**(최선 feat_pos_ema 0.1185 Δ**−0.000507**) · 무선별 대조군 `setno_1_5` 0.1173 도 동일 · **⑷ R38 게이트**: n=1183 · 탐색셀 11 · 단일MDD **0.025575** · 선택보정 p95 **0.032967** → **UNDECIDABLE** · **⑸ 결론**: 정답을 안 보고 pool 세트를 고르는 신호는 **이 특성집합 안에 없고**, 애초에 pool 자체가 무작위와 구별 불가 → **몰아주기 선별 재설계 근거 없음 · 구조 유지**(바꿀 근거도 되돌릴 근거도 없음) · 남은 길 = 당첨금(인기회피) 축 · **⑹ 구조 사실 확인**: 실제 발권경로(`coordinator`)는 **3뇌×5세트=15장→동적쿼터 5장** 이며 `repack_by_brain` 미사용 — 몰아주기는 `evolve_log`·`pool_view_cache` 분석경로 전용 · R38·R39 준수 · wire否·상수무변경·READ-ONLY · `docs/benchmarks/20260808_KREPACK_SELECT_DIAG.json`(+`_raw`) · `reports/20260808_KREPACK_SELECT_DIAG.md` |
| **K-SEED-AVERAGE-DESIGN** | **NOISE_CUT_NOT_ESTABLISHED** — 형GO ② · 회차 **936~1235(n=300)** · **outer 10묶음 × 안쪽 seed 8개** WF · walk **1345초** · 설계=같은 회차를 R번 뽑아 합친 뒤 5장 결정 · 두 합치기 방식 병행: `hybrid`(R개 pool 이어붙여 현행 `repack_by_brain`) / `score`(평균 점수순위로 5장 전부 · pool 슬롯 미사용) · 학습기는 **R=1 pool 로만** 갱신(현행 경로와 학습상태 동일 유지) · **⑴ √R 법칙 불성립**: stat·hybrid σ R1 **0.022420**→R2 0.012667→R4 0.014514→R8 **0.017075**(비 **1.313** · log-log 기울기 **−0.0982** vs 예측 −0.5) · stat·score R1 **0.019610**→R8 **0.014256**(비 **1.3756** · 기울기 **−0.1279**) · markov 기울기 **+0.0164**(감소 전무) · review·hybrid **+0.1848** · **⑵ R39 구분불가**: stat·hybrid 관측차 0.005345<임계 0.013019(필요 outer **55**) · stat·score 0.005354<0.011200(필요 **41**) · markov 필요 **436** · **⑶ 분해 σ²=A+B/R**: stat 평균화로 지울 수 있는 몫 **0.63**(A=0.011~0.013 잔존 = 학습기 경로) · markov·review·hybrid 는 B=0(제거 가능분 없음) · **⑷ 손익(결정적)**: 이항SE **0.018322**(n300) 는 못 줄이므로 총잡음=√(이항²+seed²) · R8 판정해상도 이득 **1.156배** / 비용 **8배** / 이득·비용 **0.1445** · seed 잡음을 **0으로 만들어도 상한 1.4647배** · **⑸ 등가회차 역산**(잡음바닥 24seed 모형 b≈0 → 총잡음∝1/√n): R8 총잡음 0.023215 = **등가 n 400.9** · 반복비용 2400 vs 회차비용 400.9 → **평균화 과지불 5.99배**(R2 1.37배 · R4 2.88배) · **⑹ 적중 무변화**: stat 최선 `score_R8` ge3 0.1197 vs 현행 0.1087 Δ**+0.011** · R38 게이트 **UNDECIDABLE**(단일MDD 0.050787 · n300 · 탐색셀7) · **결론=배선하지 않음** · 다음 표적은 뽑기가 아니라 **평균되지 않는 학습기 경로** · R38·R39 준수 · wire否·상수무변경·READ-ONLY · `docs/benchmarks/20260808_KSEED_AVERAGE_DESIGN.json`(+`_raw`) · `reports/20260808_KSEED_AVERAGE_DESIGN.md` |
| **K-STAT-NOISE-SOURCE** | **PREMISE_NOT_ESTABLISHED** — 회차 **836~1235(n=400 · step1)** · seed **24개** · 수집 668.9초(원자료 캐시 `_RAW`) · **⑴ 유입점 확정**: stat 가중치 seed무관 **True** · markov **True** · `repack_by_brain`/`number_scores`/`assemble_hybrid_p45_r123` 기본인자 결정적(코드확인) → **잡음은 오직 `expand_pool`→`predict_sets` 뽑기에서만 유입** · **⑵ 구조차 실재**: 유효후보수(퍼플렉시티) 중앙값 stat **40.0192**(평균39.905 · 36.9073~42.1114) vs markov **24.9844**(24.9794~24.9908) = **1.6018배** · stat=45개 전체추출 / markov=방문상위25개 · **⑶ 단순연결 반증**: pool_tvd markov **0.464213** > stat **0.373618** > review **0.356604** 인데 파이프라인 seed_std 는 markov **0.006762** 최소 → 생성단계 흩어짐 ≠ 결과 흔들림 · 6개 지표(brain_level_ge3_std·pool_tvd·presence_std·ticket_share·union_jaccard·output_perplexity) **전부 순서 불일치** · **⑷ 전제 붕괴(핵심)**: 출발 전제였던 뇌별 팽창차는 seed 유한개 측정값 · σ의 표준오차 σ/√(2(k−1)) 적용 시 **구분가능쌍 0/3** (seed10 기준 필요seed 16/32/113 · **seed24 재측정 후에도 0/3 유지** · 필요seed 58/1903/83) · 이번 독립측정 뇌수준 ge3 std 도 stat **0.016040**/markov **0.015184**/review **0.013584** 로 3쌍 전부 구분불가(필요seed 1280/142/313) → **'stat만 시끄럽다'는 근거 없음 · stat 전용 잡음대책 보류** · **⑸ 반사실(뽑기 제거)**: 가중치 상위 결정적절단 = 흔들림 **정확히 0** · 짝지은 부트스트랩 B**20000**(같은 회차 → 난이도 상쇄) stat Δge3 **+0.006146** CI[−0.024167,+0.038854] p**0.7156** · markov **−0.005833** CI[−0.036146,+0.026148] p**0.6987** → **손해 근거 없음**(이득 근거도 없음) · 독립표본 R38 게이트 **UNDECIDABLE**(MDD 0.043983 · n400) · 한계=결정적절단은 세트간 번호 비중복이라 발권 직접이식 불가 · **⑹ 신설 규칙**: 표준편차 비교 전 σ/√(2(k−1)) 선계산 의무 · R38 준수 · wire否·상수무변경·READ-ONLY · `docs/benchmarks/20260808_KSTAT_NOISE_SOURCE.json`(+`_RAW`) · `reports/20260808_KSTAT_NOISE_SOURCE.md` |
| **K-STAT-SEED-NOISE-FLOOR v2 (seed24 · 이전 seed10판 대체)** | **FLOOR_NOT_ESTABLISHED** — 회차 **53~1235(n=1183)** · seed **24개** 전구간 WF · walk **1453.4초** · **stat 전구간 ge3 0.094675~0.130178 폭 0.035503 std 0.010371**(seed10판 0.011754 에서 하향) · null 0.113624 · **잡음곡선**(창별 seed표준편차/이항SE/팽창): n50 **0.040824**/0.044881/**0.9096**(23타일) · n100 0.028467/0.031735/0.897(11) · n200 0.021343/0.022440/0.9511(5) · n400 0.016131/0.015868/1.0166(2) · n800 0.012928/0.011220/1.1523(1) · n1183 0.010371/0.009227/**1.124**(1) · **분산모형 a²/n+b²(가중R²=0.998631) → a=0.285875**(잭나이프 CI [0.267716,0.303249] · 견고) · **b=0.005087** · **⚠ 바닥 b 의 잭나이프 SE=0.006698 > 점추정 · 95% CI [−0.008244, 0.018012] → 0 과 구별 불가**(재적합 24/24 양수 · 개별값 0.001656~0.006895 · b≥0 경계제약이라 대칭CI는 '0이다'가 아니라 '구별불가'로만 해석) · **핵심 철회**: seed10판의 「FULL-WF Δ+0.0047 < 바닥 0.010127 → 표본 늘려도 영원히 판정 불가」는 **근거 상실**. 올바른 표현 = **「가용 데이터(n=1183)로는 판정 불가」**(전구간 seed std 실측 0.010371 · 보정 단일MDD 0.037197 대비 Δ+0.0047 은 한참 미달) · **게이트 보정 갱신**(총SE=√(p0(1−p0)/n+a²/n+b²)): n50K10 0.16→**0.216106**(×1.3507) · n100K10 0.11→0.149096 · n200K9 0.08→0.109189 · n500K9 0.05→0.069641 · n1183K1 0.021978→0.031965(×1.4544) · **뇌별**: stat std 0.010371/팽창1.124 · markov 0.007963/0.863 · review 0.009915/1.0746 — **R39 구분가능쌍 0/3**(stat↔markov 차0.002408<임계0.003779 필요seed**58** · stat↔review 0.000456<0.004146 필요**1903** · markov↔review 0.001952<0.003675 필요**83**) → **서열 인용 금지** · NOISE-SOURCE 독립측정과 일치 · R38·R39 준수 · wire否·상수무변경 · `docs/benchmarks/20260808_KSTAT_SEED_NOISE_FLOOR.json`(+_raw) · `reports/20260808_KSTAT_SEED_NOISE_FLOOR.md` |
| **R39 (측정 정밀도 선검증 · 신설)** | **ADOPTED** — 공용모듈 `tools/k_precision.py` · σ̂ 의 표준오차 **σ/√(2(k−1))** 를 표준편차 비교 **전에** 계산 강제 · 결과를 벤치 JSON **`precision_check`** 키에 기록 · 구분불가 = "차이없음"이 아니라 **"모른다"** → 구분가능쌍 0이면 서열 인용·후속작업 금지 · 임계로 쓰이는 추정치(잡음바닥 등)는 **잭나이프 신뢰구간 병기** 의무 · **자기검증 7/7**(몬테카를로 k=5/10/24/60 예측오차 0.14/0.055/0.037/0.004 · 필요표본 자기일관성 · 표본↑→임계↓ 단조성 · seed10 뇌별서열 0/3 재현) · RULES_FIXED R39 등재 · `tools/k_precision.py` |
| **K-GATE-COMPLIANCE (R38 신설)** | **COMPLIANT** — 게이트를 공용모듈 `tools/k_gate.py` 로 승격(형 GO ①) · `gate_block()` 결과를 벤치 JSON `decision_gate` 키에 기록 **강제** · 등급 4종 DECIDABLE/SELECTION_SUSPECT/UNDECIDABLE/NOISE_SELECTION_CONFIRMED · **자기검증 8/8 통과**(null 0.1137·0.3036 재현 · n50 SE 0.044881 · 단일MDD 0.124403 · K10 p95 0.16 · win26/mix0.8 재판정=NOISE_SELECTION_CONFIRMED) · 준수검사 `tools/_k_gate_compliance.py` 벤치 **184건** 스캔 · 비교성 133 · legacy **132건 면제**(기록물 소급수정 금지) · 위반 **0** · **강제 실동작 검증**: 게이트없는 프로브 투입 시 VIOLATION 탐지 + **exit=1** 확인 후 제거 · DECISION_GATE 벤치 리팩터 후 수치 **완전 동일**(null_analytic·ruler·retro_audit·order_invariance 전부 IDENTICAL) · `docs/benchmarks/20260808_KGATE_COMPLIANCE.json` · `reports/20260808_KGATE_COMPLIANCE.md` |
| **K-STAT-DECISION-GATE** | **RULER_TOO_COARSE** — null 해석적 검증: 초기하 1장 P(≥3)=**0.02383408** → 5장최고 **0.113624** vs 측정 **0.1137**(일치) · 15장 **0.303607** vs **0.3036**(일치) → null 기준선 신뢰 확정 · **눈금표**: n50 SE**0.044881** 단일MDD**0.124403** K10선택보정p95**0.16** / n100 **0.087966**·K10 **0.11** / n200 **0.062202**·K10 **0.08** / n1182 **0.025586**·K10 **0.032149** · **소급감사**: TUNE-ENGINE(win26/mix0.8 · n50·K10·Δ+0.16 = p95와 동일 · holdout 0.14 = null+0.0264 붕괴 · fusion Δ0) → **NOISE_SELECTION_CONFIRMED** / DETAIL-TUNE(score Δ+0.0008) → UNDECIDABLE / SEED-DIAG(폭 0.14, seed std 0.047749 > 이론SE 0.031735) → **NOISE_FLOOR** / FULL-WF(n1182 Δ+0.0047 vs MDD 0.025586) → UNDECIDABLE · **순서불변 증명**: 1→N vs N→1 최대차 **2.429e-17**(동일) · 리스트 실제역전 시 최대차 0.007995=시간축손상 · **문제→답 프레임**: `transition_log` n1134 이미구현·채점완료 · nopeek mean**2.007407** ge3**0.274074** < 무작위**0.311375** / peek 2.177778·0.392593 → 컨닝차이가 전부 · wire否·상수무변경 · `docs/benchmarks/20260808_KSTAT_DECISION_GATE.json` · `reports/20260808_KSTAT_DECISION_GATE.md` |
| **K-PAST-LEARN-EV-RELABEL** | **SELECTION_YES_TAGS_NO_AXIS_CANDIDATE** — 종속=1등당첨자수 `first_winners` · n**1131**(회차105~1235) · 분산/평균**2.95**→NB2(α=**0.06621**) · offset=log(total_sales) · 교란=시간spline6+연주기4+이월 · permutation score test B**5000** · **전역 max|z|=4.381 FW p=0.0004**(인기편향 실증) · 유의축 `sum_z` β**−0.0575**(z−4.38) · `n_le22` β**+0.0463**(z+4.19) = 동일 저번호·저합축(상관−0.876) · 태그 전부 FW 무의미: `t_carry` β−0.0337(z−2.09 pFW0.28) · `t_hot1y` β**+0.0243=인기(EV역방향)** 4시대 전부 · `t_overdue` β−0.0539(z−0.96) · `t_cold1y` β−0.0136(z−0.66) · **soft태그 EV재정의 지지=아니오** · 후보축 전후반 엄격재현 미달(전반 z−1.10/후반 −4.37 · 시대부호 3/4) → 전향적 검증 필요 · wire否·코드/가중 무변경(w=0) · `docs/benchmarks/20260808_KPAST_LEARN_EV_RELABEL.json` · `reports/20260808_KPAST_LEARN_EV_RELABEL.md` |
| **K-PAST-LEARN-AUDIT-DIMS** | **AUDIT_DONE** — 전구간 감사+차원+외부AI자문 · 실행가능 잔여 **6건**(①seed full-range ②EV전향로그 ③cycle_gap_boost 단독AB ④STATUS§5 드리프트정정 ⑤bin taxonomy ⑥cold-free live검증) · 미도구화 아이디어 7건 · 되살리기금지 8건 · 문서모순 4건 · 차원 셀당관측 1차**164.7**/2차**18.7**/3차**1.74**/4차0.12/6차0.0002 → **차원상승=표본분할**(pair/triple NOISE는 공정추첨의 정상결과) · 자문 채택: "recency=정보없음" 문구 축소 · nested WF·block bootstrap 미충족 · 해외문헌으로 한국인기도 대체금지 · `docs/benchmarks/20260808_KPAST_LEARN_AUDIT_DIMS.json` · `reports/20260808_KPAST_LEARN_AUDIT_DIMS_ADVISORY.md` |
| **K-PAST-LEARN-SCORE-RULE-DIAG** | **NO_SKILL_VS_NULL** — n**500**(736~1235) · 셀**15** log-score 전부 null(**3.8067**) 미달 · 현행 L0.005/S0.05=**3.8982**(skill **−0.0240**) · 최선 L0.0005/S0.02=**3.8875**(**−0.0212**) · 균등이탈L1↔score **r=0.9854** · 보정χ²=**32.42**(df44 p≈**0.90**, 기각못함) · PBO=**0.0** · 기대최대**0.0306**≥실측**0.0107** · hot1y=인기축(EV역방향) 경고 · wire否·상수불변 · `docs/benchmarks/20260808_KPAST_LEARN_SCORE_RULE_DIAG.json` · `reports/20260808_KPAST_LEARN_SCORE_RULE_DIAG.md` |
| **K-PAST-LEARN-DETAIL-KEEP** | **KEEP_BASE** — 형GO · decay L**0.005**/S**0.05** 확정 · 후보0.01 **미채택** · tipster/LSTM/ASSOC wire否 · `docs/benchmarks/20260808_KPAST_LEARN_DETAIL_KEEP.json` · `reports/20260808_KPAST_LEARN_DETAIL_KEEP.md` |
| **K-PAST-LEARN-YT-BENCH** | **DOC_SURVEY** — 신뢰게이트 통과 4축(조코딩LSTM·Numberphile·KYT필터·covering논문) · tipster기각 · 적용사례 A1~A4 전부 wire否 · `docs/benchmarks/20260808_KPAST_LEARN_YT_BENCH.json` · `reports/20260808_KPAST_LEARN_YT_BENCH.md` |
| **K-PAST-LEARN-DETAIL-TUNE** | **CANDIDATE→KEEP** — 틀 win26/mix0.8 · 후보 L0.01 기각 · `docs/benchmarks/20260808_KPAST_LEARN_DETAIL_TUNE.json` · `reports/20260808_KPAST_LEARN_DETAIL_TUNE.md` |
| **K-PAST-LEARN-FRAME-DONE** | **FRAME_LOCKED** — 과거학습 기본 틀 잠금(세부 전) · win**26**/mix**0.8** · soft/ASSOC/transition OFF · `framework_snapshot` · smoke OK · `docs/benchmarks/20260808_KPAST_LEARN_FRAME_DONE.json` · `reports/20260808_KPAST_LEARN_FRAME_DONE.md` |
| **K-PAST-LEARN-TUNE-ENGINE-APPLY** | **PASS** — `V2_SHORT_WIN=26`/`V2_SHORT_MIX=0.8` 적용 · tune n50 ge3=**0.28**/mean**1.88**(재현) · holdout(1085~1134) ge3=**0.14**/mean**1.72** · fusion n200 ge3=**0.135** Δ**0** · 롤백52/0.6 · `docs/benchmarks/20260808_KPAST_LEARN_TUNE_ENGINE_APPLY.json` · `reports/20260808_KPAST_LEARN_TUNE_ENGINE_APPLY.md` |
| **K-PAST-LEARN-TUNE-ENGINE** | **CANDIDATE→APPLIED** — seed n50 · base(win52/mix0.6) ge3=**0.12**/mean**1.78** · 후보 **win26/mix0.8** ge3=**0.28**(Δ**+0.16**) · `docs/benchmarks/20260808_KPAST_LEARN_TUNE_ENGINE.json` · `reports/20260808_KPAST_LEARN_TUNE_ENGINE.md` |
| **K-PAST-LEARN-TUNE-SOFT** | **KEEP_BASE** — seed(`42000+dno`) 15셀 **전부** ge3=**0.12** mean=**1.78** · soft conf 노브→발권불변 · unseeded↑=RNG잡음 · 상수 w**0.12**/cap**3.0** 유지 · applied=False · `docs/benchmarks/20260808_KPAST_LEARN_TUNE_SOFT.json` · `reports/20260808_KPAST_LEARN_TUNE_SOFT.md` |
| **K-PAST-LEARN-WIRE** | **PASS** — `past_learn.py` WIRE·engine v2 ON · ASSOC soft **OFF** · transition OFF · method=`과거학습` · solo n50(1035~1084) ge3=**0.14** mean_best=**1.58**(unseeded) · 롤백`K_PAST_LEARN=0` · `docs/benchmarks/20260808_KPAST_LEARN_WIRE.json` · `reports/20260808_KPAST_LEARN_WIRE.md` |
| **K-STAT-NUM-ASSOC-FULL** | **NOISE_LIKE** — n**1035** meanL**0.998**(Δnull**-0.004**) · union15**5.207**(Δ**-0.048**) · top1 Δ**-0.008** · thr스윕 전부 null이하 · wire否 · `docs/benchmarks/20260808_KSTAT_NUM_ASSOC_FULL.json` |
| **K-STAT-NUM-ASSOC-SAMPLE** | **MEASURED** — n**30**(recent10+rand20) meanL=**1.009** · top1_hit=**0.103**(&lt;null0.133) · carry**0.533** · wire否 · `docs/benchmarks/20260808_KSTAT_NUM_ASSOC_SAMPLE.json` |
| **K-STAT-NUM-ASSOC** | **MEASURED** — 번호→다음회 lift · 연도별=LOW_PRIORITY · 1235 meanL≈null · multi**34**(6표) · wire否 · `docs/benchmarks/20260808_KSTAT_NUM_ASSOC_1234.json` |
| **K-STAT-NUM-NEXT-FREQ** | **MEASURED** — anchor**1234** `[1,15,19,31,35,43]`→1235 · carry`[15,43]` · next-top15∩all6=`[34]` · wire否 · `docs/benchmarks/20260808_KSTAT_NUM_NEXT_FREQ_1234.json` |
| **K-BRAIN-RENAME-STAT** | **PASS** — 표시명 `통계요정`→**과거학습** · tag=`stat` 유지 · 구명 METHOD_TO_TAG 호환 · `docs/benchmarks/20260808_KBRAIN_RENAME_STAT.json` |
| **K-YT-FILTER-BENCH** | **DOC_SURVEY** — MAX**1235** · sum100–180=**0.802** · 연번=**0.517**(≈null) · 끝수=**0.780** · 이월main=**0.613** · YT AND=**0.202** · wire否 · LSTM기각유지 · `docs/benchmarks/20260808_KYT_FILTER_BENCH.json` · `reports/20260808_KYT_FILTER_BENCH.md` |
| **20260807 세션보고서** | **DONE** — `reports/20260807_ROK21_SESSION_STATUS.md` · 커서보고서 동기 · transition→HIT-WARRANT-ATTACH 마감요약 |
| **K-TRANSITION-HIT-WARRANT-ATTACH** | **PASS** — `hit_warrant_log` n**1134** · evolve.note 부착**3402** · weight=0 유지 · WIRE OFF · `docs/benchmarks/20260805_KTRANSITION_HIT_WARRANT_ATTACH.json` |
| **K-TRANSITION-HIT-WARRANT** | **CATALOG** — n_draws**1134** · explained**0.545**/unexplained**0.455** · carry**0.136** · trans_top15**0.333**(≈null) · consec**0.211** · STABLE · wire否 · `docs/benchmarks/20260805_KTRANSITION_HIT_WARRANT.json` |
| **K-TRANSITION-FUSION-N200** | **ROLLBACK** — fusion n200(1035~1234) ge3=**0.135**(27) mean_hit=**1.715** · Δbaseline**0** · period STABLE · `TRANSITION_V1_WIRE=False` 적용 · `docs/benchmarks/20260805_KTRANSITION_FUSION_N200.json` |
| **K-TRANSITION-STEP4-WIRE** | **PASS**(smoke) · 당시 ON · solo n50 ge3=**0.06** mean_best**1.22** · fusion재검증→ROLLBACK · `docs/benchmarks/20260805_KTRANSITION_STEP4_WIRE.json` |
| **K-TRANSITION-STEP3-DESIGN** | **DESIGN_HOLD** — nopeek mean**2.007** · FULL-ho**2.178** · replace=HOLD · `docs/benchmarks/20260805_KTRANSITION_STEP3_DESIGN.json` |
| **K-TRANSITION-STEP2-VERIFY** | **PASS** — table_ok · collect mean**1.998**/std · FULL **2.171806** match · period STABLE · wire否 · `docs/benchmarks/20260805_KTRANSITION_STEP2_VERIFY.json` |
| **K-TRANSITION-COLLECT-DESIGN** | **PASS** — table=`transition_log` · backfill 101~1234 n**1134** · collect mean≈**1.998**(N→N+1) · FULL재현 **2.171806** match · hook stop등록 · wire否 · `docs/benchmarks/20260805_KTRANSITION_COLLECT_DESIGN.json` |
| **K-TRANSITION-CURSOR-BRIEF** | **DOC** — **[CURSOR]** 외부AI 종합 · `CURSOR_BRIEF_FOR_EXTERNAL_AI.md` + **`DIRECTION_BRIEF_CURSOR.md`(SSOT)** · JSON author=Cursor |
| **K-TRANSITION-DISCUSS** | **DOC** — 1234→1235 팩트체크(carry·212·hit2 일치) · 무작위5+1234 단건 hit全**2** · 로드맵=검증완료→stat설계 · wire否 · `reports/20260805_KTRANSITION_*.md` · `docs/benchmarks/20260805_KTRANSITION_RANDOM_SAMPLE.json` |
| **K-TRANSITION-FULL** | **STRONG** — sim_k2 n**1135** mean_hit**2.172** Δ**+0.172** · k3 n**811** Δ**+0.065** MARGINAL · k4 n**0** · carry1235=[15,43] · brain_replace=**보류(수집후)** · wire否 · `docs/benchmarks/20260805_KTRANSITION_FULL.json` |
| **K-ASSOC-RULE-DIAG** | **NOISE** — STEP1 maxδ**0.084**<p95**0.117** · STEP2**0.45**<**0.559** · STEP3**0.667**<**0.867** · SIGNAL 0/3 · assoc wire否 · `docs/benchmarks/20260805_KASSOC_RULE_DIAG.json` |
| **K-NEIGHBOR-MATCH** | **NOISE** — rolling top15 hit≥3 =**0.23** < 무작위**0.311**(Δ**−0.081**) · mean_hit**1.91**<2.0 · HIGH maxJ≈mid → pool실패 · carry[15,43] 재출현**0.139**≈rand · neighbor wire否 · `docs/benchmarks/20260805_KNEIGHBOR_MATCH.json` |
| **K-EARLY-DIAG** | **STRUCTURAL** — ge3 early**0.138**/mid**0.150**/late**0.117** · coldΔ early**+0.005**/mid**+0.017**/late**−0.001** · pool entropy 거의同 · early단독붕괴否 · early전용wire 근거약 · `docs/benchmarks/20260805_KEARLY_DIAG.json` |
| **K-COVER-DIAG** | **NORMAL** overlap Jaccard**0.108**(기대0.122) · unique**20.7**<기대26.5 · cold-free replace Δge3**+0.030** IMPROVE(n**160**) · cover_wire否 · cold_free_add 후보 · `docs/benchmarks/20260805_KCOVER_DIAG.json` |
| **K-COLD-EXCLUDE-DIAG** | **MARGINAL** — k5 best Δ**+0.007** (clean**0.037**/all**0.030**) · k3**+0.006** · k7**+0.003** · early k5**+0.005** · VIABLE미달 · wire HOLD · `docs/benchmarks/20260805_KCOLD_EXCLUDE_DIAG.json` |
| **K-EMA-MARKOV-DIAG** | **NOISE** — H8 mean_hit**2.014** Δ+0.014 p**0.336** · H26**1.996** · H78**1.965** · div median-split Δ**0.005** · rescore **비권고** · `docs/benchmarks/20260805_KEMA_MARKOV_DIAG.json` |
| **K-REVIEW-QUOTA-SIM** | **BEST=A** — live predict_sets·3seed n200 · A**0.128** > B/C**0.127** > D**0.123** > E**0.118**(DEGRADED) · review↑ 이득無 · FIXED=None 원복 · `docs/benchmarks/20260805_KREVIEW_QUOTA_SIM.json` |
| **K-STAT-SEED-DIAG** | **HIGH_SENSITIVITY** — N100·5seed · stat range**0.14**(0.09~0.23) · markov**0.10** · review**0.03=STABLE** · pool **DIVERSE** · quota↑ **unsafe** · `docs/benchmarks/20260805_KSTAT_SEED_DIAG.json` |
| **K-QUOTA-D-WIRE** | **FAIL** — 슬롯2/3/0 발권OK · n100 avg ge3=**0.10** · full**0.115** · 하드롤백 `BENCH_FIXED_QUOTA=None` · fusion**0.135**복원 · 원인=PREP(hybrid repack)≠live(predict_sets) · `docs/benchmarks/20260805_KQUOTA_D_WIRE.json` |
| **K-PATCH-1235-PREP** | **MEASURED** — quota A**0.135**/B**0.155**/C**0.155**/D**0.170**(repack시뮬) · 후보=B·C·D · PMI/B/D기각 · wire=False · `docs/benchmarks/20260805_KPATCH_1235_PREP.json` |
| **K-PATTERN-BC-MEASURE** | **MEASURED** — B: odd_k thr**2**/cur**1** · zone thr**115**/cur**73**(mix지배) · sum_tier thr**3**/cur**5**=임박 · C: top mean**0.463**/frac_ge2**0.070** vs bottom mean**0.070**/frac_ge2**0.0016** · B=**MODERATE** C=**STRONG** · wire=False · `docs/benchmarks/20260805_KPATTERN_BC_MEASURE.json` |
| **K-GENSPARK-COMPRESS-RECOVER** | **PASS** — `GENSPARK_COMPRESS_RECOVER.md` R37자동(붙여넣기+증거체인) · 채팅기억불신·JSON재페치 · EXTERNAL_START/AI_COLLAB§2·§6 · `reports/20260805_GENSPARK_COMPRESS_RESUME.md` |
| **K-PATTERN-OWN-V1** | **MEASURED_PARTIAL** — A accel(neg≈0.49) · D slot bias frac≥4=**0.542** · E carry priorΔ≈**0** · F high→low wait mean**3.21** · B/C→**K-PATTERN-BC-MEASURE**로 승격실측 · `docs/benchmarks/20260805_KPATTERN_OWN_V1.json` |
| **K-SIGNAL-TAXONOMY-V1** | **DOC_SURVEY** — L1 전수w+deviation(consec_3plus th**0.0563**/emp**0.0543**) · L3 PMI 990쌍·top(11,21) pmi**0.421** · set_pmi mean**−0.138** · L4 birthday/sum/consec 스펙 · score w*=**0** · `docs/benchmarks/20260805_KSIGNAL_TAXONOMY_V1.json` |
| **K-LIVE-QUICK200-RESET** | **MEASURED** — preds**5910**+cache**606**+learn 삭제 후 WF · fusion ge3=**0.135**(27/200) mean**1.715** · hybrid ge3 stat**0.165**/markov**0.150**/review**0.130** · rare진단 ultra율**0.233**(WIRE OFF) · `docs/benchmarks/20260805_KLIVE_QUICK200_RESET.json` |
| **K-RARE-FILTER-PREP** | **PASS** — R0 DESIGN · R1 TAXONOMY · R2 MEASURE 1~1235 · R3 TAG_SPEC · `rare_annotate.py` WIRE=**False** · signal_pool 삽입점 주석만 · 등확률·컨닝금지·당첨P↑비약속 · `docs/benchmarks/20260805_KRARE_FILTER_DESIGN.json` |
| **K-EVOLVE-VIRTUAL-1235** | **PASS** — 확정회차 가상생애 · live hybrid(`hy_p45_r123`)+mean · λ/cover OFF · actual`[6,7,11,15,39,43]` · warrant(consec1·carry2·odd5) · SCORE best stat**2**/markov**1**/review**2** · schema3 · `docs/benchmarks/20260805_KEVOLVE_VIRTUAL_1235.json` |
| **K-EVOLVE-AUTO-S4** | **PASS** — `--ops` · G1 `EVOLVE_AUTO=1` 필수 · phase=`ops` · SCORE갭없음·1236캐시warm skip · mean feedback경로(기존·predictions없으면 no-op) · λ/covering OFF · `docs/benchmarks/20260805_KEVOLVE_AUTO_S4.json` |
| **K-EVOLVE-AUTO-S3** | **PASS** — `--apply-predict` · PREDICT **1236** pool_view_cache · SCORE갭 없음 · feedback미실행 · `docs/benchmarks/20260805_KEVOLVE_AUTO_S3.json` |
| **K-EVOLVE-AUTO-S2** | **PASS** — `--apply-score` · draw**1235** cache→evolve_log 3뇌 · PREDICT/feedback 없음 · weight=0 · `docs/benchmarks/20260805_KEVOLVE_AUTO_S2.json` |
| **K-EVOLVE-AUTO-S1** | **PASS** — `evolve_auto.tick(dry_run)` · auto_state 테이블 · 계획 SCORE/PREDICT · apply 거부 · EVOLVE_AUTO=0 · `docs/benchmarks/20260805_KEVOLVE_AUTO_S1.json` |
| **K-EVOLVE-AUTO-DESIGN** | **DOC** — 1236~ 파이프 설계 · S0~S4실장 · EVOLVE_AUTO기본0 · λ/covering wire 금지 · `reports/20260805_KEVOLVE_AUTO_DESIGN.md` |
| **K-PAIR-COVER** | **HOLD** — as_of 희소쌍 covering n200 · ge3 stat**0.155**(−0.01)·markov**0.105**(−0.025)·review**0.115**(−0.02) · WIRE=False · `docs/benchmarks/20260805_KPAIR_COVER_survey.json` |
| **K-STRUCTURE-COVER** | **HOLD** — sum/zone/odd/consec covering n200 · ge3 stat**0.145**(−0.02)·markov**0.085**(−0.045)·review**0.085**(−0.05) · WIRE=False · `docs/benchmarks/20260805_KSTRUCTURE_COVER_survey.json` |
| **K-MATH-PATTERN-WARRANT** | **FOUND** — draw1~1235 n=1235 · 명분10(연속·carry·합·존·쌍·overdue…) · 예측백테아님 · 확률만論 미사용 · `docs/benchmarks/20260805_KMATH_PATTERN_WARRANT.json` |
| **20260805 세션보고서** | **DONE** — `reports/20260805_ROK21_SESSION_STATUS.md` · 커서보고서 동기 |
| **K-EVOLVE-FEAT-LAM-REVAL** | **HOLD** — full n1182 review λ0.3 ge3=**0.1227** Δ**−0.0025** · tail Δ**−0.03** · SIGNAL n200 과적합 · `FEATURE_LAMBDA_WIRE=False` · `docs/benchmarks/20260804_KEVOLVE_FEAT_LAM_REVAL.json` |
| **K-EVOLVE-LOG-EXPAND** | **PASS** — evolve_log **1182**회(53~1234) · wf**982**+cache**200** · weight=0 · miss구간 cache미저장 · `docs/benchmarks/20260804_KEVOLVE_LOG_EXPAND.json` |
| **K-EVOLVE-FEAT-LAM-WIRE** | **ROLLED BACK** — 당시 n200 MATCH 0.145였으나 REVAL로 기각 · 모듈/`feat_lam` 코드는 잔존·OFF |
| **K-FUTURE-FULL-POST-EVOLVE** | **DONE** — FULL n=1182 ge3=**0.1184**(140) · vs구FULL **Δ=0** · thirds 0.099/0.132/0.1244 · mean feedback live · 구FULL JSON 유지 · `docs/benchmarks/20260804_KFUTURE_FULL_POST_EVOLVE.json` |
| **K-EVOLVE-SIGNAL** | **DONE** — `FEEDBACK_MATCH_MODE=mean` live(K-N차단) · λ전뇌 HOLD · review λ0.3 Δ+0.01 GO-WAIT · `docs/benchmarks/20260804_KEVOLVE_SIGNAL_survey.json` |
| **K-EVOLVE-LOG** | **PASS** — `testlotto_evolve_log` n=200 · weight=0 · API evolve/log·summary · ge3참고 stat0.165/markov0.130/review0.135 · `docs/benchmarks/20260804_KEVOLVE_LOG.json` |
| **K-MULTI-AI-PATCH** | **DOC** — 형·커서·젠스파크·벤치·FINDINGS 합의 · 최종 **K-EVOLVE-LOG→SIGNAL→AUTO** · `reports/20260804_MULTI_AI_PATCH_FINAL.md` |
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
| **K-PAST-LEARN-SCORE-RULE-DIAG** | 논문방법(적정채점규칙·PBO·보정χ²)으로 decay 재채점 · KEEP_BASE 지지 | **NO_SKILL_VS_NULL** |
| **K-YT-FILTER-BENCH** | YT다중필터+LSTM 비판 · DB1~1235 재실측 · annotate진단만 | **DOC_SURVEY** |
| **K-EVOLVE-AUTO-S3** | PREDICT+SCORE 통합 · 1236 캐시 워밍 | **PASS** |
| **K-EVOLVE-AUTO-S2** | SCORE-only apply · 1235 로그 기입 | **PASS** |
| **K-EVOLVE-AUTO-S1** | auto_state + tick dry-run · apply stub거부 | **PASS** |
| **K-EVOLVE-AUTO-DESIGN** | Phase3 AUTO 파이프·게이트·S0~S4실장 | **DOC→S4** |
| **K-PAIR-COVER** | 저출현쌍 as_of covering 모듈+ n200 survey | **HOLD** · ge3↓ |
| **K-STRUCTURE-COVER** | 구조질량 covering 모듈+ n200 survey · wire없음 | **HOLD** · ge3↓ |
| **K-MATH-PATTERN-WARRANT** | 1~1235 조합·실측 구조명분 10 · 예측아님 | **FOUND** |
| **20260805_SESSION** | 종료체크 · 날짜보고서 · EVOLVE arc 요약 | **DONE** |
| **K-EVOLVE-FEAT-LAM-REVAL** | full λ스윕 · review0.3 기각 · wire OFF | **HOLD** · 롤백 |
| **K-EVOLVE-LOG-EXPAND** | evolve_log 53~1234 · 순차WF+캐시백필 · weight0 | **PASS** · n=1182 |
| **K-EVOLVE-FEAT-LAM-WIRE** | review feature-bucket λ0.3 · schema3 · survey MATCH | **PASS** · ge3=0.145 |
| **K-FUTURE-FULL-POST-EVOLVE** | hybrid+mean 이후 FULL 리셋WF · 구FULL 대비 | **DONE** · ge3=0.1184 Δ=0 |
| **K-EVOLVE-SIGNAL** | mean피드백 wire · feature λ survey · review+0.01 | **DONE** · λ HOLD |
| **K-EVOLVE-LOG** | 회차×뇌 로그 테이블·백필·조회 API · 가중0 | **PASS** · n=200 |
| **K-MULTI-AI-PATCH** | 다중AI 패치논의 · 진화학습 최종안 · 형 A/B/C/D | **DOC** |
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

**K-PAST-LEARN-EV-RELABEL 결과 형 확인** — 적중축(SCORE-RULE NO_SKILL) · EV축(태그 무신호) 양쪽 다 닫힘. soft 태그 재정의 근거 없음.
다음 후보 = ① seed 민감도 full-range 재측정(잡음 하한 확정) ② 회차 1236+ 전향적 EV 로그(개입 없음) ③ `cycle_gap_boost` 단독 A/B.
**드리프트 정정(20260808):** transition STEP4 wire = **OFF**. `TRANSITION_V1_WIRE=False` (FUSION-N200 ROLLBACK 확정) — 이전 "STEP4 wire ON" 표기는 오기.  
압축 시: `GENSPARK_COMPRESS_RECOVER.md`+EXTERNAL_START · JSON raw 재페치.

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
