# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `df65a8a` · WORK=`IDLE`
- 지금: **K-EVOLVE-SIGNAL** — mean피드백 wire · λ HOLD · **DONE**
- 직전: K-EVOLVE-LOG Phase1 PASS
- BOOT다음: review λ=0.3 GO-WAIT 또는 FULL스냅샷 · **형 GO**
- NEXT1: K-EVOLVE-SIGNAL-DONE — SIGNAL DONE · mean(K-N차단) live · λ전뇌 HOLD · **review λ0.3** 또는 FULL스냅샷 · **형 GO** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
