# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `25b62d6` · WORK=`IDLE`
- 지금: **K-BLEND-STRENGTH-SWEEP** — 9×5 스윕 **NO_IMPROVE** · BLEND=0.55 유지 · APPLY 금지
- 직전: K-GENSPARK-IDEA-CHECK · CHECK_DONE
- BOOT다음: **형 GO** — ①정지/다른축 ②임계완화 재스윕(비권장) ③명분리뷰
- NEXT1: K-BLEND-STRENGTH-SWEEP-DONE — **BLEND_STRENGTH 스윕 완료(NO_IMPROVE)**. best=null · 현재 0.55 유지 · wire否. 형 판단 — ①정지 ②다른 축(비권장: thr완화/뇌별W) ③명분리뷰. APPLY 대기 아님. (승인=형 GO)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
