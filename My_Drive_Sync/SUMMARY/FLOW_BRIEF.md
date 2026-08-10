# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `b678490` · WORK=`IDLE`
- 지금: **K-M-REFEREE-WEIGHT** — referee GAIN식 **PATCHED** · 예측리셋·100회복습 · pred=0
- 직전: K-N-MEAN-INPUT-FIX · PATCHED
- BOOT다음: **형 GO** — ①1237 예측 생성(개발) ②추가 샘플 ③정지
- NEXT1: K-1237-DEV-PREDICT — **K-M/K-N/K-K 테스트 정합 완료**. 예측 DB 리셋됨(pred=0). 형 GO 시 **1237 예측 생성**(재료 as_of≤1236 · 개발단계). 양산 준비는 1237 개발 완료 후. (승인=형 GO)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
