# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-RARE-FILTER-PREP-DONE
- 할일: R0~R3 준비 PASS · **taxonomy v1(홀짝·존 전수) 측정확장** 또는 **1236 ops SCORE** · **형 GO**
- 완료조건: 형 선택
- 선행완료: docs/benchmarks/20260805_KRARE_FILTER_DESIGN.json · MEASURE · TAG_SPEC

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- RARE_ANNOTATE_WIRE=False · 정책 off · λ/cover HOLD
- 1236 실추첨 전 컨닝 금지 · 티켓등확률 사실 유지
- 재측정: `python tools/_k_rare_measure_1_1235.py`
