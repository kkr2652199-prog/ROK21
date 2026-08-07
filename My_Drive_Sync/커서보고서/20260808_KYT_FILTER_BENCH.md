# K-YT-FILTER-BENCH — 유튜브 필터/LSTM vs 테스트로또 실측

📅 2026-08-08 KST · **DOC_SURVEY** · wire=**False** · 수치 SSOT=`20260808_KYT_FILTER_BENCH.json`

---

## 0) 한 줄

과거 유튜브(Gemini 다중필터 생성기 · LSTM 예측)를 ROK21 `lotto_testlotto.db`로 재실측했다. 필터는 **당첨P↑가 아니라 조합 프로파일(=null 근처 질량)** 이며, LSTM 시퀀스 예측은 기각 유지. 2026-08 벤치 포인트는 바이브 생성기 복제가 아니라 **annotate/warrant/structure 진단축**이다.

---

## 1) 앱 구조 (testlotto SSOT)

| 역할 | 경로 |
|------|------|
| 엔트리 | `app/main_v13.py` · 포트 **7021** |
| API | `app/testlotto/routes.py` `/api/testlotto` |
| 예측 | `brains/coordinator.py` — **3예측+4보조** |
| DB | `data/lotto_testlotto.db` |
| 컨닝방지 | `data_service._get_draws_before(T)` = draw_no < T |
| 벤치 | `tools/_k_*` → `docs/benchmarks/*.json` |

흐름: draws → coordinator → aux/quota → predictions → walkforward/bench.

---

## 2) 영상 소스

| ID | URL | 요지 |
|----|-----|------|
| YT1 | https://youtu.be/T7I3hEfQBlc | 다중필터(합·홀짝·고저·연번·이월·끝수)+균형/핫/콜드 · Gemini 2.5 Pro 딥리서치 |
| YT2 | https://youtu.be/3G3zExNItj0 | LSTM 로또예측 무효 · train만 당첨·val/test≈일상 · 독립시행 |

---

## 3) DB 실측 (전구간 / 최근100)

- MAX draw = **1235** · n_full=**1235** · n_tail=**100**
- null = MC n=200000 seed=42 (균등 C(45,6))

### 3.1 단건 필터 rate

| 필터 | full rate | Δnull | tail100 | null |
|------|-----------|-------|---------|------|
| sum 110–170 | 0.669636 | -0.012559 | 0.74 | 0.682195 |
| sum 100–180 | 0.802429 | -0.015826 | 0.8 | 0.818255 |
| 홀짝 3:3/4:2/2:4 | 0.824291 | +0.011571 | 0.81 | 0.81272 |
| 고저(≤22:>22) 동일군 | 0.805668 | -0.008102 | 0.82 | 0.81377 |
| 연번≥1쌍 | 0.517409 | -0.011091 | 0.5 | 0.5285 (이론 0.528747) |
| 동일끝수≥1 | 0.779757 | -0.009028 | 0.75 | 0.788785 |
| 이월 main6≥1 | 0.613452 | +0.014167 | 0.616162 | 0.599285 |
| 이월(+next bonus) | 0.668558 | — | 0.676768 | — |
| YT AND 프로파일(sum110…) | 0.202429 | -0.007901 | 0.2 | 0.21033 |

- sum mean full=**138.248** (min 48 / max 238)

### 3.2 영상 주장 vs 실측 (교정)

| 영상 주장(요지) | ROK21 실측(full) | 판정 |
|-----------------|------------------|------|
| 합 110–170이 흔함 / 101–180≈80%+ | 110–170=0.669636 · 100–180=0.802429 | 질량대역 OK·null근접 |
| 홀짝 3:3/4:2/2:4가 대다수 | 0.824291 (Δ+0.011571) | 프로파일 필터(예측력≠) |
| 연번 포함≈55% | 0.517409 vs null≈0.5285 | ≈null · '의외로 흔함'은 조합기하 |
| 이월≈42%(보너스포함) | main=0.613452 · +bonus=0.668558 | 정의 민감 · Δnull 작음 |
| 동일끝수≈77% | 0.779757 (Δ-0.009028) | ≈null · 필터≠엣지 |

---

## 4) ROK21 매핑 (이미 있는 것)

| 영상 축 | ROK21 | 상태 |
|---------|-------|------|
| 합·홀짝·존·연속 | `structure_cover.py` | WIRE **OFF** · HOLD |
| carry / consec 라벨 | `hit_warrant.py` · TRANSITION HIT-WARRANT | 로그전용 · weight=0 |
| carry/ending boost | `stat_brain/predict.py` | 동결 상한 유지 |
| 합/홀짝/연번 analyze | `data_service.analyze_*` | API 통계 |
| 인기(합·연속·생일) | KSIGNAL L4 스펙 | w*=0 진단 |
| LSTM/시퀀스 DL | 레거시 미배선 | **부활 금지**(조코딩과 동일 결론) |

---

## 5) 2026-08 벤치마킹 — 채택 / 기각

### 채택 (분석·진단만 · wire 금지)

1. 다중필터 체크리스트 → **세트 annotate / warrant / structure mass** 진단축으로 재사용
2. Gemini 딥리서치 숫자 → **우리 DB+null**로 교정하는 워크플로(이미 `_k_*` 우위)
3. 균형/핫/콜드 모드 → brain·quota **성향 라벨 문서화**만 (발권 강제 아님)
4. 조코딩 교훈 → train 과적합·독립시행 → BENCH_PROTOCOL null/WF 유지

### 기각

1. 바이브코딩으로 새 '지능형 생성기' 재작성
2. LSTM/시퀀스 DL 예측 경로 부활
3. 필터 AND를 live 5장 강제 (발권가중·WIRE)
4. '당첨 확률↑' 마케팅 문구 차용

### 2026 AI 업그레이드 각도

- 모델이 좋아져도 **독립시행+등확률** 전제는 안 바뀜 → LLM은 예측기가 아니라 **postmortem·warrant 설명·taxonomy 스키마**에 쓰는 편이 ROK21과 맞음.
- 영상1 프로파일은 KSIGNAL L1/L4 · STRUCTURE_COVER와 겹침 → **신규 wire 후보 아님**, 기존 HOLD/DOC 트랙의 외부 근거 보강용.

---

## 6) 판정

- verdict: **DOC_SURVEY**
- pass: **True**
- wire: **False** · engine/quota/coordinator 미변경
- 다음: 형 GO 없으면 트랙 정지 유지 · 라벨확장만 별도 지시

---

생성: `tools/_k_yt_filter_benchmark_survey.py`
