# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `c2a4ad1` · WORK=`IDLE`
- 지금: **K-BENCH-01 postmortem SIGNAL_FOUND** — 쿼터갭 43.6%·markov 15중 best 52.5% · AUX↔hit 무상관 · ge3=0.11
- 직전: 4보조·피드백 READ-ONLY — set_no_asc 컷 없음 · K-BENCH-02 FAIL
- BOOT다음: K-BENCH-01-WIRE — 형 GO 후 피드백축 검토 (coordinator 수정 별도 GO)
- NEXT1: K-BENCH-01-WIRE — K-BENCH-01 postmortem SIGNAL_FOUND — 쿼터갭 43.6%·markov best 52.5% · 형 GO 후 피드백축 WIRE 검토 (coordinator 수정은 별도 GO) (승인=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
