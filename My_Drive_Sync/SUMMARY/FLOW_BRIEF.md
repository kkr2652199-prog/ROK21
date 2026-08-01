# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `44b3f53` · WORK=`IDLE`
- 지금: **K-WIRE-SELECT-FULL-SURVEY** — conf_global_top5 FULL ge3=0.1117(QUICK 0.135 collapse) · set_no_asc=0.1015 · wire GO=**wait/HOLD**
- 직전: K-QUOTA-GAP-SURVEY — conf_global_top5 QUICK ge3=0.135 · aux_hint=0.130 · quota_gap=43.0%
- BOOT다음: **K-WIRE-SELECT-GO-WAIT** — FULL FAIL·collapse · wire HOLD 권고 · 형 GO 시에만 A/B (coordinator 미패치)
- NEXT1: K-WIRE-SELECT-GO-WAIT — FULL FAIL·collapse(0.135→0.1117) — wire **HOLD 권고** · 형 명시 GO 시 conf_global_top5 wire A/B · coordinator 미패치 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
