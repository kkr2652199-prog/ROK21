# AI_COLLAB — 커서×젠스파크 협업 규칙 + 대화 요약

> **세션 압축 대비 SSOT.** 젠스파크 세션이 압축되면 이 파일 + EXTERNAL_START.md 를 읽어 복구.

## 1. 역할 분담

| 역할 | 담당 | 권한 |
|------|------|------|
| **형(오빠)** | 최종 결정·GO/HOLD 승인 | 모든 방향 결정권 |
| **커서** | 코드 실행·commit·push·지시서 작성·벤치마크 | D:\ROK21 직접 접근, GitHub push |
| **젠스파크** | 전략 분석·검토·지시서 초안·팩트체크 | GitHub raw 읽기 전용 |

### 원칙
- AI끼리 논의 OK, **방향 확정은 반드시 형 GO**
- 지시서 작성: 커서가 최종본 작성·실행 (젠스파크 초안 참고 가능)
- 수치 인용: `docs/benchmarks/*.json` SSOT만 (기억으로 쓰지 않음)

## 2. 세션 압축 대비 규칙

1. **GitHub = 영구 기억.** reports/, docs/benchmarks/, EXTERNAL_START.md, NEXT_ACTIONS.md, AI_COLLAB.md 가 SSOT
2. **압축되면 GitHub 파일 먼저 읽기.** 특히 EXTERNAL_START.md (현재상태) + AI_COLLAB.md (협업룰+대화요약)
3. **커서가 매 push 시 이 파일의 §3 대화요약을 갱신** → 압축 후에도 논의 맥락 복구 가능
4. 형이 젠스파크에 "GitHub 보고서 확인해줘" 하면 → 젠스파크가 raw URL로 읽고 팩트체크

## 3. 대화 요약 (커서가 매 push 시 갱신)

### 최신 상태 (2026-08-05 KST)
- **HEAD(실측)**: push 후 sync · SSOT=`kkr2652199-prog/ROK21` · 포트 **7021**
- **지금(판정)**: **K-EVOLVE-AUTO-S3** — **PASS** (PREDICT 1236)
- **다음(공식)**: S4 EVOLVE_AUTO=1 또는 다른축 · **형 GO**
- **산출물**: `docs/benchmarks/20260805_KEVOLVE_AUTO_S3.json`

### K-EVOLVE-AUTO-S3 (형 진행 · PASS)
- `--apply-predict` · `predict_and_cache` / `predict_then_score`
- 실행: PREDICT_ONLY **1236** → pool_view_cache (미추첨·SCORE 없음)
- feedback / EVOLVE_AUTO=1 **미적용** · phase=`predicted`

### K-EVOLVE-AUTO-S2 (형 진행 · PASS)
- `--apply-score` · cache→evolve_log · draw **1235** 3뇌
- PREDICT / apply_feedback / λ·covering **미실행**
- phase=`scored` · evolve_log_max=**1235**

### K-EVOLVE-AUTO-S1 (형 진행 · PASS)
- `app/testlotto/evolve_auto.py` · `tools/_k_evolve_auto_tick.py`
- 테이블 `testlotto_evolve_auto_state` · phase=planned
- 관측: draws max=1235 · evolve_log max=1234 → SCORE 1235 계획
- apply 경로 거부 · `EVOLVE_AUTO` 기본 0

### K-EVOLVE-AUTO-DESIGN (형 진행 · DOC)
- 1236~ 예측→채점→evolve_log 운송벨트 설계
- `EVOLVE_AUTO` 기본 0 · weight=0 · mean만 · λ/covering wire 금지
- 구현 단계 S0(현재)~S4 · **코드 미구현**

### K-PAIR-COVER (형 진행 · HOLD)
- `pair_cover.py` · as_of 희소쌍 top80 · assemble=`pair_cover_v1` · **WIRE=False**
- n200: stat −0.01 · markov −0.025 · review −0.02 vs hybrid
- covering 2축(구조·쌍) 모두 발권 ge3 변환 실패 · 명분 문서는 유효

### K-STRUCTURE-COVER (형 진행 · HOLD)
- 모듈 `structure_cover.py` · assemble=`struct_cover_v1` · **WIRE=False**
- n200 vs hybrid: stat −0.02 · markov −0.045 · review −0.05
- 교훈: 구조키 다양↑ ≠ ge3↑ · 명분은 유효, 발권 변환은 실패
- 다음 후보축: 저출현쌍 covering

### K-MATH-PATTERN-WARRANT (형 지시 · FOUND)
- 범위 draw **1~1235** · 예측백테/ge3 **아님**
- 금지결론「확률 외 방법 없음」**미사용**
- 명분: 연속·carry·합띠·존·쌍covering·overdue·끝자리·스팬·빈도분산·3홀3짝
- 실측예: 연속≥1 **0.517**≈이론0.529 · carry≥1 **0.614**≈0.599 · 합 mean≈**138**

