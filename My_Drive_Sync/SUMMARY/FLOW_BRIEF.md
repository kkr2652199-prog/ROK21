# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `0b39eee` · WORK=`RUNNING:K-TL-DASH-BACKFILL-1236`
- 지금: **양산前** · 테스트대시보드 백필 RUNNING
- 직전: 4군/전략X탭 HOLD_ON
- BOOT다음: 백필완료 확인 / 1237아님
- NEXT1: K-TL-DASH-BACKFILL-1236 — **양산前**. 테스트 대시보드 탭 ON. 예측초기화 후 1–1236 3뇌 백필 RUNNING. 완료 후 대시보드 숫자 확인. 1237 금지. (승인=없음(형 지시 실행 중))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
