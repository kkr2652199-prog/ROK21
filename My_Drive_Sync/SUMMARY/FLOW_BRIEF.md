# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `7e6d119` · WORK=`IDLE`
- 지금: **K-HIGHWAY-PHASE1 COMPLETE** — FEEDBACK+REFEREE+QUOTA · dynamic_brain_quota · **OK**
- 직전: K-HIGHWAY-REFEREE — aux_referee score_set · **OK**
- BOOT다음: **형 GO 대기** — K-NEW-ENGINE-MARKOV-A1 등 별도 트랙
- NEXT1: K-HIGHWAY-PHASE1-HOLD — PHASE1 COMPLETE · FEEDBACK+REFEREE+QUOTA 완료 · 다음 트랙 **형 GO 대기** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
