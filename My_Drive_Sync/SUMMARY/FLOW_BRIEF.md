# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `339fc67` · WORK=`IDLE`
- 지금: **K-BRAIN-SIGNAL-B1-BACKTEST-100** — ge3=**0.0600** · virtual=**100%** · **FAIL** (B1도 무개선)
- 직전: K-BRAIN-SIGNAL-B1 — virtual draws · smoke **PASS**
- BOOT다음: **K-BRAIN-SIGNAL-TUNE** — _MIN_MAX_SIM 또는 롤백 · **형 GO 대기**
- NEXT1: K-BRAIN-SIGNAL-TUNE — B1-BACKTEST-100 **FAIL** ge3=0.0600(=방향1·highway 동일) · _MIN_MAX_SIM 0.90→0.85 또는 B1 롤백 · **형 GO 대기** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
