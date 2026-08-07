# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `aac28d3` · WORK=`IDLE`
- 지금: **K-PAST-LEARN-EV-RELABEL** — 1등당첨자수 NB2+무작위화 · 인기편향 FW p=**0.0004** 실증 · **태그축은 무신호(재정의 지지 안 됨)**
- 직전: K-PAST-LEARN-SCORE-RULE-DIAG · NO_SKILL_VS_NULL · + AUDIT-DIMS 감사(잔여 6건)
- BOOT다음: ①seed full-range ②1236+ 전향적 EV로그 ③cycle_gap_boost 단독AB 중 **형 1건 선택** · 발권가중 금지
- NEXT1: K-PAST-LEARN-NEXT-PICK — EV-RELABEL 결과(인기편향 FW p=0.0004 실증 · **태그축 무신호 → soft 재정의 지지 안 됨**) 형 확인 후 다음 1건 선택 — **①seed 민감도 full-range 재측정** (권장 · 잡음 하한 미확정 상태로 그동안 판정해왔음) / ②회차 1236+ 전향적 EV 로그(개입 없음) / ③`cycle_gap_boost` 단독 A/B / ④트랙정지 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
