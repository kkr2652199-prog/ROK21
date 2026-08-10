# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `073e8ea` · WORK=`IDLE`
- 지금: **K-PROCESS-STRUCTURE-QUERY** — 예측/채점/evolve 흐름 DOC_OK · 젠스파크 오해 정정
- 직전: K-1236-FEEDBACK-VERIFY · VERIFY_OK
- BOOT다음: **형 GO** — ①K-N mean입력 정합 ②K-M referee ③정지
- NEXT1: K-N-MEAN-INPUT-FIX — **프로세스 구조 DOC 완료 후**. K-N HOLD 해소 — 학습입력 best오인→mean/볼지표 정합. (참고: after_predict(N)=N-1채점 · 1237예측 아직0 · 형 GO) (승인=형 GO)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
