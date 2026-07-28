# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `c2c26a6` · WORK=`IDLE`
- 지금: NEXT 교체 — **K-REFEREE-WINDOW** (합의) · CONF-CAL ARCHIVE 보류
- 직전: K-ATTACK-BAYES soft≈null · invcorr<RR
- BOOT다음: learn_state(+cutoff) 슬라이딩 윈도우 WINDOW=30
- NEXT1: K-REFEREE-WINDOW — learn_state.py + learn_state_cutoff.py 동시 패치 — recent_avg_match 누적평균 → 슬라이딩 윈도우(WINDOW=30) 교체. K-ATTACK-CONF-CAL 은 그 다음 NEXT로 ARCHIVE에 보류 등록. (승인=아니오)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
