# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `392320f` · WORK=`IDLE`
- 지금: **K-STAT-NOISE-SOURCE**(n400·seed24) — 잡음 유입점 **'뽑기' 단계로 확정**(점수·repack 결정적) · 그러나 **PREMISE_NOT_ESTABLISHED**: 뇌별 팽창차(stat1.2739/markov0.7329)가 seed10 오차 안(구분가능쌍 **0/3**) · 뇌수준 std 도 stat0.016040/markov0.015184/review0.013584 **동일** → stat 전용 대책 근거 없음
- 직전: K-STAT-SEED-NOISE-FLOOR(바닥 b=0.010127 · FULL-WF Δ+0.0047 < 바닥 → 적중축 판정불가 확정) · R38 게이트 가동(k_gate · COMPLIANT)
- BOOT다음: ①잡음바닥 seed16+ 재측정(권장 · 바닥 자체 오차 미상) ②1236+ 전향적 EV로그 ③seed 평균화 설계(형 GO 필요) 중 **형 1건 선택** · 발권가중 금지
- NEXT1: K-NOISE-SOURCE-NEXT-PICK — stat 잡음 원인 진단 완료 — **결론: 질문의 전제가 무너짐(PREMISE_NOT_ESTABLISHED)**. 뇌별 팽창차(stat 1.2739 / markov 0.7329)는 seed10 측정오차 안이라 구분가능쌍 **0/3**. 잡음 유입점은 **'뽑기' 단계로 확정**(점수·repack 모두 결정적). 형 확인 후 1건 선택 — **①잡음바닥 seed 16+ 재측정**(권장 · 현 바닥 b=0.010127 이 seed10 기반이라 바닥 자체의 오차가 미상 · 이 값이 앞으로 모든 판정 임계를 정함 · stat↔markov 구분에 seed 16이면 충분) / ②회차 1236+ 전향적 EV 로그 시작 / ③seed 평균화 설계(같은 회차 반복 뽑기→번호 득표 · random.choices 무수정 · 발권경로 변경이라 형 GO 필요) / ④트랙정지 (승인=없음 (①②는 측정·기록만 · 발권경로 무변경) / ③은 형 GO 필수)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
