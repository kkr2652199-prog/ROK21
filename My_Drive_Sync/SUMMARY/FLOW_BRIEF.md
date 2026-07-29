# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `6a6a855` · WORK=`IDLE`
- 지금: **K-BENCH-01-WIRE FAIL** — tier 피드백 ge3=0.1142·롤백 · **AUX 신호전환 제안** 문서화
- 직전: K-BENCH-01 postmortem SIGNAL_FOUND — 쿼터갭43.6%·markov52.5% · AUX↔hit 무상관
- BOOT다음: K-AUX-SIGNAL-01 survey (READ-ONLY) — 4보조 채점→신호전달 · coordinator 별도 GO
- NEXT1: K-AUX-SIGNAL-01 — 4보조 역할 전환 survey (READ-ONLY) — 채점→신호벡터 힌트 시뮬 · `reports/20260729_AUX_SIGNAL_PIVOT.md` E1 참고 · coordinator 변경은 별도 GO (승인=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
