# K-TIER45-SOURCE-AUDIT

시각: 2026-08-12T07:48:29+09:00 · **READ-ONLY** · wire=**False** · ge3미클레임 · **1237아님**

## 판정
**AUDIT_OK**

## 전제 (중요)
- BTv5 `best_hits/tier` 는 **pool10+repack5 ×3뇌** 경로의 최고치(장수 많음).
- **발권 5장** 경로와 동일하지 않음 → 4등 관측 ≠ 양산 발권 4등.

## BTv5 요약
- run_id **13** · mean_hits **2.5**(모니터)
- tiers r1~r5 = {'r1': 0, 'r2': 0, 'r3': 0, 'r4': 4, 'r5': 42}

## 4등(r4) 분해
- 회차: `[1150, 1160, 1208, 1214]`
- pool≥4 기여뇌: `{'review': 2, 'markov': 1}`
- repack≥4 기여뇌: `{'markov': 1, 'review': 1}`
- pool>repack(hit): **2**/4 · 동률: 1/4
- 발권5장 재실행 best≥4: **0**/4 · best≥3: 0/4

## 5등(r5) 분해(캐시)
- n=42 · pool≥3 기여뇌 `{'stat': 21, 'markov': 18, 'review': 14}` · repack≥3 `{'stat': 11, 'markov': 13, 'review': 6}` · pool>repack **16**

## 전구간 손실
- pool≥4 & repack<4: **2**/100
- pool≥3 & repack<3: **17**/100

## flags
```json
{
  "bt_best_is_pool_repack_path": true,
  "issue_path_r4_ge4_count": 0,
  "issue_path_r4_sample_n": 4,
  "pool_ge4_lost_in_repack": 2,
  "pool_ge3_lost_in_repack": 17,
  "note": "UI/BT 4등이 발권5장 경로에서는 재현되지 않을 수 있음(장수효과)",
  "next_patch_hint": "pool→repack 보존(상위 hit 손실) 우선 후보"
}
```

## 다음(리스트① 완료 → ②)
- 발권경로에서 r4가 안 나오면: **장수효과 정정 문서화** + 상위적중 목표를 prefer/prize·pool보존으로 재정의
- pool≥4 손실>0 이면: **repack 보존 패치**가 다음 코드 후보

## 근거
- `D:/ROK21/docs/benchmarks/20260812_KTIER45_SOURCE_AUDIT.json`
- `D:/ROK21/reports/20260812_KTIER45_SOURCE_AUDIT.md`
