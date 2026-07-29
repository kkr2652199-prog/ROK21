# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `d641717` · WORK=`RUNNING:K-WINDOW-SIGNAL-01`
- 지금: **K-WINDOW-SIGNAL-01 running** ~900/1182 · 신호셋트 아키텍처 3자 합의 문서화
- 직전: K-AUX-SIGNAL-01 FAIL ge3=0.1303 · 1군 벤치 인벤토리 · AUX_SIGNAL_PIVOT
- BOOT다음: K-WINDOW 완료→K-SIGNAL-SELECT-01 overlap survey (coordinator 무수정)
- NEXT1: K-WINDOW-SIGNAL-01 — survey 완료 대기(kill 금지) → JSON+보고서 확정 → K-SIGNAL-SELECT-01 overlap 선별 survey 설계 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
