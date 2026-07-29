# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-ATTACK-HOLD
- 할일: AUX-WEIGHT-SURVEY FAIL(13조합 ge3=0.1100 동일·Δ-0.0347·p=0.669622) · V2 set_no 경로 AUX_WEIGHTS 실레버 아님 · 다음 공격축 형 결정 대기
- 완료조건: 형이 다음 1축 지정 또는 HOLD 유지 확인
- 승인필요: 예
- 선행완료: 2026-07-29 (K-AUX-WEIGHT-SURVEY FAIL)

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- V2 pin ge3=0.1447 · mean=1.7504 (stored)
- AUX-WEIGHT live baseline ge3=0.1100 · 13조합 전부 동일 (set_no 쿼터)
- STAT-WIRE live ge3=0.1176 (롤백완료)
- 근거: docs/benchmarks/20260729_KAUX_WEIGHT_survey.json
