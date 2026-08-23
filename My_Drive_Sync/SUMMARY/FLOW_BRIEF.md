# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `d758ab3` · WORK=`IDLE`
- 지금: **양산前** · 회차형태지식 leftover COMMIT_OK
- 직전: 회차형태지식 1오더 APPLY_OK
- BOOT다음: 형 다음오더(전체조합 반영은 아직) / 1237예측아님
- NEXT1: K-AWAIT-HYUNG-NEXT — **양산前**. 회차형태지식 1오더 APPLY_OK(1–1238 회차별 저장·엔진읽기만·발권불변). 몰아주기/전체조합 미접촉. 다음오더=형(전체조합 반영은 아직). 1237예측 금지. (승인=형 1건)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