### K-EVOLVE-FEAT-LAM-REVAL (형 진행 · HOLD)
- full 53~1234: review λ0.3 ge3=0.1227 vs base 0.1252 (**Δ−0.0025**)
- tail200: λ0.3=0.105 vs base 0.135 (**Δ−0.03**) — SIGNAL 0.145는 희소과적합
- 조치: `FEATURE_LAMBDA_WIRE=False` · by_brain={} · assemble 복귀 `hy_p45_r123`
- AUTO 실행 게이트 **미달** · 설계문서만 가능

### K-EVOLVE-LOG-EXPAND (형 다음진행 · PASS)
- evolve_log **53~1234** · **1182**회 · weight=0
- from_wf **982** · from_cache **200** · miss구간 pool_cache 미저장
- 확장 중 λ OFF → 종료 후 live review λ0.3 복원
- 재실행: `python tools/_k_evolve_log_expand.py`

### K-EVOLVE-FEAT-LAM-WIRE (형 다음진행 · PASS)
- `feature_lambda.py` · `FEATURE_LAMBDA_BY_BRAIN={review:0.3}`
- offline n200 ge3=**0.145** = SIGNAL survey MATCH
- live assemble=`feat_lam_0.3` · CACHE_SCHEMA_VERSION=**3**
- stat/markov λ **HOLD** · mean feedback / hybrid / quota 유지

### K-FUTURE-FULL-POST-EVOLVE (형 진행 · DONE)
- hybrid+mean 이후 FULL 리셋 WF · draw 53~1234 · n=1182
- ge3=**0.1184**(140) · mean=1.6912 · vs 구FULL **Δ=0** · thirds 동일
- `FEEDBACK_MATCH_MODE=mean` · 구FULL JSON **미덮어씀**
- patch gate PASS · pin/enrich FAIL 유지

### K-EVOLVE-SIGNAL (형 GO · DONE)
- **WIRE:** `FEEDBACK_MATCH_MODE=mean` — best단독 학습 차단(K-N)
- PartA: best−mean ≈ +0.95~1.08 · best>mean **96%+**
- PartB λ: review **0.145**(+0.01 @λ0.3) · stat/markov는 baseline 미달 → **λ 전뇌 HOLD** · review만 GO-WAIT
- BOOST_CAPS / W_* / quota 미수정

### K-EVOLVE-LOG (형 A안 GO · PASS · weight=0)
- 테이블 `testlotto_evolve_log` · 백필 1035~1234 **200**회
- API: `/api/testlotto/evolve/log/{draw}` · `/evolve/summary`
- 저장: pool10+repack5 hits · features · miss_tags · assemble · **weight_applied=0**
- predict/W_*/quota/apply_feedback **미수정**
- ge3 참고(=hybrid): stat 0.165 · markov 0.130 · review 0.135

### K-MULTI-AI-PATCH (형 요청 · DOC)
- 합의: 진화 학습=약 · best번호 복습=독(K-N)
- 최종: Phase1 LOG(가중0) → Phase2 SIGNAL → Phase3 AUTO(1236~)
- 선택: A=LOG · B=LOG+FULL스냅샷 · C=FULL만 · D=계수재탕(비권고)
- 권고: **A 또는 B**

### K-REPACK-HYBRID-WIRE (형 GO · PASS · live)
- `signal_pool.assemble_hybrid_p45_r123` · brains=stat,review · markov=baseline
- `pool_view_cache` schema **2** (구캐시 miss→재계산)
- 검증 n200: stat **0.165** · markov **0.130** · review **0.135** (ablation 일치)
- smoke 1230 assemble: stat/review=hy_p45_r123 · markov=baseline_repack
- coordinator/quota **미수정**

### K-REPACK-HYBRID (형 GO · DONE · wire 없음)
n=200 · 1035~1234 · cache READ-ONLY

| 뇌 | baseline | hy_brain_rec | Δ |
|----|----------|--------------|---|
| stat | 0.125 | **0.165** | **+0.040** |
| markov | 0.130 | 0.130 | 0 |
| review | 0.105 | **0.135** | **+0.030** |

권고 wire: stat+review = pool4+5 + 몰1~3 · markov = 현행 몰아주기 유지

### K-PIN-GAP-DIAG (형 GO · DONE · wire 없음)
| 항목 | 결과 |
|------|------|
| FULL Δpin | **−0.0263** (0.1184 vs 0.1447) |
| 기간(n=394) | early **0.099** 최악 · mid 0.132 · late 0.1244 · **mid붕괴 기각** |
| markov80% | fused 0.1184 · blend≈0.126 · solo markov 0.13도 pin 미달 |
| N100 seed | 42→**0.15** · 0/7→**0.10** · range **0.05** 민감 |
| K-M | pin갭 기여 **≈0** |
| K-N | **low_indirect** (early≪late) |
| 다음후보 | early안정화 · I2 FULL-first · multi-seed 게이트 · I3 B1 |

