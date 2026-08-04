# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `2037617` · WORK=`IDLE`
- 지금: **K-REPACK-HYBRID** — stat+0.04·review+0.03·markov동률 · **DONE**
- 직전: K-REPACK-ANALYSIS PER_BRAIN+DECOMPOSE
- BOOT다음: **K-REPACK-HYBRID-WIRE** (stat/review p45) 또는 I2 · **형 GO**
- NEXT1: K-REPACK-HYBRID-DONE — hybrid ablation 완료 · 다음 **K-REPACK-HYBRID-WIRE**(stat/review p45+r123 · markov 유지) · **형 GO** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
