# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `913098f` · WORK=`IDLE`
- 지금: **양산前** · K-F지시서 **REJECT_REWRITE** · 젠스파크질문대기
- 직전: LEARN_WIRED이미True·learn재료0 · 지시서실행보류
- BOOT다음: 젠스파크답+형GO → K-F재작성 지시 / 또는 다른후보
- NEXT1: K-F-REWRITE-WAIT — **양산前**. K-F 지시서 **REJECT_REWRITE**(LEARN_WIRED이미True·learn재료0·구경로FINDINGS). 실행보류. 형이 젠스파크에 `reports/20260811_KF_GENSPARK_QUESTIONS.md` 붙여넣기 → 답+형GO 후 재지시. **1237아님**. (승인=형·젠스파크)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
