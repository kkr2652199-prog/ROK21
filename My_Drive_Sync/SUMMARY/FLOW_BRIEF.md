# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `791ecfb` · WORK=`IDLE`
- 지금: **양산前** · pool품질 · oversample markov**5** APPLY · jaccard HOLD
- 직전: 뇌별독립감독관 WIRE_OK · 예측감사OK
- BOOT다음: **형 지시** 1건 / 1237아님
- NEXT1: K-POOL-QUALITY-HOLD — **양산前**. pool품질: jaccard **HOLD**(0.85) · oversample markov**5** APPLY(stat/review3). 다음=형 지시1건. **1237아님**. (승인=형 다음 지시)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
