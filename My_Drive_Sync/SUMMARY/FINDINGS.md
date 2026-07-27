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
| K-06 | OPEN | per-draw fan-out 미구현 | `app/lotto/draw_scheduler.py` | 스케줄러→lotto4만. **K-AB:** hyodo 1회 정합했으나 영구 팬아웃은 STEP5 안만(코드0). 재발 방지=K-06 구현 |
| K-07 | PATCHED | fetch-latest 수동복구·갭해소 | `app/testlotto/routes.py`, `app/hyodo/routes.py` | testlotto=1234(선행) · **K-AB** lotto4→hyodo INSERT 1232–1234 · 3DB MAX=1234·mismatch0. 영구화는 K-06 |
| K-08 | OPEN | 평가지표 정의(best vs mean) | 메타·다양성 WF · `reports/20260726_ROK21_지표재정의_검증.md` | best-of-15는 초기하 천장≈2.27(MC 재현). 실력 판별은 **mean**. STATUS/벤치에 mean 병기 필수. best 단독 목표 금지 · **K-O와 병행 재정의 중** |
| K-09 | CLOSED | learn_state 컷오프 · 실질 누수 무해(당시 OFF 기본) | `learn_state_cutoff.py` · `reports/20260726_ROK21_K09컷오프_EV재검증.md` | 재구성(b). 200회 X−Y mean Δ CI에 0. **CLOSED**. **후속 K-S: 기본 ON·as_of 필수화로 선결 강화** |
| K-10 | OPEN | tier1 완화 헤드룸≈0 | `filters.py` · EV보정·최종 보고서 | T1~T3 p10 실현배율 vs T0 ≤1.002. **헤드룸0 기록·코드 완화 보류** |
| K-11 | OPEN | 적중축 폐기 · EV배선 유지(Y풀 재검증) | `ev_rerank.py` · K09컷오프 보고서 | 적중폐기 박제. Y(컷오프) 풀 순효과 1.033 CI[1.019,1.048] **YES→배선 유지**. K-09 전제 라벨 **제거**. 기본 OFF opt-in |
| K-12 | OPEN | RULES_FIXED 정합성 2건 (보고만) | `My_Drive_Sync/SUMMARY/RULES_FIXED.md` | (a) R33 복원 SSOT=kweon 기재 → ROK21 작업 오유도 → **RESTORE.md로 우회**. (b) R29 불일치 → **K-L로 승계**. **형만 수정 가능 · 동생/커서는 보고만** |
| K-A | OPEN | stat mean 0.760 < baseline 0.788/이론 0.80 | `brains/predict_stat_fairy.py:12` · `predict_statistical.py` | 최근100회(1135-1234)·500세트. **단 K-B 해소 전 패치 금지** · K-O 이후 mean 서열 해석 재검토 |
| K-B | OPEN | 성능 표본 2종 충돌 | `testlotto_brain_review` vs `lotto_predictions` | review100: stat0.760/markov0.802 ↔ pred69: stat0.835/markov0.710 **역전**. **BENCH_PROTOCOL로 SSOT 고정** |
| K-C | OPEN | referee 가중이 성적 역행 | `learn_state.py:108` `get_referee_weights` | 최저성적 stat이 최고가중 0.3348. 식 `(1+avg×0.15)/Σ` 의 avg 출처 검증 필요 · **K-M과 연계** |
| K-D | OPEN | 클릭 경로에 fusion 부재 | `fusion.py` 미호출 · `coordinator._apply_aux_scoring:47` | 실제 융합=AUX 하드코딩 [0.25]×4. 문서/기대 흐름 불일치 |
| K-E | OPEN | seed 미고정 → 비재현 | `predict_statistical.py:234` · `predict_markov.py:57,59,150,156` · `predict_review_king.py:42` | 동일입력 2회 stat/markov/review 모두 False. **동결항목 — 형 승인 전 수정금지** · K-S 재현성 설계와 연계 |
| K-F | OPEN | markov가 learn_state 미소비 | `brains/predict_flow_shaman.py:9` | boost 미적용. 3뇌 중 유일 |
| K-G | OPEN | ending boost 휴면 | `learn_state.py:134-150` | `ending_digit_boost=0.0` · miss ending=0. 경로는 살아있으나 무효 |
| K-H | OPEN | 미등록 AUX 파일 잔존 | `brains/aux_gap_scout.py` · `aux_structure_guard.py` | coordinator 미등록. 죽은 코드 |
| K-I | OPEN | per-brain fallback 없음 | `brains/coordinator.py:94-102` | 단일 뇌 예외 → 전체 실패. try 미보호 |
| K-J | OPEN | 가중치 이중 체계 | `testlotto_brain_weights.current_weight` vs live referee | DB 1.1687 ↔ live 0.3348. 어느 것이 진짜인지 불명 |
| K-K | OPEN | 클릭 예측이 feedback 미연결 | `learn_state.apply_feedback` | 백테/복습 경로에서만 호출. 단발 클릭은 학습 안 됨 |
| K-L | OPEN | R29 ↔ 실제 뇌 구성 전면 불일치 | `RULES_FIXED.md` R29 | 9뇌 중 실재 0개. 실제=3예측+4보조. **형만 수정 가능** |
| K-M | HOLD | referee 가중 실효격차 0.33% (사실상 균등) | `learn_state.py:108` `get_referee_weights` | **원인확정**: w≈균등 · top5 멤버십차 5%. 학습→가중 전달 사실상 0. 조치 설계 대기 |
| K-N | HOLD | 학습지표 best → 고분산 뇌를 실력으로 오인 | `walkforward.py:91,110` `apply_feedback(best)` | **원인확정**: null상 best 전원 비실력. 조치(학습입력을 mean/볼지표로) 대기 |
| K-O | OPEN | 세트 mean=0.8 상수 → 서열화 불가 | 초기하 E[X]=6×6/45 | 배경확정. 벤치에서 mean 단독 서열 금지 |
| K-P | OPEN | 세트 5적중 기대≈3.5/대규모백테 → 학습신호 부재 | P₅≈2.87e-5 | 상위등수 최적화 축 폐기 후보 |
| K-Q | OPEN | 볼빈도 균등부합 · 검출한계 ±~30% | `lotto_draws` 1–1234 | χ² p≈0.97 · FDR 0건 · 시간분할 공통상위 없음 |
| K-R | OPEN | 볼세트/추첨기 식별자 결측 · 층화 대기 | DB 전테이블 | 스키마 설계만. 수집금지. 층화 n≈249 시 검출폭 ±66% |
| K-S | PATCHED | 미래참조 누수 선결 해소 · WF전체는 미구현 | `feedback.py` · `learn_state*.py` · coordinator/walkforward · `reports/20260727_KT_KV_전제검정_포트폴리오감사.md` | as_of 필수·CUTOFF **기본 ON**·격리 2회동일 증명. 번호산출·random.choices 미수정. WF뼈대 잔여=형승인 |
| K-T | OPEN | 뇌 전제 검정: 의존/기하이탈 기각 · 형태·균형은 이론부합(제약명분) · referee 미정의 | `docs/benchmarks/20260727_KT_KV_results.json` · KT_KV 보고서 | markov lag1 χ² p=0.764 · miss χ² p=0.483 · pattern/balance 전부 p≥0.13 |
| K-U | OPEN | 쌍층 표본: 분산=null · FDR0 · Bonf 검출폭 ±~79%RR | 동상 | 25914 슬롯 · E=26.18 · perm(C45,7)×10k p≈0.48 · 삼중 생략 |
| K-V | PATCHED | 발권 dedup: E[k] 97.091→100.000 · unresolved0 · OFF/ON 이표본 왜곡없음 | `ticket_dedup.py` · coordinator 후처리 · `reports/20260727_KV_중복제거_구현검증.md` | `ROK21_DEDUP` 기본 ON. P배수≈1.030. 예측력↑ 아님. 절대이론 GOF는 뇌가중 산출물에서 OFF/ON 공통 기각 → 왜곡게이트=이표본 |
| K-W | OPEN | 산출 정합성: 명분(당첨≈이론) vs 뇌 산출 거리 측정 · 명분 라벨 SSOT | `docs/benchmarks/20260727_KW_alignment.json` · `WARRANT.md` · KW 보고서 | stat→A근접 · markov/review→C근접 · review끝수 편향경보. 라벨=기각5/실증2/미정의1. 기각뇌 제거금지 |
| K-X | OPEN | review 끝수편향 원인=`repeat_rate` 투영(5·8↑/7↓) · 예측폐루프·자기강화증폭 미입증 | `predict_review_king.py` · `repeat_rate_after_draw` · `docs/benchmarks/20260727_KX_review_ending.json` · KX 보고서 | early↔late KS p=0.66. ending_digit_boost는 review 미사용. 교정 구현 금지(형승인). P(1등) 관점 교정 불필요 가능 |
| K-Y | OPEN | 보조4 감사: pattern/balance→전제실증·구현미검증 강등 · miss/referee 순위기여0 · pair/consec/odd_even 미소비 | `docs/benchmarks/20260727_KY_aux_audit.json` · KY 보고서 · WARRANT | fusion 미배선 재확인(K-D). live≠DB referee(K-J). balance 기본합150≠138. 코드0 |
| K-Z | PATCHED | C(45,6) 이론값 확정 후 K-AA에서 코드 적용(AC=8·폴백합138·consec PMF) | `docs/benchmarks/20260727_KZ_theory_constants.json` · KZ/KAA 보고서 | A거리 미개선→K-AA에서 게이트↓관측 |
| K-AA | PATCHED | 이론값 적용·구현검증·명분복귀: pattern/balance→실증 · warrant.py동기화 · E[k]=100·SHA일치 | `docs/benchmarks/20260727_KAA_apply_verify.json` · diff · KAA 보고서 | 판정축=조합론 참값. A거리 관측만. 1등확률↑아님. pair/30·zone목표 미변경 |
| K-AB | PATCHED | 회차갭정합: hyodo 1232–1234를 lotto4에서 INSERT · 3DB MAX=1234·번호불일치0 · 회귀PASS | `docs/benchmarks/20260727_KAB_draw_gap.json` · backup_hashes · KAB 보고서 | 크롤링0·UPDATE0. K-06 영구팬아웃은 안만. 예측력무관·무결성 |
| K-AC | OPEN | 압축대비 룰: Q1~Q8답 · RESTORE드리프트보정 · drift n=0 · RULES/CURSOR 초안은 형승인대기 | KAC 보고서 · `tools/_doc_drift_check.py` · drafts/ | R28 미준수 자인. R33/R29 충돌 기록. 예측력무관·방향상실방지 |
| K-AD | PATCHED | 압축즉시복귀: guard_boot 동적주입(HEAD·BOOT§1·NEXT1건) · NEXT_ACTIONS앵커 · RESTORE복귀5줄 동기 · drift0·회귀PASS | KAD 보고서 · `rok21_inject.py` · `20260727_KAD_hook_inject.json` | R28→1줄[복귀]. 젠스파크는 hooks없음→RESTORE큐. 예측력무관·운영인프라 |
