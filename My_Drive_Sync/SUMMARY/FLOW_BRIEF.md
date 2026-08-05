# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `779ef42` · WORK=`IDLE`
- 지금: **K-TRANSITION-FUSION-N200** — fusion n200 · **ROLLBACK**(WIRE OFF)
- 직전: K-TRANSITION-STEP4-WIRE · PASS
- BOOT다음: n200 결과 형 확인 · 통계요정 복귀 유지 · **형 GO**
- NEXT1: K-TRANSITION-FUSION-N200-DONE — n200 결과 형 확인 · KEEP→현배선유지 / MARGINAL→추가검증or조건부유지 / ROLLBACK→`K_STAT_TRANSITION_V1=0` 즉시적용(**적용완료·WIRE=False**) · 다음회차 자동수집 대기 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
