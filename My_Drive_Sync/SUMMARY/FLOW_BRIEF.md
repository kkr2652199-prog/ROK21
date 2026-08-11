# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `aed02a9` · WORK=`IDLE`
- 지금: **양산前** · ⑧quota min_each=1 **APPLY_OK** (m3/r1/s1)
- 직전: ⑥K-I WIRE_OK · ⑦post-refill SMOKE_OK
- BOOT다음: **형 지시** 1건 / 1237아님
- NEXT1: K-QUOTA-MIN-EACH-HOLD — **양산前**. ⑧quota **APPLY_OK**(min_each1·live m3/r1/s1). 다음=형 지시1건. **1237아님**. (승인=형 다음 지시)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
