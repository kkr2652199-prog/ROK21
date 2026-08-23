# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `b4f1757` · WORK=`IDLE`
- 지금: **양산前** · 패치브리핑 DISCUSS_OK(보완필요)
- 직전: 회차연관 1–1237 APPLY_OK(읽기만)
- BOOT다음: 형 확인(맞으면패스/다르면세부) / 1237예측아님
- NEXT1: K-AWAIT-HYUNG-NEXT — **양산前**. 패치브리핑 DISCUSS_OK. 맞는번호 패스·다른번호 세부패치 1건. 시동자동화 아직아님. 1237예측 금지. (승인=형 1건)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
