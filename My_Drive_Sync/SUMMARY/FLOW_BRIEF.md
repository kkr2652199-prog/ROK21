# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `9a44877` · WORK=`IDLE`
- 지금: **K-STAT-DECISION-GATE** — 판정눈금 확정 · **RULER_TOO_COARSE** · 적용상수 win26/mix0.8=**NOISE_SELECTION_CONFIRMED**(n50·K10 Δ0.16 = 잡음p95 0.16 · holdout 0.14≈null) · 순서불변 증명 2.429e-17
- 직전: K-PAST-LEARN-EV-RELABEL(인기편향 FW p=0.0004 · 태그축 무신호) · SCORE-RULE-DIAG(NO_SKILL)
- BOOT다음: ①게이트 도구화 전면적용(권장) ②seed full-range ③1236+ 전향적 EV로그 중 **형 1건 선택** · 발권가중 금지
- NEXT1: K-STAT-GATE-ADOPT — DECISION-GATE 결과(**적용상수 win26/mix0.8 = NOISE_SELECTION_CONFIRMED** · 순서불변 2.429e-17 · 문제→답 nopeek 0.274 < 무작위 0.311) 형 확인 후 1건 선택 — **①게이트를 공용 모듈로 승격해 모든 튜닝 도구가 gate(n,k) 기록 강제**(권장 · 잡음보다 작은 차이 채택을 구조적으로 차단) / ②seed full-range 재측정으로 잡음 하한 확정 / ③회차 1236+ 전향적 EV 로그(개입 없음) / ④트랙정지 (승인=①은 도구 신규모듈(발권경로 무변경) → 형 GO 필요)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
