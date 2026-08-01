# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `e68abca` · WORK=`IDLE`
- 지금: **K-HIGHWAY-BACKTEST-100** — overall ge3=**0.0600** · baseline 0.1015 대비 −0.0415 · **FAIL**
- 직전: K-HIGHWAY-PHASE1 — FEEDBACK+REFEREE+QUOTA · learn adj 누적 확인
- BOOT다음: **형 GO 대기** — PHASE1 HOLD/롤백/튜닝 결정
- NEXT1: K-HIGHWAY-PHASE1-HOLD — BACKTEST-100 **FAIL** ge3=0.0600 · baseline −0.0415 · **형 GO 대기** (롤백/HOLD/튜닝) (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
