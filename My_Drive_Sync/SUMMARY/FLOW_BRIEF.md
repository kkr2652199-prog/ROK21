# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `4becae8` · WORK=`IDLE`
- 지금: **K-BENCH-NULL-BY-EVAL** — eval_mode별 null 병기 · enrich_metrics · TAIL100 정정 · **live**
- 직전: K-BT-PRECISION-BENCH 정밀분석
- BOOT다음: pin갭(FULL0.1184→0.1447) **형 GO 대기**
- NEXT1: K-BENCH-NULL-BY-EVAL-DONE — eval_mode null 병기 live · signal_repack FAIL(vs 0.3036) · pin갭 다음축 **형 GO 대기** (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
