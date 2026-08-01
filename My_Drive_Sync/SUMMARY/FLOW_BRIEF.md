# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `f1ae730` · WORK=`IDLE`
- 지금: **K-ENGINE-PHASE1-HOLD** — window100 롤백 OK · fusion diag ge3=**0.0900** · **AUX_PATH_BOTTLENECK**
- 직전: K-ENGINE-PHASE1 window100 solo ge3=0.0850 FAIL · B1 rollback 완료
- BOOT다음: fusion 회복 방향 결정 · quota/aux 튜닝 검토 · **형 GO 대기**
- NEXT1: K-ENGINE-PHASE1-HOLD-DONE — fusion bottleneck **AUX_PATH_BOTTLENECK** 판정 · diag ge3=0.0900 · quota 0.40/aux 0.67 · 회복 방향 결정 · **형 GO 대기** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
