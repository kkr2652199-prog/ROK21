# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ATTACK-HOLD
- 할일: GENDIV FAIL(corr|r|<0.03 · Q1 ge3 0.1224·Δ-0.0223 · Q1−Q5=-0.0344) · WIRE금지 · V2유지 · GENDIV재탕금지 · 슬롯재선택계열지양 · 형·커서 다음 직교축 1건 재선정
- 완료조건: K-GENDIV 관측완료 · recommended=없음(HOLD·V2유지)
- 승인필요: 예
- 선행완료: 2026-07-29 (K-GENDIV FAIL)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- V2 pin ge3=0.1447 · mean=1.7504
- diversify_pick jaccard_penalty=0.85 · oversample=max(3n,n+5) 유지
- 근거: docs/benchmarks/20260729_KGENDIV_survey.json · reports/20260729_KGENDIV.md
