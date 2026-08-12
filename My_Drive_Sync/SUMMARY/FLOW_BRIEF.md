# FLOW_BRIEF — 외부AI 매턴 흐름 요약 (자동 · R37)

- HEAD: `3a83dbf` · WORK=`IDLE`
- 지금: **양산前** · L5 뇌10스킬감사 **AUDIT_OK** · NEXT=L9 몰아주기보존
- 직전: L4b 역할슬롯WIRE WIRE_OK
- BOOT다음: L9 K-REPACK-PRESERVE-PROBE / 1237아님
- NEXT1: K-REPACK-PRESERVE-PROBE — **양산前**. L5 뇌10스킬감사 **AUDIT_OK**(하드PASS·소프트결함0·L6~L8스킵). 다음=**L9** 몰아주기 보존 **PROBE**(union/slots 소형·신호없으면 HOLD). **1237아님** · 강제BT보류 · S1 개별승인. (승인=없음(리스트 순서 · L6~L8 결함없음으로 점프))
- OPEN샘플: K-00, K-02, K-05
- SSOT: 수치=docs/benchmarks/*.json · 결함=FINDINGS · 라벨=WARRANT
- 금지: 동결토큰·kweon미접촉·컨닝·DB전체초기화·1~3군기록·채팅간략≠문서압축
- 진입: **EXTERNAL_START.md** (레포 루트) → 없으면 이 FLOW_BRIEF
- 젠스파크압축: **GENSPARK_COMPRESS_RECOVER.md** (채팅기억 불신·JSON 재페치)
- 주의: HEAD는 생성 시점 git. push 직후 1커밋 지연 가능.
