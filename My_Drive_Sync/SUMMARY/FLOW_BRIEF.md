# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `48c2505` · WORK=`IDLE`
- 지금: **K-WINDOW-SIGNAL-01 FAIL** — best w4_zone_mix@α=0.1 ge3=0.1328 p=0.023 · pin 미달
- 직전: K-AUX-SIGNAL-01 FAIL · E2 POSTMORTEM-SIGNAL-02 bin lift 미약
- BOOT다음: K-ATTACK-HOLD — V2 pin 유지 · E3 PATTERN-HINT-03은 형 GO
- NEXT1: K-ATTACK-HOLD — V2 pin ge3=0.1447 유지 · E3 PATTERN-HINT-03 survey는 형 GO 후 · coordinator/AUX/window hint 배선 금지 (승인=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
