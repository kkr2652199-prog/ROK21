# K-TICKET-COVER-LITE — LIST_V3 L10

시각: 2026-08-12T10:47:32+09:00 · **HOLD** · apply=**False** · wire=**False** · **1237아님** · ge3미클레임 · buy-the-pot금지  
구간: 1137~1236 seeds=[0, 42, 123] · 발권경로(dedup→`dynamic_brain_quota`)  
다음: **L11** 축 심화 잔여 (review EV 우선)

## 판정 요지

커버 축(평균 Jaccard↓ · union↑)에는 **신호 있음**.  
그러나 모든 후보가 **prefer 악화**(≤ −0.005) 및/또는 **prize 비악화 실패** → 게이트 FAIL → **상수 APPLY 안 함** (`TICKET_COVER_LITE=False` 유지).

발권경로 base `prize`가 이미 **양수**(0.014)라 pool경로식 `prize<0` health는 본 축에 부적합 — 게이트는 **base 대비 비악화**로 판정(전원 탈락).

## base (COVER off)

| prefer | prize | mean_J | mean_union | best_hits(모니터) | hit_union(모니터) |
|--------|-------|--------|------------|-------------------|-------------------|
| 0.114766 | 0.013622 | 0.111309 | 20.88 | 1.64 | 2.72 |

## cands

| cand | pen | mean_J | union | dJ | dU | d_prefer | d_prize | pass |
|------|-----|--------|-------|----|----|----------|---------|------|
| cover_p0.5 | 0.5 | 0.099345 | 21.61 | +0.012 | +0.73 | −0.0096 | +0.0065 | **False** |
| cover_p1.0 | 1.0 | 0.089415 | 22.09 | +0.022 | +1.21 | −0.0129 | +0.0070 | **False** |
| cover_p1.5 | 1.5 | 0.081536 | 22.54 | +0.030 | +1.66 | −0.0084 | +0.0085 | **False** |
| cover_p2.0 | 2.0 | 0.076821 | 22.87 | +0.034 | +1.99 | −0.0118 | +0.0027 | **False** |

임계: JACCARD_DELTA=0.015 · UNION_DELTA=0.5 · PREF_EPS=0.005 · PRIZE_EPS=0.005

## 코드

- `app/testlotto/brains/coordinator.py` — `_cover_lite_pick` · `TICKET_COVER_LITE`(기본 False) · `TICKET_COVER_JACCARD_PENALTY`
- 도구: `tools/_k_ticket_cover_lite.py`
- 벤치: `docs/benchmarks/20260812_KTICKET_COVER_LITE.json`

## 비고

- seeds 3개가 수치 동일: 발권 RNG=`BRAIN_RNG_SEED_BASE+draw_no` (프로브 seed 미개입) — 재현 안정.
- best_hits/hit_union은 **모니터만** (성적 클레임 금지).
