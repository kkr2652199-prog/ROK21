# K-BT100-DEEP-AUDIT — 100회 강제풀 심층감사

시각: 2026-08-11T14:03:15+09:00 · 범위 [1137, 1236] · 4·5등·뇌별 몰아주기 확인 · 버그/개선 교차분석

## 판정 **AUDIT_DONE_NO_HARD_BUG**
- hard_bugs=False · peek_ok=True · bad_sets=0 · bt_mismatch=0 · cache_miss=0
- ge3 클레임 금지 · 1237아님

## 형 UI 교차검증 (전체 best-of)
- mean_best_hits=2.59 · **4등=6** · **5등=48**
- tier_counts={'0': 46, '1': 0, '2': 0, '3': 0, '4': 6, '5': 48}
- 4등 회차=[{'draw': 1144, 'hits': 4, 'bonus': 6}, {'draw': 1150, 'hits': 4, 'bonus': 25}, {'draw': 1160, 'hits': 4, 'bonus': 19}, {'draw': 1208, 'hits': 4, 'bonus': 25}, {'draw': 1214, 'hits': 4, 'bonus': 14}, {'draw': 1216, 'hits': 4, 'bonus': 25}]

## 뇌별 몰아주기(repack) 성적
- **stat**: repack **r4=0** · **r5=7** · mean_hits pool=1.98 / repack=1.54 · pool>repack=45 / repack>pool=8
  - pool_tiers={'0': 78, '1': 0, '2': 0, '3': 0, '4': 1, '5': 21} · repack_tiers={'0': 93, '1': 0, '2': 0, '3': 0, '4': 0, '5': 7}
- **markov**: repack **r4=1** · **r5=10** · mean_hits pool=2.07 / repack=1.63 · pool>repack=41 / repack>pool=6
  - pool_tiers={'0': 76, '1': 0, '2': 0, '3': 0, '4': 2, '5': 22} · repack_tiers={'0': 89, '1': 0, '2': 0, '3': 0, '4': 1, '5': 10}
  - repack 4등 회차=[1160]
- **review**: repack **r4=1** · **r5=7** · mean_hits pool=1.98 / repack=1.63 · pool>repack=39 / repack>pool=11
  - pool_tiers={'0': 84, '1': 0, '2': 0, '3': 0, '4': 2, '5': 14} · repack_tiers={'0': 92, '1': 0, '2': 0, '3': 0, '4': 1, '5': 7}
  - repack 4등 회차=[1208]

## 캐시 vs live knobs (중요)
- score_build_vs_live=False
- build SCORE={'stat': [0.25, 0.35, 0.4], 'markov': [0.65, 0.15, 0.2], 'review': [0.65, 0.15, 0.2]}
- live SCORE={'stat': [0.25, 0.35, 0.4], 'markov': [0.65, 0.15, 0.2], 'review': [0.65, 0.15, 0.2]}
- live W_CROWD={'markov': 0.9, 'review': 0.9}
- tune_json filled=300/300 · live_overlay_draws=0
- note: 강제100회 빌드 시점 SCORE=cand_A · 이후 cand_B·W0.9 적용. 구행은 tune_json NULL이라 get_cached_pool_view가 live tune_snapshot으로 폴백할 수 있음.

## 이미 된 패치
- **I-TUNE-SNAPSHOT-OVERLAY PATCHED**: `tune_json` 컬럼 · 저장/서빙 시 배출 knobs 우선
- **I-CACHE-STALE-KNOBS 잔여**: UI 숫자는 옛 knobs(cand_A) 가능 → 강제100회 재실행 권장

## 개선 후보 (우선순위)
### I-REPACK-LOSS-stat · medium · OPEN
- 가설: stat 몰아주기가 pool 최고히트보다 낮아 손실
- 제안: signal_top 슬롯·SCORE/HINT 재튜닝 또는 몰아주기 선별 특성 점검(기존 K-REPACK-SELECT-DIAG 참고)

### I-REPACK-LOSS-markov · medium · OPEN
- 가설: markov 몰아주기가 pool 최고히트보다 낮아 손실
- 제안: signal_top 슬롯·SCORE/HINT 재튜닝 또는 몰아주기 선별 특성 점검(기존 K-REPACK-SELECT-DIAG 참고)

### I-REPACK-LOSS-review · medium · OPEN
- 가설: review 몰아주기가 pool 최고히트보다 낮아 손실
- 제안: signal_top 슬롯·SCORE/HINT 재튜닝 또는 몰아주기 선별 특성 점검(기존 K-REPACK-SELECT-DIAG 참고)

### I-TUNE-SNAPSHOT-OVERLAY · high · PATCHED_THIS_TURN
- 가설: get_cached_pool_view가 tune_snapshot을 live로 덮어씀
- 제안: tune_json 컬럼+저장/서빙 패치 유지(구행 NULL→live폴백). 신규 강제BT 시 시점보존.

### I-MARKOV-LEARN-NO-EFFECT · medium · OPEN
- 가설: markov learn 경로가 히트에 실질 영향 없음
- 제안: learn boost·visit_count 경로 포함한 overdue/carry 조건 축소 · 선호번호 blend가 지배적인지 확인 후 boost 설계 재검토(동결상한 준수)

### I-STAT-ENGINE-V2-FLAG · low · OPEN
- 가설: stat ENGINE_V2 플래그/ past_learn 이중경로 혼선
- 제안: 엔진 v2 vs past_learn soft 이중경로 문서화·어느 쪽이 live 지배인지 측정

### I-FEATURE-LAMBDA-OFF · low · OPEN
- 가설: feature lambda 와이어 OFF로 보조축 미사용
- 제안: 몰아주기 보조축으로 재개하려면 뇌별 λ 소규모 게이트(ge3금지·축분리)

### I-KJ-DUAL-WEIGHT · medium · OPEN
- 가설: 발권 가중 SSOT 이중화(문서 vs live)
- 제안: 발권 SSOT=live referee로 문서·코드화 일치(K-J)

### I-AUX-HINT-WEIGHT · medium · OPEN
- 가설: aux hint 가중 고정으로 뇌별 힌트 기여 과소/과다
- 제안: HINT_WEIGHT_BY_BRAIN 스윕(축=prefer/prize/hit · iso)

## 부품 맵
- 엔진: stat/markov/review `engine.py`
- 학습: `learn.py` · learn_state · CUTOFF
- 군중: crowd_signal W/BLEND
- 몰아주기: signal_pool.repack · assemble_signal_top
- 보조: aux hint · feature_lambda · past_learn

JSON: `docs/benchmarks/20260811_KBT100_DEEP_AUDIT.json`
