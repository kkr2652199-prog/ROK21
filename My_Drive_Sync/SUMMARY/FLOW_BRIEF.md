# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `2f7788f` · WORK=`IDLE`
- 지금: **양산前 테스트** — DB최신=**1236**=마지막회차 가정 · 1237 아직 아님
- 직전: K-M/K-N/K-K PATCHED · 예측리셋·100회복습
- BOOT다음: **형 GO** — 1235↓ 백테로 **뇌별 신호 최고성능 튜닝** (축 지정)
- NEXT1: K-BRAIN-SIGNAL-TUNE — **양산前**. DB 결과 최신=**1236을 마지막 회차**로 본다. **1237 예측/양산 준비 아님**. 1235·1234·그 이전으로 백테·샘플 테스트하며 **3뇌(stat/markov/review) 신호를 최고 성능으로 튜닝**. 형 GO 시 튜닝 축 지정(예: 금액뇌 EV / 선호번호 prefer / 과거학습 패턴). ge3를 성적클레임으로 쓰지 말 것. (승인=형 GO (어느 뇌·어느 축부터))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
