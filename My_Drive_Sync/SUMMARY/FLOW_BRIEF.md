# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `bd2c67d` · WORK=`IDLE`
- 지금: **K-QUOTA-GAP-SURVEY** — conf_global_top5 ge3=0.135 · aux_hint_quota=0.130 · quota_gap=43.0% · coordinator 미변경
- 직전: K-BRAIN-PACKAGE-COMPLETE — C package Phase0~7 DONE · set_no_asc ge3=0.125 · consolidated PASS
- BOOT다음: **K-WIRE-SELECT-GO-WAIT** — 형 GO for conf_global_top5 or aux_hint_quota wire A/B (auto-wire 금지)
- NEXT1: K-WIRE-SELECT-GO-WAIT — conf_global_top5(+0.01) 또는 aux_hint_quota(+0.005) wire A/B — 형 GO 전 coordinator 미패치 · FULL n=1182 재검증 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
