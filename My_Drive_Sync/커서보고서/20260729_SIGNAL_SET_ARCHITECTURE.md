# 신호셋트 아키텍처 논의 — 형 제안 + 커서×젠스파크 합의

📅 2026-07-29 23:40 KST · **문서+조사+GenSpark 협의** · coordinator/predict_statistical **미수정**  
📌 HEAD 실측: `bcaf29b` · K-WINDOW-SIGNAL-01 **running** (900/1182 @ check time)

---

## 1) Executive summary

| 항목 | 결론 |
|------|------|
| 형 제안 (5→10세트, 신호셋트 5) | **조건부 찬성** — pool 확장 OK, **선별 기준 survey 선행** 필수 |
| 4보조 역할 | Tier2 **신호 채널** 재정의 찬성 — 보조별 개별 검증 후 |
| 신호셋트 구성 | **통합 5개** (markov 52.5% 비율 반영) > 뇌별 1개씩 |
| QUICK_GATE | n=200 **tail-200** (draw 1035~1234) · PASS 완화 p<0.15 |
| coordinator wire | **형 GO 전 금지** — 오늘 WIRE 전축 FAIL 실적 |

---

## 2) 형(오빠) 제안 원문

1. 각 뇌(3+4) **5세트 → 10세트** 확장  
2. 10세트 중 **신호를 잘 받는** 세트 **1~2개** 선별  
3. 선별 번호를 **「신호셋트」** 5세트(셋트1~5)로 이관  
4. 전체 신호 프레임을 **다른 각도/티어**로 재편  
5. 인터넷·논문·YouTube 등 벤치마크 아이디어 수입

---

## 3) 커서 비보수적 의견

### 3.1 10세트 확장 — pool_cover↑, ge3는 선별에 달림

- K-BENCH-01: **쿼터 갭 43.6%** (516/1182) — 15장 중 best가 발권 5장 best보다 나은 경우  
- 10세트 확장 → 풀 안에 "더 좋은 장" 확률 ↑  
- **단** WIRE-V2 `set_no_asc` 그대로면 ge3 **불변** (K-BENCH-02 실증: AUX/confidence 정렬 ge3=0.099~0.102)  
- **핵심 레버 = 신호셋트 선별 기준**, pool 크기 아님

### 3.2 신호셋트 선별 3축 (Cursor 제안)

| 축 | 정의 | 우선순위 |
|----|------|----------|
| **(b) window hint overlap** | hint 번호 집합 ∩ 세트 번호 / 6 | **1순위** — K-WINDOW JSON 연동 |
| **(a) draw_features bin 일치** | ge3+ bin(sum/odd/AC)과 세트 구조 일치율 | 2순위 — K-BENCH-01 JSON 확장 |
| **(c) Jaccard 다양성** | 세트 간 번호 겹침 최소화 | 3순위 — pool_cover 보조 |

**금지:** AUX score (ρ≈0, p=0.973) — 채점 축 폐기

### 3.3 신호 티어 프레임 (Tier0~4)

```
Tier0  무작위성 전제     — KCI/APJCRI 6/45 (24가설 중 23 채택)
Tier1  구조 필터         — tier1_filter (합·홀짝·구간·연속) · 1군=ROK21 동일
Tier2  신호 채널         — 4보조 → window/recency/miss/draw_features hint
Tier3  신호셋트          — 10세트 pool → overlap 선별 → 5셋트
Tier4  발권              — WIRE-V2 set_no_asc (pin ge3=0.1447 stored)
```

**비전:** Tier2+3는 **중간 레이어**. Tier4 발권은 pin 유지, Tier3 출력이 Tier4 **입력 pool**을 대체/보강.

### 3.4 1군 이식 + QUICK_GATE

| P | 항목 | 출처 |
|---|------|------|
| P0 | QUICK_GATE n=200 tail | `20260729_MONEY1GUN_BENCH_INVENTORY.md` §C |
| P0 | deterministic_sets lab | predict 동결 밖 top-k |
| P1 | lead1 F1_V2_STRICT vs WIRE-V2 | READ-ONLY compare |
| P1 | postmortem signal | K-BENCH-01 연계 |

### 3.5 Cursor만의 공격적 아이디어

1. **앙상블 힌트 게이트:** E1 miss_pattern(p=0.042) + K-WINDOW window — **동시 충족 draw** subset에서 ge3_rate 재계산  
2. **1군 hyena식 consensus:** 25→10 pool union → covering score (5005 C(15,6) 아이디어, survey-only)  
3. **Position/slot bias:** Israeli lottery 800M picks — **폼 위치 편향**은 당첨 draw가 아닌 **구매자 편향**; Tier2 "역신호" 필터 후보  
4. **10세트 = pseudo-wheel:** covering design (v,k,t) — **커버리지 보장 ≠ 예측**이지만 pool 다양성 명분

---

## 4) 웹·학술 조사 ( hype 제외)

