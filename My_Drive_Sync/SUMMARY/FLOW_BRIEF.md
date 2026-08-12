# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `c50c072` · WORK=`IDLE`
- 지금: **양산前** · L11b markov prefer **HOLD** · NEXT=L11c stat
- 직전: L11b K-MARKOV-PREFER-ALIGN HOLD (생일대 prefer↓)
- BOOT다음: L11c K-STAT-HOMEWORK-QUALITY / 1237아님
- NEXT1: K-STAT-HOMEWORK-QUALITY — **양산前**. L11b markov prefer **HOLD**(생일대보너스 prefer↓·BLEND/W_CROWD재탕안함). 다음=**L11c** stat homework 잔여(pool품질·hint weeks·기스윕노브재탕금지). **1237아님** · 강제BT보류 · S1 개별승인. (승인=없음(리스트 순서))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
