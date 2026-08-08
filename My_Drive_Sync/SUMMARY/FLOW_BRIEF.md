# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `23177cb` · WORK=`IDLE`
- 지금: **K-STAT-HOMEWORK-FILL**(형GO ①) — 회차 숙제 1216~1235 **20/20 OK** · 298초. 발권경로+stat숙제5장 · 채점 · pool/evolve. 후: pred200(stat100) · learn3 · evolve60 · pool60 · warrant20. 명분 샘플 1235 set5 적중3·1yHot/Cold 태그
- 직전: K-STAT-PASTLEARN-READY-CHECK (방향준비·기록미준비)
- BOOT다음: **형 선택** — ①1235 명분 샘플 읽고 부족한 점 지적(권장) ②재료 튜닝(게이트) ③구간 확장(100회+) ④정지
- NEXT1: K-STAT-HOMEWORK-NEXT-PICK — **K-STAT-HOMEWORK-FILL 완료 20/20** (1216~1235). 확정 길로 기록 채움 — 발권 쿼터5장 + **stat 숙제 5장 강제**(쿼터만 쓰면 past학습이 DB에 0장이던 문제 해결) + matched 채점 + pool_view_cache + evolve_log. 후행수: predictions **200**(stat **100**) · learn_state **3** · evolve **60** · pool **60** · hit_warrant **20**. 형 1건 — **①1235 명분 샘플 리뷰**(권장 · 보고서 §3) / ②재료 튜닝 착수(게이트) / ③구간 확장 1136~1235 / ④정지 (승인=없음 (DB 로컬만 · 커밋 안 함))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
