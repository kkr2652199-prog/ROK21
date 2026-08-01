# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `7ca8c93` · WORK=`IDLE`
- 지금: **K-NEW-ENGINE-STAT-A1** — stat solo baseline ge3=**0.1350** · v2=**0.1350** · delta=0 · **PASS** · ENGINE_V2=False 유지
- 직전: K-BRAIN-TUNE-SURVEY — P0 aux_hint_top5=0.1091 · best_combo ge3=0.1032 · **HOLD**
- BOOT다음: **K-NEW-ENGINE-MARKOV-A1** — markov engine 개선 · **형 GO 대기**
- NEXT1: K-NEW-ENGINE-MARKOV-A1 — markov_brain engine 개선 (STAT-A1 패턴) · build_weights 변경 · bench A/B · 형 GO 시 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
