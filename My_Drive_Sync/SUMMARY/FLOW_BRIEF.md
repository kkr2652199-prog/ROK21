# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `484b145` · WORK=`IDLE`
- 지금: **K-PAST-LEARN-SCORE-RULE-DIAG** — 논문식 재채점 · **NO_SKILL_VS_NULL**(KEEP_BASE 지지)
- 직전: K-PAST-LEARN-DETAIL-KEEP · KEEP_BASE
- BOOT다음: soft태그 EV(인기회피) 재정의 or 트랙정지 · 발권가중 금지 · **형 GO**
- NEXT1: K-PAST-LEARN-EV-RELABEL-GO — SCORE-RULE-DIAG 결과(적중축 상한 없음) 형 확인 — soft 태그(hot1y/overdue)를 **EV 인기회피축**으로 라벨 재정의할지 결정 · 결정 전 코드·가중 변경 금지 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
