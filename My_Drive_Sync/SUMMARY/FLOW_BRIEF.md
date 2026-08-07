# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `97ea170` · WORK=`IDLE`
- 지금: **K-PAST-LEARN-WIRE** — 과거학습 구조패치 · smoke **PASS** · solo n50 ge3**0.14**
- 직전: K-STAT-NUM-ASSOC-FULL · NOISE_LIKE
- BOOT다음: 튜닝재개 · SOFT_WEIGHT 스윕 · **형 GO**
- NEXT1: K-PAST-LEARN-TUNE-SOFT — past_learn SOFT_WEIGHT/SOFT_CONF_CAP 스윕 · solo n50 vs wire베이스(ge3**0.14**/mean**1.58**) · ASSOC기본OFF 유지 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