### K-PIN-GAP-DIAG-REVIEW (커서 검토 · 실행 전)
목적 OK: FULL ge3 **0.1184** vs pin **0.1447** Δ**−0.0263** · READ-ONLY 진단 · wire 금지.  
**GO 전 수정 필수 3건:**
1. 기간 = FULL thirds **n=394** (early ge3 **0.099** 최악 · mid **0.132** · late **0.124**). `25/25/50`·「mid 붕괴」는 N100 혼동 → 삭제
2. READ-ONLY = 기존 JSON 1차. `_k_future_wire_revalidate` reset·WF는 별도 GO
3. 종료 = ROK21 **종료5종 + R37 sync** (EXTERNAL/AI_COLLAB/NEXT/FLOW만 부족)

근거: `docs/benchmarks/20260803_KFUTURE_WIRE_FULL.json` · 로드맵 `reports/20260804_IMPROVEMENT_INVESTIGATION_ROADMAP.md`

### K-IMPROVE-ROADMAP (형 요청 · DONE · 권고 A=I1+I3)
- I1 pin갭진단 1순위 · I3 B1로그 병행 · ultra→ge3 wire **HOLD**
- 선택지 A/B/C/D · 보고서·canvas 완료

### K-GS-FACTCHECK / K-RARE-* (직전 축)
- 팩트체크 대체로 PASS · 복귀 HEAD=`53decde` 정정 · pin갭≠n100 collapse 구분
- rare catalog 213 · ultra 183 · 구조희귀≠당첨P · wire HOLD

### K-FUTURE-WIRE-REVAL (형 GO · 리셋 WF 재검증)
근거: `docs/benchmarks/20260803_KFUTURE_WIRE_QUICK200.json` · `..._FULL.json`

| 항목 | QUICK200 | FULL1182 |
|------|----------|----------|
| draw | 1035~1234 | 53~1234 |
| ge3 | **0.1350** (27/200) | **0.1184** (140/1182) |
| vs n100 0.15 | −0.0150 | −0.0316 |
| vs pin 0.1447 | −0.0097 | −0.0263 |
| patch gate (>0.09) | **PASS** | **PASS** |
| enrich gate | FAIL (p=0.199) | FAIL (pin·p) |
| reset | pred/learn/review/weights/cache 삭제·재기입 · draws 유지 | 동일 |

**결론:** n100 이득은 유지되나 구간 확대 시 collapse. C-package FULL 0.1015 대비 +0.0169. pin 회복이 다음 후보.

### K-FUTURE-WIRE (형 GO · PASS · live)
근거: `docs/benchmarks/20260803_KFUTURE_WIRE_N100.json` · `reports/20260803_KFUTURE_WIRE_N100.md`

| 항목 | 값 |
|------|-----|
| 뿌리 원인 | 융합 시 공유 `random` — stat이 markov solo 번호를 오염 → fused 천장 0.09 |
| 핵심 패치 | 뇌마다 `seed(42+draw)` 리셋 · solo와 동치 생성 |
| 구조 패치 | `aux_hint_score`/`native_confidence` 보존 · bucket=`aux_hint_native` |
| smoke 1230~1234 | **PASS** |
| n=100 ge3 | **0.1500** (15/100) |
| vs V2 baseline | **+0.0600** |
| by_period | early **0.2000** · mid **0.0800** · late **0.1600** |
| gate | ge3 **>** 0.0900 → **PASS** |
| live | V2 quota(4/0/1) + FUTURE-WIRE 유지 |

**결론:** 0.09 벽의 진짜 원인은 aux 가중/쿼터가 아니라 **독립뇌 RNG 미분리**. 분리 후 solo 성능이 fusion에 전달됨.

### K-FUSION-INNOVATION (형 GO · FAIL · rolled back)
근거: `docs/benchmarks/20260803_KFUSION_INNOVATION_N100.json` · `reports/20260803_KFUSION_INNOVATION_N100.md`

| 항목 | 값 |
|------|-----|
| 변경 (1) | bucket **confidence desc** (기존 set_no asc) |
| 변경 (2) | AUX_WEIGHTS **[0.20, 0.35, 0.10, 0.35]** |
| smoke 1230~1234 | **PASS** (5장 ×5 · plan 4/0/1) |
| n=100 ge3 | **0.0900** (9/100) |
| vs V2 baseline | **+0.0000** (tie) |
| by_period | early **0.1200** · mid **0.0400** · late **0.1000** |
| gate | ge3 **>** 0.0900 → **FAIL** |
| rollback | INNOVATION 2곳 **롤백** · V2 SOLO_GE3_PRIORS **유지** |

**결론:** aux/wire 단독 조정으로 ge3 벽 미돌파 · K-AUX-DIAG 예상(ge3 quota 지배) 재확인 · **형 GO 대기**

