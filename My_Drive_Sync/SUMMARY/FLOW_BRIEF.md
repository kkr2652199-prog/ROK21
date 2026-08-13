# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `e667960` · WORK=`IDLE`
- 지금: **양산前** · L11c stat homework **HOLD** · NEXT=L12 형승인
- 직전: L11c K-STAT-HOMEWORK-QUALITY HOLD (WIN_1Y |Δ|미달)
- BOOT다음: L12 K-TICKET-POOL-UNIFY / 형승인 / 1237아님
- NEXT1: K-TICKET-POOL-UNIFY — **양산前**. L11c stat homework **HOLD**(WIN_1Y=52·HINT/Jaccard/oversample재탕안함). 다음=**L12** 발권5↔pool10+repack5 **통합**(형 「패치 후 10세트도 발권」의도). **지금 강제 병합 금지 · 형 승인 후**. **1237아님** · 강제BT보류 · S1 개별승인. (승인=**형 승인**)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
