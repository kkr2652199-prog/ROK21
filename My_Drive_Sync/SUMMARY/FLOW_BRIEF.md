# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `9582ac7` · WORK=`IDLE`
- 지금: **K-BRAIN-INDEPENDENT-WIRE** — hint 3뇌 분리 **5/5** · EV프록시 **MARGINAL**(consistent) · **WIRE_CONFORMS**
- 직전: K-BRAIN-CROWD-RESTRUCTURE · WIRE_SMOKE_OK
- BOOT다음: hint 분리 PASS → **형 GO 후 뇌별 독립 튜닝** (FAIL였으면 롤백 `K_CROWD_PREFER=0`)
- NEXT1: K-BRAIN-INDEPENDENT-WIRE-DONE — hint 분리 결과 + EV프록시 게이트 형 확인. **WIRE_CONFORMS 5/5** · EV=`MARGINAL`(delta−0.0927 · 3구간 consistent). 형 GO → 각 뇌 독립 튜닝 단계로 / PARTIAL·FAIL이었으면 추가 버그 수정 후 재검증(이번 턴은 CONFORMS) (승인=형 GO (다음 튜닝 착수))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
