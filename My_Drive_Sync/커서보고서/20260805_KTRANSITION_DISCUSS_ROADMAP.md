# K-TRANSITION 논의 로드맵 — **CURSOR 갱신** (2026-08-05)

> 작성/갱신: **Cursor** · 상세 브리핑: `reports/20260805_KTRANSITION_DIRECTION_BRIEF_CURSOR.md`

## 형 요청 흐름

1. 1234 기준 유사(2+) → 다음 회차 빈도 + carry
2. 1235 대조 · 단건은 sanity
3. 전 회차 rolling = `K-TRANSITION-FULL` ✅
4. **최종:** 전 회차 저장 → 미래 자동 적용 (stat 재설계는 **나중**)

## 현재 단계 (Cursor 정정 2026-08-05)

| 단계 | 상태 | 산출물 |
|------|------|--------|
| 1234→1235 ad-hoc | ✅ | 팩트체크 |
| rolling 101~1235 | ✅ STRONG | `20260805_KTRANSITION_FULL.json` |
| 팩트체크·표본 | ✅ | FACTCHECK · RANDOM_SAMPLE |
| **방향성 브리핑** | ✅ | `DIRECTION_BRIEF_CURSOR` (**Cursor**) |
| **패턴 수집 설계** | ⏳ | **형 GO** ← 지금 |
| 수집 데이터 재검증 | ⏳ | 수집 후 |
| stat 뇌 재설계 | ⏳ | 재검증·형 GO 후 |
| engine wire / 발권 | 🚫 | 확실 전 금지 |

## 핵심 판단 (수치 SSOT)

- rolling sim_k2: mean_hit **2.172** · Δ **+0.172** · **STRONG** (=미세 신호)
- brain_replace: **보류(수집 후)** — 구 「즉시착수」문구 철회
- markov 80% / review 20% / stat 0% 유지

## 금지

`random.choices` · `engine.py` 직접 수정 · auto-tune · wire · 발권경로 DB쓰기
