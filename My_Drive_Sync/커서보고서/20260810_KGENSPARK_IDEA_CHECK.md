# K-GENSPARK-IDEA-CHECK

📅 2026-08-10 KST · **READ-ONLY** · wire=False · DB쓰기=없음  
도구: `tools/_k_genspark_idea_check.py` · HEAD 작업 후 push

형/젠스파크 붙여넣기용. 아래 JSON 블록이 지시서 스키마 대응.

---

## check1_result

```json
{
  "early_noise_range_ok": false,
  "seed_sensitivity": {
    "seed_0": true,
    "seed_42": true,
    "seed_123": true,
    "seed_999": true,
    "seed_7": true
  },
  "consistent_neg_as_gate_opinion": "조건부",
  "reason": "cand early 부호는 seed 5/5 전부 음수·consistent_neg=True(안정). early SE≈0.009(n=45)라 ±0.03 단순 룰만으로 부호반전을 noise라 단정하긴 어렵고(|base→cand|Δ≈0.038>0.03). 다만 base early 양수는 다른 SCORE_WEIGHTS 대비 결과라 '신호 증명'으로 과장 금지. → consistent_neg는 다seed 보조조건으로 동의, 단독 하드게이트는 비동의."
}
```

| seed | early | consistent_neg |
|-----:|------:|:--------------:|
| 0 | −0.0216 | True |
| 42 | −0.0115 | True |
| 123 | −0.0439 | True |
| 999 | −0.0269 | True |
| 7 | −0.0283 | True |

(위 `seed_sensitivity` bool = early_neg)

---

## check2_result

```json
{
  "w_crowd_w_struct_separated_now": false,
  "blend_strength_per_brain": false,
  "separation_feasible": true,
  "modification_scope": "crowd_signal.py에 BY_BRAIN dict + prefer/prize/blend 인자화 (1파일+호출 2곳). coordinator/random.choices 불필요",
  "opinion": "지금 BLEND_STRENGTH 단일 노브로 충분. 뇌별 W 분리는 BLEND PASS 후 2단계. n136에서 노브 동시스윕은 선택편향 위험."
}
```

실측 상수: `W_CROWD=0.70` · `W_STRUCT=0.30` · `BLEND_STRENGTH=0.55` (**3뇌 공유**)

---

## check3_result

```json
{
  "evolve_log_weight_nonzero": false,
  "stat_weight_applied_values": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
  "feedback_connected": false,
  "referee_weights_live": {"stat": 0.333333, "markov": 0.333333, "review": 0.333333},
  "opinion": "stat 내부 튜닝 지금 금지. weight_applied 상수 0.0(Phase1). referee 완전 균등(spread=0, K-M 유지). routes에 apply_feedback 없음(K-K OPEN). coordinator WF 경로에만 존재."
}
```

- 테이블: `testlotto_evolve_log` n=60 · `WEIGHT_APPLIED=0.0` 고정

---

## check4_result

```json
{
  "gate_cond1_pass": true,
  "gate_cond2_pass": true,
  "gate_cond3_pass": true,
  "split_half_n_ok": true,
  "cond3_threshold_suggestion": 0.01,
  "additional_gate_suggestion": "다seed(≥3) consistent_neg≥2/3 · prefer 다seed 평균>0 · |Δprize|≥0.01",
  "idea_classify": {
    "immediate": [
      "CHECK-1_consistent_neg_as_soft_aux_multiseed",
      "CHECK-2_single_BLEND_STRENGTH_first",
      "CHECK-3_block_stat_tune_until_feedback_alive",
      "CHECK-4_EV_prefer_gate_no_ge3"
    ],
    "hold": [
      "CHECK-1_consistent_neg_sole_hard_gate",
      "CHECK-2_per_brain_W_CROWD_W_STRUCT",
      "CHECK-3_stat_engine_knob_tune_now",
      "CHECK-4_period_neg_without_multiseed"
    ]
  },
  "final_opinion": "cand_A는 조건1·2·3 통과·split n=68/68 OK·다seed cn_rate=1.0. BLEND 게이트 채택 가능. consistent_neg는 다seed 보조. 뇌별 W·stat튜닝 HOLD."
}
```

split-half(seed42): prefer 전반 **+0.2509** / 후반 **+0.2479** (둘 다 +)

---

## 커서 종합 의견 (젠스파크 합산용)

1. **consistent_neg**: 이번 cand에서 seed 5/5 안정 → **소프트·다seed 보조 동의**. 단독 하드게이트는 과신.
2. **W_CROWD/STRUCT 뇌별**: 코드상 **미분리·분리 가능**. 지금은 **BLEND_STRENGTH 단일**이 맞음.
3. **stat 피드백**: weight=0 · referee 균등 · 클릭 feedback 미연결 → **stat 튜닝 HOLD** (K-M/K-N/K-K 선해소).
4. **BLEND 게이트 3조건**: cand_A 기준 **통과**. ge3 금지 유지. 임계 |Δ|≥**0.01** + 다seed 권고.

**즉시 BLEND 지시서에 넣을 것:** 단일 `BLEND_STRENGTH` 스윕 + EV/prefer 게이트(+다seed consistent_neg 보조).  
**HOLD:** 뇌별 W 분리 · stat 엔진 튜닝 · consistent_neg 단독 필수.
