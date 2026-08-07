# NEXT_ACTIONS.md — 다음 1건만 커서에 지시 (K-AD)

> STEP1 guard_boot 는 **아래 ## NEXT (1건) 블록만** 읽는다. 다른 섹션 무시.

## NEXT (1건)
- ID: K-PAST-LEARN-TUNE-ENGINE
- 할일: soft rerank 무효과(KEEP_BASE) → engine v2 윈도우/가중 스윕 설계·실측 · `random.choices` 동결 유지 · ASSOC OFF
- 완료조건: engine 스윕 JSON + 후보1안 · 형 GO 전 fusion n200 금지
- 선행완료: docs/benchmarks/20260808_KPAST_LEARN_TUNE_SOFT.json
- 승인필요: 미확인
- 선행조건: 없음
- 최종갱신: 2026-08-08

## WORKSTATE
IDLE

---

## 메모 (커서 아님 · guard 무시)

- TUNE-SOFT: seed(42000+dno) 15셀 전부 ge3**0.12**/mean**1.78** · soft conf만으로는 pick 불변
- 상수 w0.12/cap3.0 유지 · env `K_PAST_LEARN_SOFT_*` 가능
