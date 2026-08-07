# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-PAST-LEARN-DETAIL-APPLY
- 할일: decay 후보 `LONG=0.01`/`SHORT=0.05`(hold ge3**0.16**·fusion**0.135**) 상수적용 or KEEP_BASE · **형 GO**
- 완료조건: 형 GO 후 적용/보류 실행
- 선행완료: docs/benchmarks/20260808_KPAST_LEARN_DETAIL_TUNE.json
- 승인필요: 필요
- 선행조건: 없음
- 최종갱신: 2026-08-08

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- base L0.005/S0.05: tune**0.28**/hold**0.14** · 후보 L0.01/S0.05: tune**0.24**/hold**0.16** · fusion Δ**0**
- applied=False · 이득 작음(hold +0.02, tune −0.04)
