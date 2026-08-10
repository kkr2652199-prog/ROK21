# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `36fc78f` · WORK=`IDLE`
- 지금: **K-KK-FEEDBACK-WIRE** — routes 피드백 연결 **PATCHED** · weight=0 · K-M/K-N HOLD
- 직전: K-BLEND-STRENGTH-SWEEP · NO_IMPROVE
- BOOT다음: **형 GO** — ①K-M referee 설계 ②K-N mean입력 정합 ③정지
- NEXT1: K-KK-FEEDBACK-WIRE-DONE — **K-K PATCHED 완료**. routes 클릭/수집→feedback 연결 · weight_applied=0.0 유지. 형 판단 — ①K-M referee 가중 설계 ②K-N mean 입력 정합(권장 선행) ③정지. (피드백 경로 살아 있으나 referee 균등·best오인 HOLD) (승인=형 GO)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
