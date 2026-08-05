# K-TRANSITION 논의 로드맵 — 1234 패턴 → 전회차 → 미래 적용 (2026-08-05)

## 형 요청 흐름 (확정)

1. **1234 회차** 기준 — 과거 유사(2+ 겹침) → 다음 회차 빈도 + carry
2. **1235**와 대조 — “이 패턴으로 다음 회차 힌트”
3. **1233·1234·지금**처럼 회차별 동일 분석 → **전 회차 rolling** = `K-TRANSITION-FULL`
4. **최종 목표:** 전 회차 저장 → 미래 회차 자동 적용 (stat 뇌)

## 현재 단계

| 단계 | 상태 | 산출물 |
|------|------|--------|
| 1234→1235 ad-hoc | ✅ | 채팅 + 팩트체크 |
| rolling 101~1235 | ✅ STRONG | `20260805_KTRANSITION_FULL.json` |
| 팩트체크 | ✅ | `20260805_KTRANSITION_FACTCHECK.md` |
| 무작위 표본 sanity | ✅ | `20260805_KTRANSITION_RANDOM_SAMPLE.json` |
| stat 뇌 교체 설계 | ⏳ | **형 GO** |
| engine wire / auto-patch | 🚫 | GO 전 금지 |

## 핵심 판단 (수치 SSOT)

- rolling sim_k2: mean_hit **2.172** · Δ **+0.172** · **STRONG**
- brain_replace: **즉시착수** (target=stat) — **설계 착수**이지 wire 아님
- markov 80% / review 20% / stat 0% 유지 중

## 금지 (동결)

`random.choices` · `engine.py` 직접 수정 · auto-tune · wire · DB INSERT/UPDATE
