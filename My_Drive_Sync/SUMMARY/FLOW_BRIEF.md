# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `c54068a` · WORK=`IDLE`
- 지금: K-SETCOUNT-SURVEY PASS · n15 ge3=0.3088 · **WIRE후보**
- 직전: COVER FAIL (ge3≤RR)
- BOOT다음: K-SETCOUNT-WIRE — null/비용 검증 후 SETS 확장 여부
- NEXT1: K-SETCOUNT-WIRE — SETCOUNT PASS(n=10·15 ge3>RR) · 배선 전 null/비용 대비 검증 후 SETS 확장 여부 결정 (승인=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
