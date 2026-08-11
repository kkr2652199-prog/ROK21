# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `4b69c9c` · WORK=`IDLE`
- 지금: **양산前** · 다음리스트 DOC_OK · 종료체크 20260812보고서 보충
- 직전: pool품질 · oversample markov**5** APPLY · jaccard HOLD
- BOOT다음: **형 지시** 1건(합동smoke/pool잔여/BT/learn/K-G) / 1237아님
- NEXT1: K-NEXT-LIST-HOLD — **양산前**. 다음리스트 DOC_OK(`20260812_KNEXT_LIST_BRIEF`). 후보=합동smoke/pool잔여/강제BT/learn재누적/K-G. 형 번호1건. **1237아님**. (승인=형 다음 지시)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
