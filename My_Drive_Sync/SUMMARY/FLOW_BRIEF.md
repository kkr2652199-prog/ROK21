# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `ba21125` · WORK=`IDLE`
- 지금: **K-HIGHWAY-FEEDBACK** — `_auto_feedback` · 3뇌 apply_feedback · import OK · **OK**
- 직전: K-NEW-ENGINE-STAT-A1 — stat solo ge3=0.1350 · v2=0.1350 · **PASS** · ENGINE_V2=False
- BOOT다음: **K-HIGHWAY-REFEREE** — referee 가중 · **형 GO 대기**
- NEXT1: K-HIGHWAY-REFEREE — coordinator referee 가중 자동 갱신 · **형 GO 대기** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
