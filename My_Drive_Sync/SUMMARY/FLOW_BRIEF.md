# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `6d51588` · WORK=`IDLE`
- 지금: **양산前** · stat 6~10복습 BT200 PASS · COVER_MIN_HITS=3 · NEXT=형다음(markov)
- 직전: 리셋+stat만200 · v1표빔 → 3맞복습 패치 재BT
- BOOT다음: 형 다음 1건(권고=markov 동일배선) / 1237아님
- NEXT1: K-AWAIT-HYUNG-NEXT — **양산前**. stat 6~10복습 **BT200 PASS** · COVER_MIN_HITS**3**. 1~5불변. 다음=**형 다음 1건**(권고: markov 동일 소비). **1237아님**. (승인=**형 다음 1건**)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
