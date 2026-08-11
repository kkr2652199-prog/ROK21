# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `490312e` · WORK=`IDLE`
- 지금: **양산前** · 강제BTv2·repack손실조사·K-J PATCHED
- 직전: 순서①②③ 완료 · 4등6·5등48 · pool_best탈락
- BOOT다음: **형 지시** — 몰아주기 P1/P2게이트 승인여부 / 1237아님
- NEXT1: K-SEQ-DONE-HOLD — **양산前**. 순서①강제BTv2(cand_B·4등6·5등48·NO_HARD_BUG) · ②repack손실=POOL_BEST_DROPPED(stat45/mk41/rv39·slots2) PROPOSE_HOLD · ③K-J SSOT=live PATCHED. 다음=형 지시1건(P1/P2게이트승인 또는 다른튜닝). **1237아님**. (승인=형 다음 지시)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
