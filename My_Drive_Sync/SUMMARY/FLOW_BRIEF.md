# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `7f8964b` · WORK=`IDLE`
- 지금: **양산前** · markov 선호순위 APPLY_OK
- 직전: ρprefer 0.22→0.93 · prefer+0.035
- BOOT다음: 형 1건 / 1237예측아님
- NEXT1: K-AWAIT-HYUNG-NEXT — **양산前**. 선행=K-MARKOV-PREFER-DNA-RANK APPLY_OK(markov만). 다음=형 1건. 시동·1237예측 금지. (승인=형 1건)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
