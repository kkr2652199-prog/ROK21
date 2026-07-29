# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `75be8e9` · WORK=`IDLE`
- 지금: **4보조·피드백 READ-ONLY 검토 완료** — AUX=15장 채점·set_no_asc면 컷 없음 · 피드백 뼈대만 · GenSpark 형6문 답변 일치
- 직전: K-BENCH-02 FAIL — confidence/AUX < set_no_asc baseline ge3=0.1100 · pin 미달
- BOOT다음: K-ATTACK-HOLD — V2 pin 유지 · 형 다음 1축 (K-BENCH-01 또는 HOLD)
- NEXT1: K-ATTACK-HOLD — K-BENCH-02 FAIL(confidence/AUX 정렬 전축 ge3≤0.1100·baseline 최고) · V2 pin 유지 · 형 다음 1축 지정 대기 (K-BENCH-01 postmortem 또는 HOLD) (승인=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
