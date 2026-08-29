# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `20d0049` · WORK=`IDLE`
- 지금: **양산前** · 2–1238 3뇌 벡터 REFILL_OK
- 직전: 예측초기화 후 2–1238 재백필
- BOOT다음: 형 1건 / 1239예측아님
- NEXT1: K-AWAIT-HYUNG-NEXT — **양산前**. 선행=K-3BRAIN-VECTOR-REFILL-2-1238 REFILL_OK(2–1238). 다음=형 1건. 시동·1239예측 금지. (승인=형 1건)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
