# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `368598c` · WORK=`IDLE`
- 지금: **양산前** · ①~④완료 · knobs markov0.55/review0.85/statHINT52
- 직전: K-BRAIN-JOINT-SMOKE **SMOKE_OK** · drift0 · 서버7021재가동
- BOOT다음: **형 지시 대기** — 1237양산 아님 · 추가축/정지 선택
- NEXT1: K-TUNE-CYCLE-HOLD — **양산前 완료분 고정**. 뇌별 단독①markov BLEND0.55 HOLD · ②review BLEND**0.85** · ③stat HINT**52** · ④합동 smoke **SMOKE_OK**(prefer+0.244/prize−0.074/hit0.319 · drift0). **1237 예측/양산 아님**. 형 다음 지시(추가 축·정지·UI확인 등) 대기. ge3 성적클레임 금지. 공유=`lotto_draws`만. (승인=형 다음 지시)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
