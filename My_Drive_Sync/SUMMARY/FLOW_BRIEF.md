# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `83378a5` · WORK=`IDLE`
- 지금: **K-BRAIN-SIGNAL-BACKTEST-100** — ge3=**0.0600** · signal_active=**100%** · **FAIL** (=highway 동일)
- 직전: K-BRAIN-SIGNAL-A1 — pattern_signal + coordinator blend · **PASS**
- BOOT다음: **K-BRAIN-SIGNAL-TUNE** — _MIN_MAX_SIM 조정 · **형 GO 대기**
- NEXT1: K-BRAIN-SIGNAL-TUNE — BACKTEST-100 **FAIL** ge3=0.0600(=highway 동일) · signal_active 100% · _MIN_MAX_SIM 0.90→0.85 재검증 · **형 GO 대기** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
