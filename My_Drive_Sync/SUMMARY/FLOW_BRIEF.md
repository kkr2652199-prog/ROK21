# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `f2f851f` · WORK=`IDLE`
- 지금: **K-TRANSITION-STEP3-DESIGN** — **DESIGN_HOLD**
- 직전: K-TRANSITION-STEP2-VERIFY · PASS
- BOOT다음: STEP4 패치 또는 HOLD · **형 GO**
- NEXT1: K-TRANSITION-STEP3-DESIGN-DONE — 설계 결과 형 확인 → **STEP4(실제 stat 교체 패치) GO 여부** 결정 (현재 replace=**HOLD**) (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
