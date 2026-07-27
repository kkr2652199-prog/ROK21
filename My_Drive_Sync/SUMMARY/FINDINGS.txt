# FINDINGS — ROK21 결함 대장 (ID 영구 고정 · kweon 복사본)

> memoy는 F-*, ROK21/kweon계는 **K-*** 로 구분. ID 재사용·재번호 금지.
> 상태: OPEN -> VERIFYING -> PATCHED -> CLOSED

| ID | 상태 | 요약 | 위치 | 비고 |
|----|------|------|------|------|
| K-00 | OPEN | 4군 정밀분석 미착수 | `app/lotto4/` | 분석 후 K-A~ 채움 |
| K-01 | CLOSED | STATUS_LATEST 최신화 지연 | `My_Drive_Sync/SUMMARY/STATUS_LATEST.md` | 20260726 갱신 (07-25 재기록+07-26 인프라/UI 반영) |
| K-02 | OPEN | STATUS/RESUME .md·.txt 이중 사본 | `My_Drive_Sync/SUMMARY/` | 갱신 시 양쪽 동기화 유지 |
| K-03 | CLOSED | app/lotto·lotto2 = 1~2군 레거시 잔존 | `app/lotto/`, `app/lotto2/` | main_v13 router 미등록 · init/scheduler만 공유 (STEP0 20260726) |
| K-04 | CLOSED | .gitignore 신설 | 루트 `.gitignore` | 커밋 `0a1a55c` (20260726) |
| K-05 | OPEN | public 레포·tracked *.db ~306MB | `data/*.db`, `data/combos/` | 24 files · 320,983,040 byte (20260726 실측) · 형 승인 전 untrack 금지 |
| K-06 | OPEN | per-draw fan-out 미구현 | `app/lotto/draw_scheduler.py` | 스케줄러→`collect_latest_forward` lotto4.db만 · testlotto/hyodo 미연동 · draws gap **hyodo=1231** (testlotto/lotto4=1234, 20260727 실측) |
| K-07 | OPEN | fetch-latest 수동복구·팬아웃 | `app/testlotto/routes.py`, `app/hyodo/routes.py` | **20260727:** testlotto 백업+fetch검증 완료(MAX=1234·1232~1234 공식MATCH·pred/review 있음). **잔여=hyodo만 1231**. hyodo 동기화는 형 승인 후 |
| K-08 | OPEN | 평가지표 정의(best vs mean) | 메타·다양성 WF · `reports/20260726_ROK21_지표재정의_검증.md` | best-of-15는 초기하 천장≈2.27(MC 재현). 실력 판별은 **mean**. STATUS/벤치에 mean 병기 필수. best 단독 목표 금지 |
| K-09 | CLOSED | learn_state 컷오프 · 실질 누수 무해 | `learn_state_cutoff.py` · `reports/20260726_ROK21_K09컷오프_EV재검증.md` | 재구성(b) 플래그 `ROK21_LEARN_CUTOFF=1`. 200회 X−Y mean Δ CI에 0. **CLOSED**. 전제 라벨 제거. 스키마 변경 없음 |
| K-10 | OPEN | tier1 완화 헤드룸≈0 | `filters.py` · EV보정·최종 보고서 | T1~T3 p10 실현배율 vs T0 ≤1.002. **헤드룸0 기록·코드 완화 보류** |
| K-11 | OPEN | 적중축 폐기 · EV배선 유지(Y풀 재검증) | `ev_rerank.py` · K09컷오프 보고서 | 적중폐기 박제. Y(컷오프) 풀 순효과 1.033 CI[1.019,1.048] **YES→배선 유지**. K-09 전제 라벨 **제거**. 기본 OFF opt-in |
| K-12 | OPEN | RULES_FIXED 정합성 2건 (보고만) | `My_Drive_Sync/SUMMARY/RULES_FIXED.md` | (a) R33 복원 SSOT=kweon 기재 → ROK21 작업 오유도 → **RESTORE.md로 우회**. (b) R29 불일치 → **K-L로 승계**. **형만 수정 가능 · 동생/커서는 보고만** |
| K-A | OPEN | stat mean 0.760 < baseline 0.788/이론 0.80 | `brains/predict_stat_fairy.py:12` · `predict_statistical.py` | 최근100회(1135-1234)·500세트. **단 K-B 해소 전 패치 금지** |
| K-B | OPEN | 성능 표본 2종 충돌 | `testlotto_brain_review` vs `lotto_predictions` | review100: stat0.760/markov0.802 ↔ pred69: stat0.835/markov0.710 **역전**. 원인규명 최우선 |
| K-C | OPEN | referee 가중이 성적 역행 | `learn_state.py:108` `get_referee_weights` | 최저성적 stat이 최고가중 0.3348. 식 `(1+avg×0.15)/Σ` 의 avg 출처 검증 필요 |
| K-D | OPEN | 클릭 경로에 fusion 부재 | `fusion.py` 미호출 · `coordinator._apply_aux_scoring:47` | 실제 융합=AUX 하드코딩 [0.25]×4. 문서/기대 흐름 불일치 |
| K-E | OPEN | seed 미고정 → 비재현 | `predict_statistical.py:234` · `predict_markov.py:57,59,150,156` · `predict_review_king.py:42` | 동일입력 2회 stat/markov/review 모두 False. **동결항목 — 형 승인 전 수정금지** |
| K-F | OPEN | markov가 learn_state 미소비 | `brains/predict_flow_shaman.py:9` | boost 미적용. 3뇌 중 유일 |
| K-G | OPEN | ending boost 휴면 | `learn_state.py:134-150` | `ending_digit_boost=0.0` · miss ending=0. 경로는 살아있으나 무효 |
| K-H | OPEN | 미등록 AUX 파일 잔존 | `brains/aux_gap_scout.py` · `aux_structure_guard.py` | coordinator 미등록. 죽은 코드 |
| K-I | OPEN | per-brain fallback 없음 | `brains/coordinator.py:94-102` | 단일 뇌 예외 → 전체 실패. try 미보호 |
| K-J | OPEN | 가중치 이중 체계 | `testlotto_brain_weights.current_weight` vs live referee | DB 1.1687 ↔ live 0.3348. 어느 것이 진짜인지 불명 |
| K-K | OPEN | 클릭 예측이 feedback 미연결 | `learn_state.apply_feedback` | 백테/복습 경로에서만 호출. 단발 클릭은 학습 안 됨 |
| K-L | OPEN | R29 ↔ 실제 뇌 구성 전면 불일치 | `RULES_FIXED.md` R29 | 9뇌 중 실재 0개. 실제=3예측+4보조. **형만 수정 가능** |
