# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-PIN-GAP-DIAG-WAIT
- 할일: 지시서 수정3건 반영 후 **K-PIN-GAP-DIAG GO** · 또는 로드맵 A/B/C/D **형 선택**
- 완료조건: 형 GO(수정지시서) 또는 A/B/C/D 명시
- 선행완료: reports/20260804_GENSPARK_COMPRESS_RESUME.md · K-PIN-GAP-DIAG-REVIEW DOC · 로드맵 I1+I3 권고

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **수정3건(GO 전 필수):** (1) FULL thirds n=394 — 「mid붕괴·25/25/50」금지 (2) READ-ONLY=JSON1차 / WF reset은 별도GO (3) 종료5종+R37 sync (SSOT4종만 부족)
- **FULL 실측:** early ge3=0.099 · mid=0.132 · late=0.124 (mid 최악 아님)
- **K-IMPROVE-ROADMAP** — I1 pin갭진단 + I3 B1 권고 · ultra wire HOLD
- **K-UI-BT-PRELOAD** — draw-index actuals 200 · pool-index 13 · per-draw fetch 제거
- **K-FUSION-INNOVATION** — ge3=0.09 tie · rolled back · V2 live
