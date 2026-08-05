# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `a518cdf` · WORK=`IDLE`
- 지금: **K-TRANSITION-COLLECT-DESIGN** — transition_log · **PASS**
- 직전: DIRECTION_BRIEF_CURSOR · COLLECT_FIRST
- BOOT다음: STEP2 재검증 또는 자동수집 · **형 GO**
- NEXT1: K-TRANSITION-COLLECT-DESIGN-DONE — 수집 구조 완료 · backfill 검증 · 형 확인 → **STEP2 (데이터 재검증)** 또는 다음 회차 자동수집 대기 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
