# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-TRANSITION-COLLECT-DESIGN
- 할일: transition 패턴 수집(DB/로그) 설계 · **wire/뇌/발권 미접촉** · 방향성 브리핑(`DIRECTION_BRIEF_CURSOR`) 확인 후 진행
- 완료조건: 형 GO
- 선행완료: docs/benchmarks/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.json
- 승인필요: 미확인
- 선행조건: docs/benchmarks/20260805_KTRANSITION_FULL.json
- 최종갱신: 2026-08-05

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- **Cursor 브리핑 SSOT:** `reports/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.md`
- STRONG(Δ+0.172)=미세신호 · 「stat 교체 즉시」문구는 **철회** → 수집 먼저
- STEP: 수집→재검증→형GO 후 뇌재설계→자동화
- K-ANALOG=UI 별트랙 · 본선 아님
