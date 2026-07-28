# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `7227b96` · WORK=`IDLE`
- 지금: K-MARKOV-WIRE-V2 PASS · set_no=E · **ENABLED=True**
- 직전: WIRE-V1 FAIL (conf쿼터)
- BOOT다음: K-MARKOV-TUNE — markov 세부 파라미터/쿼터 미세조정
- NEXT1: K-MARKOV-TUNE — WIRE-V2 PASS(set_no ge3=0.1447 p=0.0007) · markov 세부 파라미터/쿼터 미세조정 여부 (승인=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
