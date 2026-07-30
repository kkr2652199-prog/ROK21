# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `3661cdd` · WORK=`IDLE`
- 지금: **tail-100 백테스트** — repack ge3=0.23(23/100) · combined ge3=0.15(15/100) · run_id 3·4 · UI 「3뇌 예측」 단일
- 직전: TESTLOTTO click-predict DONE · cache-only · tier-match fix
- BOOT다음: K-SIGNAL-SELECT-FULL — full 1182 walk-forward · **전체 큐=`TEST_PRIORITY.md`**
- NEXT1: K-SIGNAL-SELECT-FULL — **tail-100 BACKTEST DONE(20260730f)** — repack ge3=0.23 · combined ge3=0.15 · run_id 3·4 · full n=1182 walk-forward 재실행 · pin+p<0.05 확인 · wire는 형 GO 전 금지 (승인=full 실행=아니(QUICK PASS 후 자동) · wire=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
