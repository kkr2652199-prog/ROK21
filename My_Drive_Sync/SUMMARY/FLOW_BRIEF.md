# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `dc96602` · WORK=`IDLE`
- 지금: **양산前** · 숙제소비=과거학습만 RESTORE
- 직전: 형정정 · review200 안함 · stat10장 불변100
- BOOT다음: 형 1건(과거학습) / 1237아님
- NEXT1: K-AWAIT-HYUNG-NEXT — **양산前**. **과거학습(stat)만**. S1~S5완료. 숙제소비 라이브=`{stat}`. markov/review 숙제·S1~S4는 지시 시. **1237아님**. (승인=형 다음지시)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
