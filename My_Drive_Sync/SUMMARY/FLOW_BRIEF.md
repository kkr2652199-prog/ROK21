# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `2a4435c` · WORK=`IDLE`
- 지금: **K-COMBO-V2 QUICK FAIL** — combo_v2 ge3=0.125 · baseline=0.145 · B3_cov=100%
- 직전: K-COMBO-SIGNAL-01 · K-EXCLUDE-SURVEY · SELECT-FULL
- BOOT다음: **K-ATTACK-HOLD** — wire HOLD · **전체 큐=`TEST_PRIORITY.md`**
- NEXT1: K-ATTACK-HOLD — COMBO-V1/V2 wire HOLD · baseline 미개선 · 형 GO 또는 10SET·배제 재설계 전까지 survey 중단 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
