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
| K-06 | OPEN | per-draw fan-out 미구현 | `app/lotto/draw_scheduler.py` | 스케줄러→`collect_latest_forward` lotto4.db만 · testlotto/hyodo 미연동 · draws gap lotto4=1234 vs testlotto/hyodo=1231 |
| K-07 | OPEN | fetch-latest 수동복구·팬아웃 | `app/testlotto/routes.py`, `app/hyodo/routes.py` | **20260726 재실측:** testlotto/lotto4 MAX=1234 · **hyodo만 1231**. 옛 “testlotto=1231” 서술은 폐기. hyodo 1232~1234 동기화는 형 승인 후 |
| K-08 | OPEN | 평가지표 정의(best vs mean) | 메타·다양성 WF · `reports/20260726_ROK21_지표재정의_검증.md` | best-of-15는 초기하 천장≈2.27(MC 재현). 실력 판별은 **mean**. STATUS/벤치에 mean 병기 필수. best 단독 목표 금지 |
| K-09 | OPEN | learn_state 전역 시계열 누수 위험 | `app/testlotto/learn_state.py` · review/stat 경로 | draws는 `_get_draws_before`로 정상. `load_learn_state`는 cutoff 없음 → 과거 회차 재생성 시 미래 피드백 오염 가능. 저장세트 review mean>0.80 **미입증**. `reports/20260726_ROK21_뇌감사_비인기검증.md` |
| K-10 | OPEN | tier1 완화 헤드룸≈0 | `filters.py` · EV보정·최종 보고서 | T1~T3 p10 실현배율 vs T0 ≤1.002. **헤드룸0 기록·코드 완화 보류** |
| K-11 | OPEN | 적중축 폐기 · D배선(기본OFF) · 창200 생존 | `ev_rerank.py` · `reports/20260726_ROK21_D배선_사전등록검증.md` | 적중폐기 유지. D=EV0.5+커버0.5 · `ROK21_EV_RERANK=1`만 활성. 창200 순효과 1.032 CI[1.020,1.044] **YES**. OFF해시 동일. `K-09 전제` |
| K-12 | OPEN | RULES_FIXED 정합성 2건 (보고만) | `My_Drive_Sync/SUMMARY/RULES_FIXED.md` | (a) R33 복원 SSOT=kweon 기재 → ROK21 작업 오유도 → **RESTORE.md로 우회**. (b) R29 "7활성+2Hidden=9뇌" ≠ 테스트로또 실측 3예측+4보조. **형만 수정 가능 · 동생/커서는 보고만** |
