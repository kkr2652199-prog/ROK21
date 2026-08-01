# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `000846b` · WORK=`IDLE`
- 지금: **K-SIGNAL-SELECT-FULL 완료** — n=1182 · combined ge3=0.1218 · **FAIL** · wire HOLD
- 직전: K-EXCLUDE-HIST-01 · LEAKAGE_POLICY · TESTLOTTO pool/repack UI
- BOOT다음: K-EXCLUDE-SURVEY — 배제 ON/OFF · **전체 큐=`TEST_PRIORITY.md`**
- NEXT1: K-EXCLUDE-SURVEY — combined + 배제 ON/OFF · λ sweep · as_of WF · wire는 형 GO 전 금지 (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
