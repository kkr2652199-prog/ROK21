# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `0450d5a` · WORK=`IDLE`
- 지금: **K-STAT-NUM-ASSOC-SAMPLE** — 과거30회 리프트샘플 · **MEASURED**
- 직전: K-STAT-NUM-ASSOC · MEASURED
- BOOT다음: 형 논의 · 전수여부 · WIRE금지 · **형 GO**
- NEXT1: K-STAT-NUM-ASSOC-SAMPLE-DONE — SAMPLE n30 결과 형 논의 · meanL≈1 · top1_hit&lt;null → 전수/정지 결정 (과거학습 · WIRE금지) (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
