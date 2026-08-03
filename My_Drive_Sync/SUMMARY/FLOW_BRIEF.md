# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `fa9c2aa` · WORK=`IDLE`
- 지금: **K-BT-PRECISION-BENCH** — BT200/WIRE 정밀분석 · 외부문헌 대조 · canvas · **DONE**
- 직전: K-DB-RESET-BT200 · tail-200 WF · pool 201
- BOOT다음: eval_mode null 병기·pin갭 등 **형 GO 대기**
- NEXT1: K-BT-PRECISION-BENCH-DONE — 정밀분석 보고·canvas 완료 · P0(eval_mode null병기)/pin갭 등 **형 GO 대기** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
