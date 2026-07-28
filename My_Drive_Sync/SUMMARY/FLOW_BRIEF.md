# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `6ee6ee8` · WORK=`IDLE`
- 지금: GENDIV FAIL · corr/Q1 false · **HOLD** · V2유지
- 직전: SUM FAIL / BAND FAIL / EV-POP FAIL / SETNO FAIL / SETPACK FAIL / TUNE FAIL / WIRE-V2 PASS
- BOOT다음: K-ATTACK-HOLD — GENDIV재탕금지 · 슬롯재선택지양 · 다음 직교축
- NEXT1: K-ATTACK-HOLD — GENDIV FAIL(corr|r|<0.03 · Q1 ge3 0.1224·Δ-0.0223 · Q1−Q5=-0.0344) · WIRE금지 · V2유지 · GENDIV재탕금지 · 슬롯재선택계열지양 · 형·커서 다음 직교축 1건 재선정 (승인=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
