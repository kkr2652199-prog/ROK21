# NEXT_ACTIONS.md — 다음 1건 단일 앵커 (K-AD)

> STEP1 `guard_boot` 는 **아래 `## NEXT (1건)` 블록만** 읽는다. 여러 건 나열 금지.

## NEXT (1건)
- ID: K-REFEREE-WINDOW
- 할일: learn_state.py + learn_state_cutoff.py 동시 패치 — recent_avg_match 누적평균 → 슬라이딩 윈도우(WINDOW=30) 교체. K-ATTACK-CONF-CAL 은 그 다음 NEXT로 ARCHIVE에 보류 등록.
- 선행조건: 동생·형 합의 완료 · CONF-CAL 보류
- 승인필요: 아니오
- 최종갱신: 2026-07-29 (NEXT 교체 · REFEREE-WINDOW)

## WORKSTATE
IDLE

---

## ARCHIVE (참고 · 훅 미사용)

| 우선순위 | 작업 | 분류 | 상태 |
|----------|------|------|------|
| 다음 | **K-ATTACK-CONF-CAL** | 공격·관측 | **보류** — REFEREE-WINDOW 완료 후 NEXT 복귀 · 뇌내 conf 보정·세트순위 시뮬(READ-ONLY) |
| — | K-00 과거예측 숙제 확장 | 숙제·명분 | **완료 K-00** |
| — | K-1235-PREP 1235 루프 준비 | 선행 | **완료** |
| — | K-H 미등록 AUX _unused 격리 | 위생 | **완료 K-H** |
| — | K-B BENCH SSOT 고정·기계검증 | 프로토콜 | **완료 K-B** |
| — | K-W post-KP3 재측정 | 관측 | **완료 K-W** |
| — | K-P5 hyodo LSTM·인프라 UI | UI | **완료 K-P5** |
| — | K-PIN-CLOSE drift·3DB 마감 | 검증 | **완료 K-PIN-CLOSE** |

### HOLD
- 1군 직접수정 (구매주간 금지)
- 적중률 목표 (물리적 불가)
