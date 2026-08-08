# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `11a6890` · WORK=`IDLE`
- 지금: **K-STAT-PASTLEARN-READY-CHECK**(READ-ONLY) — 과거학습 뇌가 「회차 숙제」 길로 패치 준비됐는지 점검. **방향·컨닝차단·파이프는 준비됨** · **학습/명분 DB는 리셋으로 비어 튜닝 직전 아님**. 실측: _get_draws_before(1235)→last1234 · cutoff 없으면 learn 로드 차단 · wire ON·v2 ON·ASSOC OFF · reasoning 태그 있음(1yHot) · learn_state/predictions/hit_warrant/evolve=0
- 직전: K-BRAIN-INDEPENDENCE-AUDIT 14/14 · RNG독립·예측DB리셋
- BOOT다음: **형 GO** — ①회차 숙제 백테스트로 기록 채우기(권장·튜닝 전 필수) ②한 회차 명분 샘플 리뷰 ③재료 튜닝(게이트) 중 1건
- NEXT1: K-STAT-HOMEWORK-FILL-PICK — **K-STAT-PASTLEARN-READY-CHECK 완료** — 형 질문 「확정 길(회차 숙제)로 패치 준비된 뇌인가?」에 대한 실측 답. **방향·컨닝차단·파이프는 준비됨 / 학습·명분 DB는 비어 튜닝 직전 아님.** 실측: `_get_draws_before(1235)`→last=1234 · `set_learn_as_of` 없으면 learn 로드 차단 · `PAST_LEARN_WIRE=ON`·`ENGINE_V2=ON`(past_learn경유)·ASSOC OFF · reasoning에 `1yHot` 태그 존재 · `learn_state/predictions/hit_warrant/evolve_log=0`. **확정 길 잠금**: 예측=N 숙제 · 재료=1..(N-1) · 채점=N 정답 · 깊은 패턴은 재료일 뿐 본선 아님. 형 1건 선택 — **①회차 숙제 백테스트로 기록 채우기**(권장 · 빈 DB로 decay/하드코딩 튜닝 금지) / ②한 회차(예 1235) 명분 샘플을 형이 읽고 부족한 점 지적 / ③재료 튜닝(게이트·성적주장) / ④트랙정지 (승인=없음 (READ-ONLY 점검 · 발권/동결 무접촉))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