### K-FUSION-DYNAMIC-V2 (형 GO · FAIL(1bp) · live)
근거: `docs/benchmarks/20260802_KFUSION_DYNAMIC_V2_N100.json` · `reports/20260802_KFUSION_DYNAMIC_V2_N100.md`

| 항목 | 값 |
|------|-----|
| `_get_quota_weights` | referee × **SOLO_GE3_PRIORS** (고정 DEFAULT 폐기) |
| SOLO_GE3_PRIORS | stat=0.09 · markov=0.13 · review=0.11 (K-HIGHWAY by_brain) |
| QUOTA_DOMINANCE_FLOOR | **1.15** → plan **4/0/1** |
| referee-only (V2 초版) | ge3=**0.0600** (1/3 균등 → 2/2/1) |
| solo×ref (V2.1 **live**) | ge3=**0.0900** (9/100) |
| vs fixed quota60 0.0800 | **+0.0100** |
| vs markov80 floor 0.0900 | **동일** |
| gate | ge3 **>** 0.0900 → **FAIL** (1bp tie) |
| quota avg | stat **0%** · markov **80%** · review **20%** |
| commit | `63ae865` + `f97312c` (R37 sync) |

**결론:** 3뇌 교체에 맞춘 동적 quota live · markov80 floor와 동일 ge3 · gate strict 1bp 부족 · **형 GO 대기**

### 현재 live stack (2026-08-03 · SOLO_GE3_PRIORS · dominance 1.15)
```
run_coordinated_prediction
  → _auto_feedback(prev) → apply_feedback → learn_state
  → 3뇌 predict_sets(draws)          ← B1 virtual draws **제거됨**
  → aux 1:1 scoring (AUX_1TO1_ENABLED)
  → dynamic_brain_quota (referee × SOLO_GE3_PRIORS → plan 4/0/1)
  → DB 저장
```
- `pattern_signal.py` **파일 보존** · coordinator에서 signal wiring **없음**
- markov engine: **full draws** (window100 롤백 완료)
- `DEFAULT_QUOTA_WEIGHTS` 25/60/15: **legacy pin only** (production 미사용)

### K-QUOTA-MARKOV80-REV2 (형 GO · FAIL · superseded by V2)
근거: `docs/benchmarks/20260801_KQUOTA_MARKOV80_N100.json`

| 항목 | 값 |
|------|-----|
| DEFAULT | stat 10% · markov 80% · review 10% |
| floor | markov **4/5** · stat 1 · review 0 |
| smoke 1230~1234 | **PASS** (markov 4/5 ×5) |
| n=100 ge3 | **0.0900** (9/100) |
| vs quota60 0.0800 | **+0.0100** |
| vs fused diag markov100% 0.0900 | **동일** |
| gate | ge3 **>** 0.0900 → **FAIL** (0.0900 = tie) |
| quota avg | stat **20%** · markov **80%** · review **0%** |
| rollback | DEFAULT **25/60/15** + floor 로직 **제거** · 이후 **K-FUSION-DYNAMIC-V2**가 solo prior로 대체 |

**결론:** floor 4/5는 quota60 +0.01 · fusion diag 재현 · gate strict **1bp 부족** · V2 solo×ref로 **동일 ge3 대체 live**

### K-AUX-DIAG (형 GO · per-aux ablation · no auto next)
근거: `docs/benchmarks/20260801_KAUX_DIAG.json`

| scenario | ge3 | markov survival | survival Δ |
|----------|-----|-----------------|------------|
| baseline (all ON) | **0.0800** | **0.6680** | — |
| miss OFF | 0.0800 | 0.6680 | 0 |
| **spotlight OFF** | 0.0800 | **0.0000** | **−0.6680** |
| balance OFF | 0.0800 | **0.9480** | **+0.2800** |
| referee OFF | 0.0800 | 0.6680 | 0 |
| all aux OFF | 0.0800 | 0.0280 | −0.6400 |

**dropout ranking:** 1) **pattern_spotlight** (markov top5 생존 필수) · 2~3) miss/referee 무영향 · 4) **balance_keeper** (OFF 시 survival↑ = markov에 불리)

**결론:** ge3는 모든 시나리오 **0.0800 동일**(quota 5장 선택이 ge3 지배) · markov 탈락 1순위 **pattern_spotlight OFF→survival 0** · balance_keeper는 markov ranking 억제 · **형 GO 대기**

### K-FUSION-QUOTA-FIX (형 GO · FAIL · no auto-tune)
근거: `docs/benchmarks/20260801_KQUOTA_FIX_N100.json`

| 항목 | 내용 | 판정 |
|------|------|------|
| coordinator | `DEFAULT_QUOTA_WEIGHTS` stat25/markov60/review15 · `_get_quota_weights` · total-slot largest remainder | **OK** |
| smoke | draw 1230~1234 · 5장 · quota 1/3/1 | **PASS** |
| n=100 walk-forward | draw 1135~1234 · full coordinator | **FAIL** ge3=**0.0800** |

