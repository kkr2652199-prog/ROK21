# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `5675df6` · WORK=`IDLE`
- 지금: **R38 게이트 강제 가동** — `tools/k_gate.py` 공용모듈 · 벤치 `decision_gate` 기록 필수 · 준수검사 **COMPLIANT**(자기검증 8/8 · 184벤치 · legacy132면제 · 위반0 · 프로브로 exit=1 실동작 확인)
- 직전: K-STAT-DECISION-GATE — 적용상수 win26/mix0.8=**NOISE_SELECTION_CONFIRMED** · 순서불변 2.429e-17 · 문제답 nopeek 0.274<무작위 0.311
- BOOT다음: ①seed full-range로 잡음하한 확정 ②1236+ 전향적 EV로그 ③기존 legacy 판정 게이트 소급적용 중 **형 1건 선택** · 발권가중 금지
- NEXT1: K-GATE-NEXT-PICK — R38 게이트 가동 완료(공용모듈 승격 · 준수검사 COMPLIANT · 강제 exit=1 실동작 확인) 형 확인 후 1건 선택 — **①seed 민감도 full-range 재측정으로 잡음 하한 확정**(권장 · 현재 폭 0.14 는 n=100 단일 추정 · 약 25분) / ②회차 1236+ 전향적 EV 로그(개입 없음 · 저번호·저합 인기축 검증) / ③legacy 132건 중 상수·배선에 영향 준 판정만 골라 게이트 소급적용 / ④트랙정지 (승인=없음 (①~③ 모두 측정·기록만 · 발권경로 무변경))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
