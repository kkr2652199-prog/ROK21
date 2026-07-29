# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `512d318` · WORK=`IDLE`
- 지금: STAT-TUNE **PASS** · best ge3=**0.1523** · Δ+0.0076 · **WIRE승인대기**
- 직전: HOLD맵 · 실레버공백 · V2유지
- BOOT다음: K-STAT-TUNE-WIRE — 형 GO 시 0.02/20/10 배선 · 승인전금지
- NEXT1: K-STAT-TUNE-WIRE — STAT-TUNE PASS(best ge3=0.1523·Δ+0.0076·p=3.6e-05) · 형 승인 후 predict_statistical 리터럴(0.02/gap20/hot10·pairs30/cap0.5) 배선·verify · 승인 전 코드수정금지 (승인=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
