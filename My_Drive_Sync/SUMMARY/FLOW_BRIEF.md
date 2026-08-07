# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `caf49bd` · WORK=`IDLE`
- 지금: **K-PAST-LEARN-TUNE-SOFT** — 시드고정 15셀 동일 · **KEEP_BASE**
- 직전: K-PAST-LEARN-WIRE · PASS
- BOOT다음: engine 생성단 튜닝 · **형 GO**
- NEXT1: K-PAST-LEARN-TUNE-ENGINE — soft rerank 무효과(KEEP_BASE) → engine v2 윈도우/가중 스윕 설계·실측 · `random.choices` 동결 유지 · ASSOC OFF (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
