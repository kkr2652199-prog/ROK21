# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `399391a` · WORK=`IDLE`
- 지금: **K-TRANSITION-STEP4-WIRE** — transition_v1 · **PASS**(smoke)
- 직전: STEP3 DESIGN_HOLD · 형A=GO
- BOOT다음: fusion n200 재검증/롤백 · **형 GO**
- NEXT1: K-TRANSITION-STEP4-WIRE-DONE — STEP4 배선 완료 · **fusion n200 live 재검증** 또는 롤백(`K_STAT_TRANSITION_V1=0`) 결정 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
