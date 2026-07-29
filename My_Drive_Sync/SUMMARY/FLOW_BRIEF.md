# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `64fbbd2` · WORK=`IDLE`
- 지금: AUX-WEIGHT-SURVEY **FAIL** · 13조합 ge3=**0.1100** 동일 · pin불일치
- 직전: STAT-WIRE FAIL · 롤백완료
- BOOT다음: K-ATTACK-HOLD — AUX_WEIGHTS 실레버 아님 · 다음 공격축 형 결정 대기
- NEXT1: K-ATTACK-HOLD — AUX-WEIGHT-SURVEY FAIL(13조합 ge3=0.1100 동일·Δ-0.0347·p=0.669622) · V2 set_no 경로 AUX_WEIGHTS 실레버 아님 · 다음 공격축 형 결정 대기 (승인=예)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
