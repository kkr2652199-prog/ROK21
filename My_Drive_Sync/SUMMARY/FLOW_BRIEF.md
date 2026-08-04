# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `dffbc5b` · WORK=`IDLE`
- 지금: **K-QUOTA-D-WIRE** — 실적용 검증 · **FAIL·롤백**
- 직전: K-PATCH-1235-PREP
- BOOT다음: 형 확인 · live경로 재측정 여부
- NEXT1: K-QUOTA-D-WIRE-DONE — quota D wire **FAIL·롤백완료** · 검증 결과 확인 · **형 GO**(다음: live경로 재측정 또는 다른 후보) (승인=미확인)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
