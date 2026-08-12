# K-EMA-OR-LEDGER-SSOT — LIST_V3 L9d

판정: **DOC_OK** · wire 변경 없음 · 양산前 · 1237아님

## 결정 (본턴 고정)

| 신호 | SSOT | 영속 | 비고 |
|------|------|------|------|
| 몰아주기(repack/`focus_r1`) 적중 기여 | **`testlotto_pool_hit_ledger` (+scatter)** | ✅ DB | `LEDGER_SIGNAL_WIRE=True` · blend β=0.5 |
| 프로세스 내 EMA warm | `RollingSignalLearner` | ❌ 메모리 | ledger 없을 때·blend 잔여용 · **별도 EMA 테이블 만들지 않음**(현 단계) |
| 뇌 스킬 hint | **`testlotto_skill_homework`** (L9c) + 재계산 fallback | ✅ | miss/prefer/prize |
| CUTOFF learn | **`testlotto_brain_review`** (L9b 미러 포함) | ✅ | |

## 금지

- EMA를 ledger와 **동등 SSOT**로 문서/코드에 병기하지 말 것.
- ge3/등수P를 EMA·ledger 성적으로 클레임 금지.
- EMA persist 테이블 신설은 **형 승인 후** (필요 증거: ledger만으로 게이트 실패 시).

## 다음

**L10** K-TICKET-COVER-LITE (발권5 커버라이트).
