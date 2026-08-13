# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `505c46d` · WORK=`IDLE`
- 지금: **양산前** · L12 발권↔pool SPEC **DOC_OK** · NEXT=L12b 형A~E
- 직전: L12 K-TICKET-POOL-UNIFY-SPEC DOC_OK (강제병합안함·권고E)
- BOOT다음: L12b WIRE / 형 A~E 선택 / 1237아님
- NEXT1: K-TICKET-POOL-UNIFY-WIRE — **양산前**. L12 SPEC **DOC_OK**(강제병합안함·C8 PASS·권고E). 다음=**L12b** 형 옵션 **A~E** 선택 후 WIRE. A=분리유지 · B=pool10발권 · C=repack15발권 · D=10+5전부 · **E권고**=생성1회+pool캐시동기. **1237아님** · 강제BT보류. (승인=**형 A~E**)
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
