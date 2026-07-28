# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `0f201f7` · WORK=`IDLE`
- 지금: K-PROB-VECTOR — 유효신호 0 · **HOLD 복귀**
- 직전: OPEN A/B/C FAIL · HOLD→PROB-VECTOR 교체 실행
- BOOT다음: K-ATTACK-HOLD — 형·동생 새 축 재선정
- NEXT1: K-ATTACK-HOLD — K-PROB-VECTOR 유효신호 0 · STRENGTHEN 미등록 · 형·동생 다음 공격 축 1건 재선정 (승인=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