| 출처 | 핵심 | ROK21 적용 |
|------|------|------------|
| [APJCRI 2025 — 6/45 시계열](https://doi.org/10.47116/apjcri.2025.02.43) | χ²·ANOVA·Benford — **23/24 무작위 채택** | Tier0 근거 · 번호 예측 기각 |
| [KJAS 2025 — 로또 공정성](https://doi.org/10.5351/kjas.2025.38.1.089) | 구매자 **비랜덤 선택** vs draw 무작위 | Tier2 ≠ 당첨 예측, 구조 필터 |
| [JRSS Combination Preference 2011](https://doi.org/10.1111/j.1467-985x.2011.00693.x) | 조합 클러스터 선호 모델 | tier1_filter·조합 분포 |
| [Israeli lottery spatial 2021](https://dlab.sauder.ubc.ca/sjdm/journal/21/210322/jdm210322.pdf) | 티켓 **위치·행 편향** (800M+) | UI/역필터 아이디어 (draw 무관) |
| [Lottery wheel / covering design](https://en.wikipedia.org/wiki/Lottery_wheeling) | (v,k,t)-covering — **필터 시 guarantee 파괴** | 10세트 pool 다양성 참고만 |
| [ELJC lotto design](https://www.combinatorics.org/ojs/index.php/eljc/article/download/v19i3p28/pdf/) | 조합 설계 이론 | wheel 수학 배경 |

**YouTube/블로그:** hot/cold·갭 전략 — 대부분 n<500·p>0.27 → **Tier2 후보에서 기각** (AUX_SIGNAL_PIVOT §4.1)

---

## 5) 젠스파크 3라운드 협의 요약

### R1 — 10→신호셋트

> **「10→신호셋트 5 구조 — 조건부 찬성」**  
> pool 43.6% 갭 해소 가능. **선별 기준 없으면 연산만 증가.**  
> SETS_PER_BRAIN 5→10 = coordinator 수정 → **survey 선행.**

> **선별 1순위: (b) window hint overlap** — K-WINDOW JSON으로 즉시 검증.

> **E1 연결:** PASS면 overlap 상위 → 신호셋트. FAIL+p<0.1이면 miss_pattern 앙상블.

### R2 — Tier / QUICK_GATE

> **「4보조 Tier2 신호 채널 — 찬성, 보조별 개별 검증 조건」**  
> E1은 miss만. pattern/balance/referee는 미검증.

> **「신호셋트 — 통합 5개 추천」**  
> markov 52.5% / stat 30% / review 17.5% — 뇌별 1개 고정은 review 슬롯 낭비.

> **「QUICK_GATE n=200 — 조건부 OK」**  
> tail-200 (1035~1234) · PASS: ge3>0.1218 AND p<0.15 · full은 PASS variant만.

### R3 — 구현 순서 합의

> **「합의해요. 단 1개 수정 제안이에요.」**  
> K-QUICK-GATE-01은 **K-SIGNAL-SELECT-01 결과 반영 후** 설계 — 선별 기준·window 크기 모르고 QUICK_GATE 먼저 돌리면 스크리닝 대상 결정 불가.

> **「보고서에 이 순서 그대로 넣어줘요. K-WINDOW 결과 나오면 바로 공유해줘요.」**

---

## 6) 3자 합의 — 권장 구현 순서

| # | ID | 내용 | wire |
|---|-----|------|------|
| 1 | **K-WINDOW-SIGNAL-01** | full survey 완료 대기 (kill 금지) | ❌ running |
| 2 | **K-SIGNAL-SELECT-01** | overlap + draw_features bin 선별 READ-ONLY | ❌ |
| 3 | **K-QUICK-GATE-01** | BENCH §9 + tail-200 패치 | ❌ |
| 4 | **K-DET-LAB-01** | 1군 deterministic_sets lab copy | ❌ |
| 5 | **K-10SET-SURVEY-01** | 10세트 pool QUICK_GATE wrapper | ❌ |
| 6 | **K-SIGNAL-SET-SPEC** | 신호셋트 5 spec · Tier 프레임 문서 | ❌ |
| 7 | *(형 GO)* | coordinator · SETS_PER_BRAIN wire | ⛔ HOLD |

**공통 금지:** `predict_statistical.py` random.choices · coordinator live wire (형 GO 전)

---

## 7) 신호셋트 spec 초안 (survey 설계용)

```yaml
signal_set:
  count: 5
  naming: ["신호셋트1", ..., "신호셋트5"]
  source_pool:
    per_brain_sets: 10          # survey phase only
    brains: [markov, stat, review, miss, pattern, balance, referee]  # 7×10=70 max
  selection:
    method: unified_top5         # not per-brain quota
    score:
      w_overlap: 0.5             # window hint
      w_bin_match: 0.35          # draw_features
      w_diversity: 0.15          # Jaccard vs already picked
    min_per_brain: 0             # no forced review slot
  output:
    feeds: tier4_wire_pool       # replaces 15-set pool input (GO 후)
  validation:
    quick_gate: {n: 200, range: [1035, 1234], pass: "ge3>0.1218 & p<0.15"}
    full: {n: 1182, pass: "ge3>0.1447 & p<0.05"}
```

---

## 8) K-WINDOW-SIGNAL-01 상태

| 항목 | 값 |
|------|-----|
| 상태 | **running** (kill 금지) |
| 진행 | **900/1182** (~76%) @ 2026-07-29 23:38 KST |
| variants | 61 · seed=42 |
| pin | ge3=0.1447 · null=0.1137 |
| 완료 시 | `docs/benchmarks/20260729_KWINDOW_SIGNAL_survey.json` + `reports/20260729_KWINDOW_SIGNAL_SURVEY.md` auto |

**기대:** 형 LOW — pin 미달 가능. null 대비 p<0.1이면 Step 2 overlap 분석 진행.

---

## 9) 근거 파일

- `reports/20260729_AUX_SIGNAL_PIVOT.md`
- `reports/20260729_MONEY1GUN_BENCH_INVENTORY.md`
- `reports/20260729_KAUX_SIGNAL_SURVEY.md`
- `docs/benchmarks/20260729_KBENCH_POSTMORTEM.json`
- `My_Drive_Sync/SUMMARY/AI_COLLAB.md`

---

*작성: Cursor + GenSpark browser 3-round · coordinator 미수정*
