# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `9c53b52` · WORK=`IDLE`
- 지금: **양산前** · BT100정밀감사 **NO_HARD_BUG** · tune_json패치
- 직전: 4등5·5등51 재집계 · pool>repack · knobs드리프트
- BOOT다음: **형 지시** — 강제BT재실행 / 몰아주기개선 / K-J / 1237아님
- NEXT1: K-BT100-FOLLOW-HOLD — **양산前**. BT100정밀감사 **NO_HARD_BUG**(4등5·5등51·뇌별repack확인·peekOK). **tune_json PATCHED**. 잔여고우선=강제100회재실행(cand_B·W0.9) / 몰아주기손실(pool>repack) / K-J SSOT. **1237아님**. 형 다음 지시 1건. (승인=형 다음 지시)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
