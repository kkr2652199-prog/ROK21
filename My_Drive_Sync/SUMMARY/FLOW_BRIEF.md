# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `b525683` · WORK=`IDLE`
- 지금: **K-N-MEAN-INPUT-FIX** — WF 학습입력 mean **PATCHED** · 3뇌 테스트단계 · 다음=K-M
- 직전: K-PROCESS-STRUCTURE-QUERY · DOC_OK
- BOOT다음: **형 GO** — ①K-M referee 가중 ②1237 예측 생성(개발) ③정지
- NEXT1: K-M-REFEREE-WEIGHT — **K-N PATCHED 후**. K-M HOLD 해소 — referee 가중 실효격차(균등≈0) 설계·패치. (3뇌 테스트/개발 단계 · 1237 양산前 · mean 학습입력 정합 완료) (승인=형 GO)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
