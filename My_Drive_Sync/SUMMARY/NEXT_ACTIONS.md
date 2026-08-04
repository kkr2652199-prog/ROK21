# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-COVER-DIAG-DONE
- 할일: covering 진단 완료 · 결과 확인 · **각도3(early 취약성) 진행**
- 완료조건: 형 GO
- 선행완료: docs/benchmarks/20260805_KCOVER_DIAG.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-05

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- overlap Jaccard0.108 NORMAL · unique20.7 < 기대26.5
- cold-free replace Δge3=+0.03 IMPROVE (n_replaced=160) · wire는 별도 GO
