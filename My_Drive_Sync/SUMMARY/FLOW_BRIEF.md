# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `01abac1` · WORK=`IDLE`
- 지금: **K-1236-FEEDBACK-VERIFY** — 1236 실전 **VERIFY_OK** · 다음=K-N-MEAN-INPUT-FIX
- 직전: K-KK-FEEDBACK-WIRE · PATCHED
- BOOT다음: **형 GO** — ①K-N mean입력 정합 ②K-M referee ③정지
- NEXT1: K-N-MEAN-INPUT-FIX — **1236 피드백 실전 VERIFY_OK 후**. K-N HOLD 해소 — 학습입력을 best 오인→mean/볼지표로 정합. (선행=K-KK PATCHED·1236 VERIFY_OK · K-M은 K-N 후) (승인=형 GO)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