| 지표 | before (40/40/20) | after |
|------|-------------------|-------|
| overall ge3 | 0.0600 | **0.0800** (+0.0200) |
| mean_match | 1.63 | **1.63** |
| quota avg | stat 40% · markov 40% · review 20% | stat **20%** · markov **60%** · review **20%** |
| by_period ge3 | early 0.04 · mid 0.04 · late 0.08 | early **0.08** · mid **0.04** · late **0.10** |
| gate | — | ge3 **>** 0.0900 → **FAIL** |

**결론:** markov 쿼터 60%로 ge3 +0.02 개선 · 0.09 gate 미달 · auto-tune 없음 · **형 GO 대기**

### K-ENGINE-PHASE1-HOLD (형 GO · STEP1~2 · fusion diag)
근거: `docs/benchmarks/20260801_KFUSION_BOTTLE_DIAG.json`

| STEP | 내용 | 판정 |
|------|------|------|
| 1 window100 롤백 | build_transition_matrix full draws 복원 · smoke 1230~1234 5/5 | **OK** |
| 2 fusion diag n=100 | BENCH_FIXED_QUOTA markov=5 · draw 1135~1234 | **AUX_PATH_BOTTLENECK** |

| 지표 | 값 |
|------|-----|
| diag ge3_rate (markov 100%) | **0.0900** (9/100) |
| vs fused ref 0.0600 | **+0.0300** |
| vs solo markov ref 0.1300 | **−0.0400** |
| prod markov quota rate avg | **0.4000** (2/5 slots) |
| aux survival rate avg | **0.6680** (markov in global top5) |
| bottleneck | **aux_or_coordinator_path** (quota also contributes 0.06→0.09) |

**결론:** window100 롤백 완료 · solo 0.13 vs fused 0.06 격차는 quota(40%) + aux/coordinator path 혼합 · 회복 튜닝 **형 GO 대기**

### K-ENGINE-PHASE1 (형 GO · STEP1~3 · window100 FAIL)
근거: `docs/benchmarks/20260801_KMARKOV_WINDOW100_SOLO_N200.json`

| STEP | 내용 | 판정 |
|------|------|------|
| 1 B1 rollback | coordinator signal import/block 제거 · predict_sets(draws) 복원 · smoke 1230~1234 5/5 | **OK** |
| 2 markov window=100 | build_transition_matrix draws[-100:] · smoke 1230~1234 5/5 | **OK** |
| 3 solo bench n=200 | draw 1035~1234 walk-forward · vs K-HIGHWAY solo 0.1300 | **FAIL** ge3=**0.0850** |

| 지표 | 값 |
|------|-----|
| solo ge3_rate | **0.0850** (17/200) |
| mean_match | **1.6150** |
| vs ref 0.1300 | **−0.0450** |
| by_period ge3 | early **0.1194** · mid **0.0896** · late **0.0455** |
| gate | ge3 > 0.1300 → **FAIL** (auto-tune 없음) |

**결론:** B1 rollback 완료 · markov window100은 solo ge3 **하락** → 유지/롤백·fusion 회복 백테 **형 GO 대기**

### K-BRAIN-SIGNAL-B1-BACKTEST-100 (형 GO · FAIL · B1 rollback으로 superseded)
근거: `docs/benchmarks/20260801_KBRAIN_SIGNAL_B1_BACKTEST_100.json`

| 지표 | 값 |
|------|-----|
| overall ge3 | **0.0600** (6/100) — 방향1·highway **동일** |
| virtual_active_rate | **100%** |
| delta vs 0.0600 | **+0.0000** |
| by_brain solo | stat 0.09 · markov 0.13 · review 0.11 |
| by_period | early 0.04 · mid 0.04 · late 0.08 |

**결론:** B1 virtual draws도 ge3 개선 없음 → TUNE(_MIN_MAX_SIM) 또는 B1 롤백 검토

### K-BRAIN-SIGNAL-B1 (형 GO · PASS)
| 항목 | 내용 | 판정 |
|------|------|------|
| make_signal_draws | signal top6 → virtual draws×3 | **OK** |
| coordinator | draws_with_signal → predict_sets · conf blend **제거** | **OK** |
| smoke | 1225~1234 · virtual_active 10/10 | **PASS** |

**live stack (B1):**
```
run_coordinated_prediction
  → get_pattern_signal(draws)
  → make_signal_draws → draws_with_signal = virtual + draws
  → predict_sets(draws_with_signal)  ← engine weights에 signal 반영
  → aux 1:1 → dynamic_brain_quota → DB
```

