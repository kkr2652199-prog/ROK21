# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `dcc20b3` · WORK=`IDLE`
- 지금: **K-FUSION-INNOVATION** — conf bucket+AUX reweight ge3=**0.0900** · gate FAIL · **INNOVATION 롤백** · V2 live
- 직전: K-FUSION-DYNAMIC-V2 · solo×ref ge3=0.09 tie · SOLO_GE3_PRIORS live
- BOOT다음: 0.09+ 추가 경로 · **형 GO 대기**
- NEXT1: K-FUSION-INNOVATION-DONE — conf bucket+AUX reweight ge3=**0.0900** · vs V2 **+0.0000** · gate FAIL · **INNOVATION 롤백 완료** · V2 live · 0.09+ 경로 · **형 GO 대기** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
