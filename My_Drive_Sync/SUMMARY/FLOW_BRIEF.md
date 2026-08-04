# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `7e010bf` · WORK=`IDLE`
- 지금: **K-EVOLVE-AUTO-S3** — PREDICT 1236 캐시 · **PASS**
- 직전: K-EVOLVE-AUTO-S2 SCORE 1235
- BOOT다음: S4 EVOLVE_AUTO=1 운영 또는 다른축 · **형 GO**
- NEXT1: K-EVOLVE-AUTO-S3-DONE — S3 PREDICT 1236 캐시 PASS · **S4 EVOLVE_AUTO=1 운영** 또는 다른축 · **형 GO** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