### K-BRAIN-SIGNAL-BACKTEST-100 (형 GO · FAIL)
근거: `docs/benchmarks/20260801_KBRAIN_SIGNAL_BACKTEST_100.json`

| 지표 | 값 |
|------|-----|
| overall ge3 | **0.0600** (6/100) — highway와 **동일** |
| signal_active_rate | **100%** (100/100) |
| vs highway 0.0600 | **+0.0000** |
| vs baseline 0.1015 | **−0.0415** |
| by_brain solo | stat 0.09 · markov 0.13 · review 0.11 |
| by_period | early 0.04 · mid 0.04 · late 0.08 |
| DB | reset 후 **505행** 유지 · draw **1235** UI 5장 |

**판정:** FAIL (ge3 ≤ 0.0600) · signal 레이어는 **전 회차 active** → ge3 개선 없음 → TUNE(_MIN_MAX_SIM) 검토

### K-BRAIN-SIGNAL-A1 (형 GO · PASS · B1에서 conf blend **대체됨**)
| 항목 | 내용 | 판정 |
|------|------|------|
| pattern_signal.py | 9-dim cosine top-k analog signal | **OK** |
| coordinator (A1) | 85% conf + 15% signal — **B1에서 제거** | superseded |
| BACKTEST-100 (방향1) | ge3=0.0600 = highway 동일 | **FAIL** |

### K-HIGHWAY-PHASE1 (형 GO · 코드 반영 완료 · 백테 FAIL)
| ID | 파일 | 내용 | 판정 |
|----|------|------|------|
| K-HIGHWAY-FEEDBACK | coordinator.py | `_auto_feedback` · `_detect_missed_patterns` · deprecated import 삭제 | **OK** |
| K-HIGHWAY-REFEREE | aux_referee.py | `score_set()` → `get_referee_weights()` 반영 | **OK** |
| K-HIGHWAY-QUOTA | coordinator.py | `dynamic_brain_quota()` · referee 가중 5장 (min 1/뇌) | **OK** |
| K-HIGHWAY-BACKTEST-100 | tools | draw 1135~1234 n=100 · full coordinator walk-forward | **FAIL** ge3=0.0600 |

**현재 live stack (PHASE1 반영):**
```
run_coordinated_prediction 진입
  → _auto_feedback(prev) → apply_feedback → learn_state
  → 3뇌 predict 15장 → aux 1:1 scoring
  → dynamic_brain_quota (referee 가중 5장 · set_no_asc)
  → DB 저장
```

### K-HIGHWAY-BACKTEST-100 수치 SSOT
근거: `docs/benchmarks/20260801_KHIGHWAY_BACKTEST_100.json`

| 지표 | 값 |
|------|-----|
| overall ge3 | **0.0600** (6/100) |
| mean_match | 1.63 |
| vs K-BACKTEST-FULL-C baseline | **−0.0415** (0.1015) |
| by_brain solo ge3 | stat 0.09 · markov **0.13** · review 0.11 |
| by_period ge3 | early 0.04 · mid 0.04 · late 0.08 |
| dynamic quota avg | stat 40% · markov 40% · review 20% → **K-QUOTA-FIX 후 20/60/20** |
| learn 루프 | **동작 확인** — draw1234 rc=99 · carry/ending adj cap 도달 |

**형 결정 대기:** PHASE1 **HOLD** vs **롤백**(고정 쿼터 markov3/stat1/review1) vs **튜닝**

### 병렬 트랙 (별도 · PHASE1과 독립)
| ID | 판정 | 비고 |
|----|------|------|
| **K-BRAIN-SIGNAL** | **B1-BACKTEST FAIL** | ge3=0.0600 · virtual 100% · TUNE/롤백 **형 GO 대기** |
| K-NEW-ENGINE-STAT-A1 | **PASS** (delta=0) | ENGINE_V2=False 유지 · solo ge3=0.1350 |
| K-BRAIN-TUNE-SURVEY | **HOLD** | best_combo 0.1032 · auto-apply 금지 |
| K-BRAIN-LOGIC-UPGRADE | **설계 검토만** | 젠스파크 4방향 · 커서 Q1~Q5 답변 · 형 GO 전 구현 금지 |
| K-CLEANUP-AND-NEW-ENGINE-PREP | **커서 거부** | engine NotImplementedError 교체 위험 |

### ⚠️ 중단·거부 지시서
- **K-CLEANUP** — 레거시 mv + engine 스켈레톤 → 커서 **실행 거부** (Q1~Q6 반문 · §6 참고)

