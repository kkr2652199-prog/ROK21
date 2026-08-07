# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `1b886bb` · WORK=`IDLE`
- 지금: **K-PAST-LEARN-TUNE-ENGINE** — 후보 win26/mix0.8 ge3**0.28** · **CANDIDATE**
- 직전: K-PAST-LEARN-TUNE-SOFT · KEEP_BASE
- BOOT다음: 후보 상수적용 or fusion · **형 GO**
- NEXT1: K-PAST-LEARN-TUNE-ENGINE-APPLY — 후보 `short_win=26`/`short_mix=0.8`(seed n50 ge3**0.28** Δ+0.16) 상수적용 여부 · 또는 fusion n200 검증 · **형 GO** (승인=필요)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
