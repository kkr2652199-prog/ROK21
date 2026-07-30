# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `3f80951` · WORK=`IDLE`
- 지금: **보고서 한국어 규칙** · REPACK **3등 1회** 긍정 반영 · SELECT-FULL 대기
- 직전: K-SIGNAL-REPACK-01 DONE · top5 ge3=0.085 · 5장 공정 FAIL
- BOOT다음: K-SIGNAL-SELECT-FULL — full 1182 · **전체 큐=`TEST_PRIORITY.md`**
- NEXT1: K-SIGNAL-SELECT-FULL — QUICK PASS(combined ge3=0.145) → full n=1182 walk-forward 재실행 · pin+p<0.05 확인 · wire는 형 GO 전 금지 (승인=full 실행=아니(QUICK PASS 후 자동) · wire=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