### 벤치 수치 SSOT (주요 · `docs/benchmarks/*.json`)
| ID | n | ge3 | 판정 |
|----|---|-----|------|
| **K-FUTURE-WIRE-FULL** | 1182 | **0.1184** | patch PASS · pin FAIL · vs C-FULL +0.0169 |
| **K-FUTURE-WIRE-QUICK200** | 200 | **0.1350** | patch PASS · enrich FAIL |
| **K-FUTURE-WIRE** | 100 | **0.1500** | **PASS** · +0.06 vs V2 · **live** |
| **K-FUSION-INNOVATION** | **FAIL** — conf bucket+AUX reweight n=100 ge3=**0.0900** · vs V2 +0 · **rolled back** |
| K-QUOTA-MARKOV80-REV2 | 100 | **0.0900** (floor 4/5) | **FAIL** → V2 대체 |
| **K-AUX-DIAG** | 100 | **0.0800** (전 시나리오 동일) | **DONE** |
| K-FUSION-QUOTA-FIX | 100 | **0.0800** | **FAIL** (>0.09) |
| K-FUSION-BOTTLE-DIAG | 100 | **0.0900** (markov100%) | diag |
| K-MARKOV-WINDOW100-SOLO | 200 | **0.0850** | **FAIL** |
| K-HIGHWAY-BACKTEST-100 | 100 | **0.0600** | **FAIL** |
| solo markov (highway by_brain) | — | **0.1300** | ref |
| K-BACKTEST-FULL-C | 1182 | 0.1015 | FAIL (<0.1218) |
| K-NEW-ENGINE-STAT-A1 | 200 | 0.1350 (v2=0.1350) | PASS (delta=0) |

### fusion ge3 격차 분해 (확정 · 2026-08-03)
| 단계 | ge3 | vs 이전 | 원인 |
|------|-----|---------|------|
| full coordinator (highway) | 0.0600 | — | quota 40/40/20 + aux |
| quota fix 20/60/20 | **0.0800** | +0.02 | markov quota ↑ |
| markov 100% fixed (diag) | 0.0900 | +0.01 | quota 희석 제거 |
| markov80 floor 4/5 | 0.0900 | tie | hard floor |
| referee-only (V2) | 0.0600 | −0.03 | 1/3 균등 referee |
| **solo×ref (V2 live)** | **0.0900** | +0.03 vs referee-only | SOLO_GE3_PRIORS + dominance 1.15 |
| solo markov | 0.1300 | +0.04 | aux/coordinator path 손실 |
| aux ablation | **0.0800** (변화 없음) | 0 | quota 5장 선택이 ge3 지배 |

### 논의 이력 (최신순)
1. **[08/03] 젠스파크 동기화** — 20260803 보고서 · AI_COLLAB §3·§6 · RESTORE commit열 갱신
2. **[08/02] K-FUSION-DYNAMIC-V2 FAIL(1bp)** — solo×ref ge3=0.0900 · referee-only 0.06 · commit 63ae865
3. **[08/02] 종료체크 commit+push** — f97312c R37 HEAD sync
4. **[22:35] K-AUX-DIAG DONE** — 6시나리오 · ge3 전부 0.0800 · spotlight OFF→surv 0 · balance OFF→surv 0.948
2. **[21:45] K-FUSION-QUOTA-FIX FAIL** — quota 20/60/20 · ge3=0.0800 (+0.02 vs 0.06)
3. **[21:10] K-ENGINE-PHASE1-HOLD** — window100 롤백 · fusion diag AUX_PATH_BOTTLENECK ge3=0.09
4. **[20:30] K-ENGINE-PHASE1** — B1 rollback · window100 solo FAIL ge3=0.0850
5. **[19:30] K-ENGINE-UPGRADE 브리핑** — PHASE1~3 의견 · markov window100만 GO 가치
6. **[18:55] K-BRAIN-SIGNAL** — A1/B1 BACKTEST FAIL ge3=0.0600 · B1 rollback됨
7. **[17:50] K-HIGHWAY-BACKTEST-100 FAIL** — ge3=0.0600 · PHASE1 코드 반영

## 4. 파일 지도 (젠스파크용 GitHub raw URL)

| 용도 | URL |
|------|-----|
| 현재상태 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/EXTERNAL_START.md` |
| 협업룰+대화 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/AI_COLLAB.md` |
| NEXT 1건 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md` |
| 수치 SSOT | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/` |
| 보고서 | `https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/reports/` |
| 보고서 언어 규칙 | `My_Drive_Sync/SUMMARY/REPORT_STYLE.md` |

## 6. 압축 복구 패킷 — 외부 AI(젠스파크)에 붙여넣기용 (2026-08-04 11:35)

> 형이 젠스파크 세션 압축 후 **아래 블록 전체**를 채팅에 붙여넣으면 맥락 복구.  
> 전문·타임라인: `reports/20260804_GENSPARK_COMPRESS_RESUME.md`

