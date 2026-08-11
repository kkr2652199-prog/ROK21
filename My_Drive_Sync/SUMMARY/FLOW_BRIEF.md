# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `4642e25` · WORK=`IDLE`
- 지금: **양산前** · 상세UI **10+5** PATCH · knobs strip · schema4
- 직전: K-UI-DETAIL-POOL10x5 · 1236 pool10/repack5 실측
- BOOT다음: **형 지시 대기** — UI추가개선 / 정지 / 1237아님
- NEXT1: K-TUNE-CYCLE-HOLD — **양산前**. 뇌별 튜닝①~④·합동smoke OK · 상세페이지 **10+5 UI PATCHED**(schema4·knobs strip). **1237 양산아님**. 브라우저: `http://127.0.0.1:7021/static/testlotto-detail.html?draw=1236` 또는 메인→테스트로또→자세히 분석. 형 다음 지시 대기. (승인=형 다음 지시)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
