# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `a4b243f` · WORK=`RUNNING:K-POOL-RESIDUAL-TUNE`
- 지금: **양산前** · ①합동smoke **SMOKE_OK** · 다음② pool잔여
- 직전: 다음리스트 DOC_OK · 20260812보고서 보충
- BOOT다음: ② review/stat pool잔여 / 1237아님
- NEXT1: K-POOL-RESIDUAL-TUNE — **양산前**. ①합동smoke **SMOKE_OK** 완료. 단계②=review/stat pool잔여(몫축·hit) 튜닝 1노브. **1237아님**. (승인=없음(형 순서진행))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
