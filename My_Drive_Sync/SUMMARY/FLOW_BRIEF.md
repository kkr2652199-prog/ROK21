# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `7b8591f` · WORK=`IDLE`
- 지금: **TESTLOTTO UI+DB** — 10+5 pool · 백테스트 DB 2건 · 한국어 라벨
- 직전: K-SIGNAL-REPACK-01 · SELECT-01 QUICK PASS · REPORT_STYLE
- BOOT다음: K-SIGNAL-SELECT-FULL — 형 7021 육안 확인 → full 1182 · **전체 큐=`TEST_PRIORITY.md`**
- NEXT1: K-SIGNAL-SELECT-FULL — **형 7021 UI·백테스트 DB 육안 확인** → full n=1182 walk-forward 재실행 · pin+p<0.05 확인 · wire는 형 GO 전 금지 (승인=full 실행=아니(QUICK PASS 후 자동) · wire=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
