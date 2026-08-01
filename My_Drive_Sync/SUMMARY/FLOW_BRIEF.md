# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `b50a3f2` · WORK=`IDLE`
- 지금: **K-EXCLUDE-SURVEY QUICK FAIL** — λ sweep n=200 · best exclude ge3=0.145=baseline · λ0.25 하락
- 직전: K-SIGNAL-SELECT-FULL · K-EXCLUDE-HIST-01 · LEAKAGE_POLICY
- BOOT다음: **K-ATTACK-HOLD** — SELECT/EXCLUDE wire HOLD · **전체 큐=`TEST_PRIORITY.md`**
- NEXT1: K-ATTACK-HOLD — SELECT/EXCLUDE wire HOLD 유지 · 형 GO 또는 새 축(10SET·패턴튜닝) 전까지 survey 중단 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
