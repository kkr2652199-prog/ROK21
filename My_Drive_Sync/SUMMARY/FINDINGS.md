# FINDINGS — ROK21 결함 대장 (ID 영구 고정 · kweon 복사본)

> memoy는 F-*, ROK21/kweon계는 **K-*** 로 구분. ID 재사용·재번호 금지.
> 상태: OPEN -> VERIFYING -> PATCHED -> CLOSED · **HOLD**(원인확정·조치 대기)

## 관점 전환 (20260727 · 전제 실증)

확률이 조합불변이므로 ‘선택’ 비용 0 → 확률 외 목적함수 최적화는 자유롭다.  
평가 질문: (구) 어느 뇌가 잘 맞히는가 → (신) 어느 뇌의 **전제**가 실재하는가.  
**뇌 정당성 = 적중률이 아니라 전제의 실증 여부** (`BENCH_PROTOCOL` §정당성).

## 배경 확정 (20260727 · 볼단위 전환)

1. **(K-O)** E[적중]=6×(6/45)=**0.8** 상수 → 세트 mean만으로 뇌 서열화 **불가**.
2. **(K-P)** 전이력×100세트 백테의 5개일치 기대 ≈ **3.5건**(실측식 1245×100×P₅≈3.58) → 세트단위 상위등수 지표는 **학습신호 부재**.
3. 따라서 검정 층위를 **세트 → 볼(번호)** 로 하향. 볼 표본 실측 n_draws=1234 → 본+보너스 슬롯 **8638**.

성적 비교는 `BENCH_PROTOCOL.md` 준수. 원본 kweon(`264de3c`) 동결.

