# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `e3aa05c` · WORK=`IDLE`
- 지금: **양산前** · S2 shape코어 HOLD · NEXT=S3 몰아주기쿼터
- 직전: Jaccard 0.71→0.29 나왔으나 prefer+0.012 인기↑
- BOOT다음: S3 K-STAT-REPACK-ROLE-QUOTA / 1237아님
- NEXT1: K-STAT-REPACK-ROLE-QUOTA — **양산前**. S2 HOLD(set1). **stat 몰아주기** cap4 복사에 cover최소1·shape최대1·skill최소1. 게이트 prefer/prize 비악화. 모니터 copy_by_role. **1237아님**. (승인=없음(형 캠페인GO · stat엔진+몰아주기))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
