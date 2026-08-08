# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `a142b77` · WORK=`IDLE`
- 지금: **K-BRAIN-INDEPENDENT-TUNE** — SCORE_WEIGHTS 뇌별 **APPLY** · prefer↑/prize더음수/stat hit↑ · ge3미사용
- 직전: K-BRAIN-INDEPENDENT-WIRE · WIRE_CONFORMS
- BOOT다음: **형 선택** — ①군중 BLEND 소튜닝(review EV) ②과거학습 명분리뷰 ③정지
- NEXT1: K-BRAIN-INDEPENDENT-TUNE-DONE — **SCORE_WEIGHTS 뇌별 APPLY 완료**. cand_A(stat 0.25/0.35/0.40 · markov·review 0.55/0.20/0.25). 축지표 1100~1235: prefer+0.023 · prize−0.027 · stat hit+0.005 · review 3구간 consistent. 형 1건 — **①군중 BLEND_STRENGTH 소튜닝**(review EV 강화 후보) / ②1235 과거학습 명분리뷰 / ③정지 (승인=없음 (다음 선택만))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
