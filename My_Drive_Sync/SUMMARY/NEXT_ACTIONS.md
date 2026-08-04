# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-QUOTA-D-WIRE-DONE
- 할일: quota D wire **FAIL·롤백완료** · 검증 결과 확인 · **형 GO**(다음: live경로 재측정 또는 다른 후보)
- 완료조건: 형 확인
- 선행완료: docs/benchmarks/20260805_KQUOTA_D_WIRE.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-05

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- n100 avg ge3=0.10 · full=0.115 → 하드롤백 · BENCH_FIXED_QUOTA=None · fusion 0.135 복원
- PREP 0.170은 hybrid repack 시뮬 ≠ live predict_sets
