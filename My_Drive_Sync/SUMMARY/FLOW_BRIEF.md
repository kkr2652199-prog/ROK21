# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `bc8c32e` · WORK=`IDLE`
- 지금: **K-FUSION-QUOTA-FIX** — DEFAULT 25/60/15 · n=100 ge3=**0.0800** · quota **20/60/20** · **FAIL** (>0.09)
- 직전: K-ENGINE-PHASE1-HOLD fusion diag ge3=0.0900 · AUX_PATH_BOTTLENECK · quota 40/40/20
- BOOT다음: fusion ge3 0.08→0.09+ 추가 회복(aux path 등) · **형 GO 대기**
- NEXT1: K-FUSION-QUOTA-FIX-DONE — fusion ge3 **0.0800** (<0.09 gate) · quota shift 40/40/20→**20/60/20** 적용 완료 · aux path 등 추가 회복 검토 · **형 GO 대기** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
