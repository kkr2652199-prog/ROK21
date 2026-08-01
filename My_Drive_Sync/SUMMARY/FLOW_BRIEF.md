# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `1478e0c` · WORK=`IDLE`
- 지금: **K-COMBO-SIGNAL-01 QUICK PASS** — baseline ge3=0.145 · signal_AB=0% (AND 미발화)
- 직전: K-EXCLUDE-SURVEY FAIL · SELECT-FULL FAIL · LEAKAGE_POLICY
- BOOT다음: **K-COMBO-SIGNAL-FULL** — n=1182 · signal_A 재검토 · **전체 큐=`TEST_PRIORITY.md`**
- NEXT1: K-COMBO-SIGNAL-FULL — K-COMBO-SIGNAL-01 QUICK **PASS** → full n=1182 검증 · signal_A 0% 재검토 · wire는 형 GO 전 금지 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