| ID | 상태 | 요약 | 위치 | 비고 |
|----|------|------|------|------|
| K-00 | OPEN | 4군 정밀분석 미착수 | `app/lotto4/` | 분석 후 K-A~ 채움 |
| K-01 | CLOSED | STATUS_LATEST 최신화 지연 | `My_Drive_Sync/SUMMARY/STATUS_LATEST.md` | 20260726 갱신 (07-25 재기록+07-26 인프라/UI 반영) |
| K-02 | OPEN | STATUS/RESUME .md·.txt 이중 사본 | `My_Drive_Sync/SUMMARY/` | 갱신 시 양쪽 동기화 유지 |
| K-03 | CLOSED | app/lotto·lotto2 = 1~2군 레거시 잔존 | `app/lotto/`, `app/lotto2/` | main_v13 router 미등록 · init/scheduler만 공유 (STEP0 20260726) |
| K-04 | CLOSED | .gitignore 신설 | 루트 `.gitignore` | 커밋 `0a1a55c` (20260726) |
| K-05 | OPEN | public 레포·tracked *.db ~306MB | `data/*.db`, `data/combos/` | 24 files · 320,983,040 byte (20260726 실측) · 형 승인 전 untrack 금지 |
| K-06 | PATCHED | per-draw fan-out 영구화 | `app/lotto/draw_fanout.py` · `collect_latest_forward` | K-AE+**K-AF**: 수집0건에도 catch-up · MAX/COUNT조기게이트. **잔여위험: 순차commit 시 선행DB만 커밋될 수 있음→다음 catch-up 수렴(완전원자 불가)** |
| K-07 | PATCHED | fetch-latest 수동복구·갭해소 | `app/testlotto/routes.py`, `app/hyodo/routes.py` | testlotto=1234(선행) · **K-AB** lotto4→hyodo INSERT 1232–1234 · 3DB MAX=1234·mismatch0. 영구화는 K-06 |
| K-08 | OPEN | 평가지표 정의(best vs mean) | 메타·다양성 WF · `reports/20260726_ROK21_지표재정의_검증.md` | best-of-15는 초기하 천장≈2.27(MC 재현). 실력 판별은 **mean**. STATUS/벤치에 mean 병기 필수. best 단독 목표 금지 · **K-O와 병행 재정의 중** |
| K-09 | CLOSED | learn_state 컷오프 · 실질 누수 무해(당시 OFF 기본) | `learn_state_cutoff.py` · `reports/20260726_ROK21_K09컷오프_EV재검증.md` | 재구성(b). 200회 X−Y mean Δ CI에 0. **CLOSED**. **후속 K-S: 기본 ON·as_of 필수화로 선결 강화** |
| K-10 | OPEN | tier1 완화 헤드룸≈0 | `filters.py` · EV보정·최종 보고서 | T1~T3 p10 실현배율 vs T0 ≤1.002. **헤드룸0 기록·코드 완화 보류** |
| K-11 | OPEN | 적중축 폐기 · EV배선 유지(Y풀 재검증) | `ev_rerank.py` · K09컷오프 보고서 | 적중폐기 박제. Y(컷오프) 풀 순효과 1.033 CI[1.019,1.048] **YES→배선 유지**. K-09 전제 라벨 **제거**. 기본 OFF opt-in |
| K-12 | OPEN | RULES_FIXED 정합성 2건 (보고만) | `My_Drive_Sync/SUMMARY/RULES_FIXED.md` | (a) R33 복원 SSOT=kweon 기재 → ROK21 작업 오유도 → **RESTORE.md로 우회**. (b) R29 불일치 → **K-L로 승계**. **형만 수정 가능 · 동생/커서는 보고만** |
| K-A | OPEN | stat mean 0.760 < baseline 0.788/이론 0.80 | `brains/predict_stat_fairy.py:12` · `predict_statistical.py` | 최근100회(1135-1234)·500세트. **단 K-B 해소 전 패치 금지** · K-O 이후 mean 서열 해석 재검토 |
| K-B | PATCHED | 성능 표본 2종 충돌 → **BENCH SSOT 고정·기계검증** | `BENCH_PROTOCOL.md` · `20260727_KB_bench_ssot.json` | review100완결 · pred갭1149–1179=31 · 세트동일0. 실력=review JSON mean · pred는 UI전용. mean단독서열 금지 |
| K-C | OPEN | referee 가중이 성적 역행 | `learn_state.py:108` `get_referee_weights` | 최저성적 stat이 최고가중 0.3348. 식 `(1+avg×0.15)/Σ` 의 avg 출처 검증 필요 · **K-M과 연계** |
| K-D | PATCHED | 클릭 경로 fusion 부재 → **의도 문서화·미호출 import 제거** | `engine.py` · `fusion.py` · `coordinator.py` · `20260728_KD_fusion_path.json` | run_prediction→coordinator only · AUX 0.25×4 · fusion 재배선금지 · 3+4유지 |
| K-E | OPEN | seed 미고정 → 비재현 | `predict_statistical.py:234` · `predict_markov.py:57,59,150,156` · `predict_review_king.py:42` | 동일입력 2회 stat/markov/review 모두 False. **동결항목 — 형 승인 전 수정금지** · K-S 재현성 설계와 연계 |
| K-F | PATCHED | markov learn 재정의(재료+효과) · live=`markov_brain` 이미 소비 · predict_flow_shaman DEPRECATED | `markov_brain/learn.py` · `20260811_KF_재정의_판정` | 재료채움후 효과미달 → 배선사실 PATCHED·효과없음 CLOSE기록 · LEARN_WIRED=True유지(경로정상) |
| K-G | PATCHED | ending boost 휴면 → 재누적 후 **ACTIVE** | `learn_state.apply_feedback` · coordinator `_detect_missed_patterns` · `20260812_KG_ENDING_BOOST_AUDIT` | 리셋후 0/0은 재료부재. refill후 전뇌 boost**0.3**(cap)·miss10~15. 상한변경 금지 · 효과튜닝=별도지시 |
| K-H | PATCHED | 미등록 AUX 잔존 → **`brains/_unused/` 격리** | `aux_gap_scout.py` · `aux_structure_guard.py` · `20260728_KH_unused_aux.json` | live import0 · 3+4 유지 · 재배선 금지기본 · 예측력무관 |
| K-I | PATCHED | per-brain fallback 없음 → 뇌별 try 보호 | `coordinator.run_coordinated_prediction` · `signal_pool.expand_pool` · `20260812_KI_BRAIN_FALLBACK_WIRE` | mock markov boom → pool stat/review10 · 발권 생존·`brain_errors` · 20260812 |
| K-J | PATCHED | 가중치 이중 체계 → SSOT=live referee · DB=미러 | `get_referee_weights` · `apply_feedback` 미러동기 · detail_service | 발권/UI=`get_referee_weights` · DB `current_weight`는 미러(구식1+avg*0.1제거) · 20260811_KSEQ · init시드1/3+sync |
| K-REFEREE-BY-BRAIN | PATCHED | 감독관 단일교차의존 → 뇌별 독립 엔진 | `referee_by_brain.py` · `*_brain/referee.py` · aux_referee | set_score=해당뇌 learn만 · quota만 상대정규화 · 20260811 |
| K-POOL-JACCARD-BY-BRAIN | HOLD | pool diversify Jaccard 뇌별 스윕 | `diversity.JACCARD_PENALTY_BY_BRAIN` · `20260811_KPOOL_JACCARD_*` | 전뇌 0.85 유지 · |Δ|≪0.005 |
| K-POOL-OVERSAMPLE-BY-BRAIN | PATCHED | pool 후보배수 뇌별 스윕 | `diversity.OVERSAMPLE_MULT_BY_BRAIN` · predict factor(brain=) | markov**5** APPLY · prefer+0.0079 · stat/review3 |
| K-K | PATCHED | 클릭 예측이 feedback 미연결 → routes 연결 | `click_feedback.py` · `routes.py` | POST /predict·/fetch-latest → apply_draw_result_feedback · evolve_log note=`K-KK-FEEDBACK` · weight_applied=0.0 유지 · K-M HOLD · K-N PATCHED |
| K-L | OPEN | R29 ↔ 실제 뇌 구성 전면 불일치 | `RULES_FIXED.md` R29 | 9뇌 중 실재 0개. 실제=3예측+4보조. **형만 수정 가능** |
| K-M | PATCHED | referee 가중 실효격차 0.33% (사실상 균등) | `learn_state.get_referee_weights` · GAIN=2.5·baseline=0.8 | 구식1+avg×0.15→baseline대비편차×GAIN · 100회 샘플복습 후 격차 확대 · K-N mean입력 선행 |
| K-N | PATCHED | 학습지표 best → 고분산 뇌를 실력으로 오인 | `walkforward._learn_match_from_sets` · `FEEDBACK_MATCH_MODE=mean` | WF/클릭/coordinator 학습입력 **mean** · best는 표시·참고만 · K-M HOLD |
| K-O | OPEN | 세트 mean=0.8 상수 → 서열화 불가 | 초기하 E[X]=6×6/45 | 배경확정. 벤치에서 mean 단독 서열 금지 |
| K-P | OPEN | 세트 5적중 기대≈3.5/대규모백테 → 학습신호 부재 | P₅≈2.87e-5 | 상위등수 최적화 축 폐기 후보 |
| K-Q | OPEN | 볼빈도 균등부합 · 검출한계 ±~30% | `lotto_draws` 1–1234 | χ² p≈0.97 · FDR 0건 · 시간분할 공통상위 없음 |
| K-R | OPEN | 볼세트/추첨기 식별자 결측 · 층화 대기 | DB 전테이블 | 스키마 설계만. 수집금지. 층화 n≈249 시 검출폭 ±66% |
| K-S | PATCHED | 미래참조 누수 선결 해소 · WF전체는 미구현 | `feedback.py` · `learn_state*.py` · coordinator/walkforward · `reports/20260727_KT_KV_전제검정_포트폴리오감사.md` | as_of 필수·CUTOFF **기본 ON**·격리 2회동일 증명. 번호산출·random.choices 미수정. WF뼈대 잔여=형승인 |
| K-T | OPEN | 뇌 전제 검정: 의존/기하이탈 기각 · 형태·균형은 이론부합(제약명분) · referee 미정의 | `docs/benchmarks/20260727_KT_KV_results.json` · KT_KV 보고서 | markov lag1 χ² p=0.764 · miss χ² p=0.483 · pattern/balance 전부 p≥0.13 |
| K-U | OPEN | 쌍층 표본: 분산=null · FDR0 · Bonf 검출폭 ±~79%RR | 동상 | 25914 슬롯 · E=26.18 · perm(C45,7)×10k p≈0.48 · 삼중 생략 |
| K-V | PATCHED | 발권 dedup: E[k] 97.091→100.000 · unresolved0 · OFF/ON 이표본 왜곡없음 | `ticket_dedup.py` · coordinator 후처리 · `reports/20260727_KV_중복제거_구현검증.md` | `ROK21_DEDUP` 기본 ON. P배수≈1.030. 예측력↑ 아님. 절대이론 GOF는 뇌가중 산출물에서 OFF/ON 공통 기각 → 왜곡게이트=이표본 |
| K-W | PATCHED | 산출 정합성 측정+**post-KP3 재측정** · 명분 라벨 SSOT | `20260727_KW_alignment.json` · `20260727_KW_post_KP3.json` · WARRANT | 초기: review ending χ²/df vsA **13.37**→live **2.82** · vsC **8.54**→**2.32**. NameError(`rates`) 회귀수정. 기각명분 유지·제거금지 |
| K-X | PATCHED | review 끝수편향: K-X 원인규명(rate투영) + **K-P3** ending질량균등화 | `predict_review_king.py` · `20260727_KP3_review_ending.json` | l1_ball 0.299→0.098 · verify_pass · random.choices 동결 · 기각명분 유지 |
| K-Y | OPEN | 보조4 감사(이력): miss/referee 순위기여0 · fusion미배선(K-D) · live≠DB referee(K-J) | `docs/benchmarks/20260727_KY_aux_audit.json` · KY 보고서 | **후속:** K-AA pattern/balance→실증 · K-AG pair÷32·LMH·3키배선. 감사 시점(미소비)은 K-AG로 해소됨 |
| K-Z | PATCHED | C(45,6) 이론값 확정 후 K-AA에서 코드 적용(AC=8·폴백합138·consec PMF) | `docs/benchmarks/20260727_KZ_theory_constants.json` · KZ/KAA 보고서 | A거리 미개선→K-AA에서 게이트↓관측 |
| K-AA | PATCHED | 이론값 적용·구현검증·명분복귀: pattern/balance→실증 · warrant.py동기화 · E[k]=100·SHA일치 | `docs/benchmarks/20260727_KAA_apply_verify.json` · diff · KAA 보고서 | 판정축=조합론 참값. A거리 관측만. 1등확률↑아님. pair/30·zone목표 미변경 |
| K-AB | PATCHED | 회차갭정합: hyodo 1232–1234를 lotto4에서 INSERT · 3DB MAX=1234·번호불일치0 · 회귀PASS | `docs/benchmarks/20260727_KAB_draw_gap.json` · backup_hashes · KAB 보고서 | 크롤링0·UPDATE0. K-06 영구팬아웃은 안만. 예측력무관·무결성 |
| K-AC | PATCHED | 압축대비 룰: Q1~Q8답 · RESTORE드리프트보정 · R35/R36/R37·§6 반영(K-AE) · drift0 | KAC 보고서 · `tools/_doc_drift_check.py` · drafts/이력 | R28→1줄복귀·EXTERNAL_START. 예측력무관·방향상실방지 |
| K-AD | PATCHED | 압축즉시복귀: guard_boot 동적주입(HEAD·BOOT§1·NEXT1건) · NEXT_ACTIONS앵커 · RESTORE복귀5줄 동기 · drift0·회귀PASS | KAD 보고서 · `rok21_inject.py` · `20260727_KAD_hook_inject.json` | R28→1줄[복귀]. 젠스파크는 hooks없음→RESTORE큐. 예측력무관·운영인프라 |
| K-AE | PATCHED | 룰 R35/R36·CURSOR §6 반영 + K-06 영구팬아웃 구현·샌드박스검증 | KAE 보고서 · fanout_verify.json · draw_fanout.py | 수집무결성. lotto4 실패롤백없음(K-AB). drafts 이력유지 |
| K-AF | PATCHED | 팬아웃 잔여정합: 순차commit위험명시·catch-up무조건·조기게이트·T1~T7 PASS · R37 FLOW_BRIEF | KAF 보고서 · `20260727_KAF_fanout_followup.json` | 예측력무관·무결성. 실전발화0회(logs없음) |
| K-AG | PATCHED | pair÷null_q95(32)·zone=LMH이론PMF · 미소비3키(pair/consec/odd) aux배선 · E[k]=100 | KAG 보고서 · `20260727_KAG_pair_zone_learnkeys.json` | 명분·배선정합. 1등↑아님. 구/30·spread대비 SHA변경은 재정의정상 |
| K-MONEY1-LESSONS | OPEN | 1군→ROK21 교훈: **배울점** draws컷오ff·생성/채점분리·stat/markov≈0.8 · **갖춘점** WIRE-V2·BENCH·as_of·fusion미배선 · **금지** fusion전역가중·feedback무관·캐시·hyena2차·lstm stored | `reports/20260729_MONEY1GUN_ROK21_LESSONS.md` · 1군 `lotto.db` ro | 1131~1231 3등15(0/0/15) · 전체10/3/171 · stat/markov 0건. 예측코드 미수정 |
| K-BENCH-DEEP | OPEN | 1군 심화→ROK21 적용 아이디어 **K-BENCH-01~05** · **01 SIGNAL_FOUND·05·03 PATCHED** · 02 FAIL | `reports/20260729_BENCH_DEEP_IDEAS.md` · `20260729_KBENCH_POSTMORTEM.json` | 쿼터갭43.6%·markov52.5% · AUX무상관 · coordinator 동결 |
| K-BENCH-01 | CLOSED | postmortem WF n=1182 · SIGNAL_FOUND · WIRE 후속 완료 | `20260729_KBENCH_POSTMORTEM.json` | 진단 survey · WIRE=별도 |
| K-BENCH-01-WIRE | CLOSED | tier 피드백 배선 live WF ge3=**0.1142** p=0.49 · pin 0.1447 미달 → **롤백** | `20260729_KBENCH01_WIRE_verify.json` | learn_state tier 원복 · coordinator 미수정 |
| K-AUX-SIGNAL | OPEN | 4보조 채점→**신호전달** 역할 전환 · E1 survey **FAIL** · E2/E3 후보 | `20260729_KAUX_SIGNAL_survey.json` | best miss_pattern@α=0.2 ge3=0.1303 p=0.042 · pin 0.1447 미달 · WIRE 보류 |
| K-AUX-SIGNAL-01 | CLOSED | E1 live WF n=1182 · 5 variants×α grid · hint inject wrapper | `20260729_KAUX_SIGNAL_survey.json` | FAIL · coordinator 미수정 · → K-ATTACK-HOLD or E2/E3 |
