# NEXT_ACTIONS.md — 다음 1건 단일 앵커 (K-AD)

> STEP1 `guard_boot` 는 **아래 `## NEXT (1건)` 블록만** 읽는다. 여러 건 나열 금지.

## NEXT (1건)
- ID: K-ATTACK-OPEN
- 할일: CONF-CAL 보류(Δ≈0·tier/RR 대패) · conf 세트순위 경로 관측종료 · 다음 공격 레버 1건 선정(READ-ONLY 우선 · WIRE 금지)
- 선행조건: K-ATTACK-CONF-CAL 완료 · spearman 약함 · cal≪tier
- 승인필요: 예 (다음 레버 선정)
- 최종갱신: 2026-07-29 (K-ATTACK-CONF-CAL)

## WORKSTATE
IDLE

---

## ARCHIVE (참고 · 훅 미사용)

| 우선순위 | 작업 | 분류 | 상태 |
|----------|------|------|------|
| — | **K-ATTACK-CONF-CAL** | 공격·관측 | **보류/관측종료** — cal≈orig · ≪tier · WIRE 금지 |
| — | **K-REFEREE-WINDOW** | 학습·referee | **완료** — W=30 · max_gap=0.1334 PASS |
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
- K-ATTACK-CONF-WIRE (CONF-CAL 미달)
