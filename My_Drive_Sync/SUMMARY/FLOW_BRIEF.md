# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `0cc870d` · WORK=`IDLE`
- 지금: **양산前** · 강제100회 pool백테 **REBUILT** · UI backtest 적재
- 직전: 리셋+1137~1236 WF · pool300/bt100 · nopeek · 패치knobs
- BOOT다음: **형 지시 대기** — UI확인 / 추가튜닝 / 정지 / 1237아님
- NEXT1: K-FORCE-POOL-BT-HOLD — **양산前**. 강제 리셋+1137~1236 n100 pool백테 **REBUILT_OK**(pool캐시300·bt_results100·API draw-index100). knobs=markov0.55/review0.85/statHINT52 · `_get_draws_before` nopeek. ge3는 모니터만. **1237 양산아님**. 브라우저 Ctrl+F5 후 테스트로또·백테패널/`testlotto-detail.html?draw=1236` 확인. 형 다음 지시 대기. (승인=형 다음 지시)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
