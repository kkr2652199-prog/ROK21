# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `05453be` · WORK=`IDLE`
- 지금: **양산前** · L3 원장WIRE **WIRE_OK** · NEXT=L4 몰아주기원장읽기
- 직전: L2b 역할SPEC DOC_OK
- BOOT다음: L4 K-REPACK-READ-LEDGER / 1237아님
- NEXT1: K-REPACK-READ-LEDGER — **양산前**. L3 원장 **WIRE_OK**(ledger+scatter CREATE·피드백경로쓰기·1236 45행·no_peek). 다음=**L4** 몰아주기(`focus_r1`)가 원장 SSOT **읽기**(draw_no<target · EMA단독탈피). **1237아님** · 역할슬롯 코드는 L4b · 강제BT보류. (승인=없음(리스트 순서))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