```
[ROK21 압축복구 · 2026-08-04 · pin갭진단 직전]

■ SSOT
- Repo: kkr2652199-prog/ROK21 · main · D:\ROK21 · 포트 7021
- kweon(D:\3kweon) 동결 · 쓰기·push·신규작업 금지
- 진입1순위: EXTERNAL_START.md (루트)
- 협업·대화: AI_COLLAB.md §3·§6
- NEXT: My_Drive_Sync/SUMMARY/NEXT_ACTIONS.md
- 수치 SSOT: docs/benchmarks/*.json (기억 금지)

■ 지금 / 다음
- 지금: K-PIN-GAP-DIAG-REVIEW DOC — 젠스파크「K-PIN-GAP-DIAG GO」지시서 구조대조 완료
- 직전: K-IMPROVE-ROADMAP DONE — 권고 I1 pin갭진단 + I3 B1로그 · ultra wire HOLD
- 다음: 수정3건 반영한 K-PIN-GAP-DIAG GO · 또는 로드맵 A/B/C/D 형 선택
- 실행 금지: 수정 전 원본 지시서로 WF/wire 착수

■ live 성적 (확정 · JSON)
| 벤치 | n | ge3 | 비고 |
| FUTURE-WIRE N100 | 100 | 0.1500 | PASS · live |
| FUTURE-WIRE QUICK | 200 | 0.1350 | patch PASS · pin FAIL |
| FUTURE-WIRE FULL | 1182 | 0.1184 | pin 0.1447 · Δ−0.0263 FAIL |
| null best-of-5 | — | 0.1137 | fusion 5장 기준 |
| WIRE-V2 pin | — | 0.1447 | stored |
| quota FULL | — | markov 80% · review 20% · stat 0% | 고착 |

■ FULL by_period (n=각 394 · 「mid 붕괴」아님)
| 구간 | ge3 | vs pin |
| early | 0.0990 | −0.0457 최악 |
| mid | 0.1320 | −0.0127 상대 최선 |
| late | 0.1244 | −0.0203 |

※ N100 기간 n=25/25/50 은 FULL과 다른 창. pin갭 본체 진단은 FULL thirds.

■ K-PIN-GAP-DIAG 지시서 — GO 전 수정 3건 (커서 검토 확정)
1) 기간: FULL n=394 thirds. 「early/mid/late n=25/25/50」「mid 붕괴」문구 삭제
2) READ-ONLY: 1차=기존 JSON 분해. _k_future_wire_revalidate reset·WF는 별도 GO
3) 종료: ROK21 종료5종 + sync_all_resume_docs (EXTERNAL/AI_COLLAB/NEXT/FLOW만으로는 미달)

그 외 OK: 목적(Δ−0.0263) · markov80% · seed=42 · K-M/N 수치확인 · wire/engine/auto-tune/FINDINGS무단 금지

■ 최근 완료 타임라인 (과거→현재)
1. UI 즉시·프리로드 (BT DB 즉시표시)
2. K-BENCH-NULL-BY-EVAL (eval_mode별 null · best15 허위PASS 제거)
3. K-FUTURE-WIRE (+REVAL) live · FULL pin FAIL
4. K-RARE-BUNDLE / APPLY / NESTED — ultra→ge3 wire HOLD
5. K-GS-FACTCHECK — 젠스파크 대체로 PASS · 복귀HEAD 53decde 정정
6. K-IMPROVE-ROADMAP — I1+I3 권고 · ultra HOLD
7. K-PIN-GAP-DIAG-REVIEW — 지시서 구조 불일치 3건 DOC (본 패킷)

■ 로드맵 선택지 (형)
A = I1+I3 GO (수정된 pin갭진단 + B1로그)
B = B2 mild survey
C = pin 회복 패치 시도 (진단 전 비권고)
D = 중기만 (볼/Brier 등)
권고: A · 단 I1은 위 수정3건 반영본

■ 절대 금지
random.choices · _get_draws_before · boost상한 · kweon쓰기
engine/coordinator wire(GO없이) · FINDINGS무단 · FAIL→auto-tune · 1~3군기록

■ 젠스파크 할 일 (압축 복귀 후)
1. EXTERNAL_START.md + 이 블록으로 상태 확인
2. 수정3건 반영한 K-PIN-GAP-DIAG 지시서 재작성(또는 형에게 확인 질문 1개)
3. GO 없이 코드·백테·wire 금지
4. 첫줄: [복귀] HEAD=<EXTERNAL_START실측> · 지금=K-PIN-GAP-DIAG-REVIEW · 다음=수정GO/형선택
```

---

## 5. 언어 규칙 (Cursor × 형 · 2026-07-30)

- **형이 읽는 모든 보고서·STATUS·UI 문구 = 한국어** (초보 친화). 코드·JSON 필드명만 영어.
- 영어 약어는 **한국어(괄호)** — 예: ge3(3개 이상 적중률) · repack(몰아주기) · p(유의확률).
- 용어表 SSOT: `REPORT_STYLE.md` · `reports/BENCH_REPORT_TEMPLATE.md` §용어表.
- 형의 **긍정 결과**(예: REPACK 3등 1회)는 복습·STATUS에 반드시 명시.
