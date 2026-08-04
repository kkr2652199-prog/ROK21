# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `f85de74` · WORK=`IDLE`
- 지금: **K-SIGNAL-TAXONOMY-V1** — L1·L3·L4 진단 · **DOC_SURVEY**
- 직전: K-LIVE-QUICK200-RESET
- BOOT다음: L2 EMA 진단 또는 L1 annotate stub · **형 GO**
- NEXT1: K-SIGNAL-TAXONOMY-V1-DONE — L1/L3/L4 진단 PASS · **L2 EMA 구현(진단)** 또는 **L1 deviation→annotate stub** · **형 GO** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
