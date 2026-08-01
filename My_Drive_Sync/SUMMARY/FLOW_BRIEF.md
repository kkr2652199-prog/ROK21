# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `1bd771d` · WORK=`IDLE`
- 지금: **K-AUX-DIAG** — baseline ge3=**0.0800** · markov survival **0.668** · worst aux **pattern_spotlight**
- 직전: K-FUSION-QUOTA-FIX ge3=0.0800 · quota 20/60/20 · FAIL (>0.09)
- BOOT다음: aux 회복 방향(spotlight/balance) 결정 · **형 GO 대기**
- NEXT1: K-AUX-DIAG-DONE — aux ablation 완료 · worst **pattern_spotlight** · balance_keeper markov 억제 · ge3 전 시나리오 **0.0800** · 회복 방향 결정 · **형 GO 대기** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
