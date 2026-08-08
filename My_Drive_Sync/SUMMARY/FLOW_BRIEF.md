# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `0789266` · WORK=`IDLE`
- 지금: **K-BRAIN-RNG-INDEPENDENT + K-PREDICT-RESET**(형GO) — **WIRE_CONFORMS 9/9**(1216~1235 · 리셋 후 재검증). ④`expand_pool` 이 3뇌를 **한 난수 흐름**으로 돌려 stat 이 markov 를 오염(발권경로는 이미 뇌별 시드리셋인데 pool 경로만 누락) → **뇌마다 `random.seed` 리셋** ⑤pass0 시드를 `seed+draw_no` 로 맞춰 **pool 1~5 = 실제 발권 5세트**(C8 신설) · 뇌별 상수 dict 개방(`POOL_SLOTS/SCORE_WEIGHTS/LEARN_EMA_BY_BRAIN` · **값 전부 동일=성적 무변화**) · **미해결 명시: hint 는 3뇌 공유**(`W_HINT=0.40` · 뇌별 hint 는 성적 주장이라 범위 밖) · DB 3뇌 예측 **7,094행 삭제**(원천 보존 · rare_hits·transition_log 는 회차파생이라 보존)
- 직전: K-REPACK-SIGNAL-WIRE(성적표 뇌별분리·4·5고정제거·3뇌동일 · 7/7) · K-REPACK-SELECT-DIAG(POOL_EQUALS_RANDOM)
- BOOT다음: **선생님 차례** — ①과거학습 뇌(stat) 예측 튜닝 ②뇌별 hint 분리 ③1236+ 자동시스템 배선 중 **형 1건 선택** · 발권가중 금지
- NEXT1: K-BRAIN-INDEPENDENT-NEXT-PICK — 형 지시 3건 **완료** — ⑴ **나머지 2뇌 독립**: 「3뇌 동일 배선」은 앞 턴에 됐지만 **독립은 아니었다**. `expand_pool` 이 `_live_candidates` 로 3뇌를 **한 난수 흐름에서 순차 호출**해 앞 뇌의 뽑기 소비량이 뒤 뇌 결과를 바꿨다(stat→markov 오염). 발권경로 `coordinator._seed_independent_brain` 은 이미 뇌별 시드리셋인데 **pool 경로만 누락**이었다 → `expand_pool` 이 `BRAIN_TAGS` 를 직접 돌며 뇌마다 시드 리셋. 덤으로 pass0 시드를 발권 규칙(`42+draw_no`)과 맞춰 **pool 1~5 = 실제 발권 5세트** 확보(C8 신설 · 분석과 발권이 어긋나던 것도 해소). 뇌별 상수 dict(`POOL_SLOTS_BY_BRAIN`·`SCORE_WEIGHTS_BY_BRAIN`·`LEARN_EMA_BY_BRAIN`) 개방했으나 **값은 3뇌 동일 = 성적 무변화**(차별화는 게이트 통과 후) · 검증 **9/9**(1216~1235 · 리셋 후 재실행) · ⑵ **DB 리셋**: 테스트로또 DB 3뇌 예측 **7,094행 삭제** · 원천데이터 보존 · `rare_bundle_hits`·`transition_log` 는 회차 파생이라 3뇌 예측 아님 → 보존 · ⑶ **미해결 1건 명시**: `HINT_SHARED_ACROSS_BRAINS=True` — `_build_hint` 하나를 3뇌에 그대로 넘기고 `W_HINT=0.40` 이라 **점수의 40%가 3뇌 동일**. 완전 독립이 아니다. 형 확인 후 1건 선택 — **①과거학습 뇌(stat) 예측 튜닝**(권장 · 형이 말한 「과거 회차 분석해 번호 예측하는 뇌 튜닝」 · 통로가 뚫렸으니 이제 개선이 몰아주기까지 전달됨 · 튜닝 지점 후보는 아래 메모) / ②뇌별 hint 분리(남은 마지막 공유축 · 단 어느 hint 가 어느 뇌에 맞는지는 데이터로 정해야 하므로 게이트 필요) / ③1236+ 회차별 자동시스템 배선(형이 「이후 패치」로 미뤄둔 건) / ④트랙정지 (승인=없음 (발권경로 `coordinator` 무변경 · 동결항목 무접촉 · DB 는 커밋 안 함))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
