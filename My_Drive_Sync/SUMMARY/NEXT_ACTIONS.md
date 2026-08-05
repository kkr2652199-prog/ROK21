# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-NEIGHBOR-MATCH-DONE
- 할일: kNN 패턴 진단 완료 · 결과 확인 · **cold-free wire GO 여부 결정**
- 완료조건: 형 GO
- 선행완료: docs/benchmarks/20260805_KNEIGHBOR_MATCH.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-05

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- knn top15 ge3=0.23 < 무작위0.311 → **NOISE** (fusion0.135와 지표 다름·혼동금지)
- neighbor wire 보류 · cold-free(COVER Δ+0.03) 별도 형 결정
