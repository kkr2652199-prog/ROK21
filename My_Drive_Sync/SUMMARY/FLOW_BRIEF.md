# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `53c20b8` · WORK=`IDLE`
- 지금: **K-BRAIN-TUNE-SURVEY** — P0 aux_hint_top5=0.1091 · best_combo ge3=**0.1032** · live_baseline 0.1218 미달 · **HOLD**
- 직전: K-BACKTEST-FULL-C — C package FULL ge3=0.1015 · QUICK collapse −0.0235 · **FAIL**
- BOOT다음: **K-BRAIN-TUNE-APPLY** — survey HOLD 권고 · tune apply · **형 GO 대기**
- NEXT1: K-BRAIN-TUNE-APPLY — survey HOLD 권고 · 형 GO 시 wire/hint/lb A/B apply · auto-apply 금지 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
