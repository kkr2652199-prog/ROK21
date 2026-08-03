# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `bc34585` · WORK=`IDLE`
- 지금: **K-UI-BT-PRELOAD** — 200회 draw-index 프리로드·즉시적용 · JS `20260803b` · **live**
- 직전: K-UI-BT-INSTANT · GET 자동WF 제거
- BOOT다음: 다음축(pin갭 등) · **형 GO 대기**
- NEXT1: K-UI-BT-PRELOAD-DONE — 200회 백테 draw-index 프리로드·즉시적용 live · Ctrl+F5 후 확인 · 다음축 **형 GO 대기** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
