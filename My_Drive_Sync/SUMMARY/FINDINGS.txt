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
