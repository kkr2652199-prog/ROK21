# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `b5ab7a2` · WORK=`IDLE`
- 지금: 핀①~④ 완료 — SCATTER 기회大 · gather v0 회수0 → **V1 튜닝**
- 직전: 형 핀 GO · POS sticky≈null
- BOOT다음: K-GATHER-V1 — oracle 분해 후 휴리스틱 교체 (WIRE 보류)
- NEXT1: K-GATHER-V1 — union6 회차 oracle 분해 → 몰아주기 휴리스틱 교체 → PILOT 재실행 JSON (WIRE 전 성적 게이트) (승인=아니오 · **K-GATHER-WIRE만 형 GO**)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
