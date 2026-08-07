# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `f5db94d` · WORK=`IDLE`
- 지금: **K-PAST-LEARN-YT-BENCH** — 신뢰YT 벤치 · decay보류권고 · **DOC_SURVEY**
- 직전: K-PAST-LEARN-DETAIL-TUNE · CANDIDATE
- BOOT다음: DETAIL KEEP_BASE 확정 · **형 GO**
- NEXT1: K-PAST-LEARN-DETAIL-KEEP — YT벤치 권고대로 DETAIL decay **KEEP_BASE**(0.005/0.05) 확정 · tipster/LSTM wire 금지 · **형 GO** (승인=필요)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
