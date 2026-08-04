# 대폭 개선 조사 로드맵 · 리스크 · 최선 선택 논의

HEAD `192da71` · 2026-08-04 · READ-ONLY 보고(코드 wire 없음)  
Canvas: `rok21-improvement-roadmap.canvas.tsx`  
근거: `docs/benchmarks/20260803_KFUTURE_WIRE_*.json` · K-RARE-* · K-BENCH-NULL · WARRANT · BENCH_PROTOCOL · FINDINGS

---

## 0. 한 줄 권고

**지금 대폭 조사가 필요한 1순위는 「극소번들 강제」가 아니라 live 엔진의 pin갭·FULL 붕괴 진단(I1)이다.**  
위험 없는 **B1(1D feature 로그)** 는 병행. ultra→ge3 wire는 **계속 HOLD**.

---

## 1. 지금까지의 지도 (끝난 것 / 구멍)

### 1.1 완료·정합 (인프라·수학)

| 축 | 결과 |
|----|------|
| UI 즉시·프리로드 | DONE · DB 백테 즉시 표시 |
| eval_mode null | DONE · best15 허위 PASS 제거 |
| FUTURE-WIRE | n100 ge3=**0.1500** PASS · live |
| rare catalog/API | 213/183 · 관측 레이어 |
| NESTED·적용분석 | 구조희귀≠당첨P · 역이용 설계 |
| 젠스파크 팩트체크 | 대체로 PASS · HEAD 정정 |

### 1.2 미해소 구멍 (성적·평가)

| 구멍 | 수치 SSOT | 심각도 |
|------|-----------|--------|
| FULL pin 미달 | ge3 **0.1184** vs pin **0.1447** (Δ**−0.0263**) | **대폭** |
| 소표본 붕괴 | n100 0.150 → FULL 0.1184 (Δ**−0.0316**) | **대폭** |
| mean≈null | FULL mean **1.691** ≈ best5 null **1.729** | 중 |
| quota 고착 | markov **80%** / stat **0%** | 중 |
| SELECT-FULL | combined 0.1218 FAIL · wire HOLD | 중 |
| 볼/Brier 부재 | K-O·K-S 미이행 | 중기 대폭 |
| K-M/N HOLD | referee·best 학습 | 구조 |

---

## 2. 대폭 개선을 위해 **해야 할 조사 작업**

| ID | 작업 | 산출물 | 선행 |
|----|------|--------|------|
| **I1** | pin갭 진단 survey | 기간·뇌기여·쿼터·seed 분해 JSON+보고서 | READ-ONLY WF |
| **I2** | FULL-first 게이트 문서/도구 | n100 단독 PASS→wire 금지 명문화 | I1과 병행 가능 |
| **I3** | B1 1D feature 로그 (가중 **0**) | draw별 max_run·parity·zone·rarity DB/로그 | 최저위험 |
| **I4** | B2 mild-consec+balance λ survey | QUICK→FULL ge3 vs null | I3 권장 |
| **I5** | covering select (B3) | Cover@t · ge3 병기 · eval_mode null | 중위험 |
| **I6** | 볼단위·Brier·calibration 설계 | K-S 승인용 스펙 | 형 승인 |
| **I7** | quota/stat0% 해소 A/B | pin과 직교 가설 검증 | I1 결과 후 |
| **X** | ultra→ge3 wire | — | **기각 유지** |

---

## 3. 리스크 점검

| 리스크 | 발생 시 | 등급 | 대응 |
|--------|---------|------|------|
| 소표본 착시 | n100 PASS로 wire | **고** | I2 · FULL 필수 |
| 단위 혼동 | best15 vs null5 | 중(완화됨) | null_for_eval_mode 유지 |
| 과배제 | 극소/패턴 강제 | **고** | ultra HOLD · λ만 |
| 목적 혼동 | EV/Cover를 ge3로 채점 | 중 | 게이트 분리 |
| 동결 위반 | random.choices·boost | **치명** | 패치 범위 명시 |
| 진단 전 패치 | pin「느낌」수정 | **고** | I1 선행 |
| HEAD 문서 지연 | 외부AI 오복귀 | 저 | ls-remote |

---

## 4. 외부 벤치마킹 → 아이디어

| 출처 | 배울 점 | ROK21 제시 |
|------|---------|------------|
| Walk-forward / WFE (betting·quant) | 튜닝은 train fold 안 · 폴드 drift | **I2** FULL-first · 기간표 필수 |
| Brier·calibration (스포츠예측) | hit-rate만으로 모델 선택 금지 | **I6** 볼/세트 확률 점수 |
| arXiv:2307.12430 covering | t적중 최소 장수 | **I5** cover_select |
| JRSS / JDM / Significance | 인기 조합=공유 EV↓ | rare_behavior UX (ge3 제외) |
| LotteryCodex · NESTED | 구조 빈도≠개별 P | **I3/I4** mild not ultra |
| StatLotto NN · LSTM ROI | OOS→random | pin 미달=정직 HOLD |
| YouTube 「AI 로또」 | 회고·단위 미공개 | **벤치 금지 사례** |

---

## 5. 최선 선택 논의 (권고안)

### 왜 I1이 1순위인가
- live FUTURE-WIRE가 **이미 pin FAIL·FULL 붕괴** — 사용자 성적의 본체.
- rare/NESTED는 수학적으로 **적중 부스터가 아님** — 대폭 wire 대상 아님.
- 원인(쿼터 고착·기간 early 0.099·seed·AUX)을 모르면 B2/covering도 노이즈.

### 권고 패키지

| Phase | 내용 | GO |
|-------|------|-----|
| **0 (지금)** | **I1** pin갭 진단 + **I3** B1 로그 병행 | **권고 GO** |
| **1** | I2 게이트 명문화 · (원인 시) I7 또는 I4 λ만 QUICK→FULL | I1 후 |
| **2** | I5 covering · I6 볼/Brier 설계 | 중기 |

### 형 선택지
- **A)** I1+I3 GO ← **최선**  
- **B)** B2만 즉시 survey (가능하나 원인 없이 λ 낭비 위험)  
- **C)** pin 바로 패치 (진단 전 — **비권고**)  
- **D)** covering/Brier만 설계 문서 (성적 구멍 방치)

---

## 6. 성공 정의 (조사 단계)

| 단계 | 성공 |
|------|------|
| I1 | 「왜 0.1184인가」1~3 가설을 수치로 기각/채택 |
| I3 | feature 테이블/로그 n≥200 · 예측 불변 증명 |
| I4 | ge3≥null AND FULL 비악화 · 아니면 HOLD |
| 전체 | pin(0.1447) 근접 **또는** 정직히 「random 근접」문서화 |

---

## 7. 금지 (재확인)

- ultra rare → ge3 wire  
- n100/QUICK 단독 wire  
- `random.choices` · `_get_draws_before` · boost 상한  
- kweon 원본 쓰기  
- 1~3군 STATUS 혼입  

---

*당첨 보장 없음 · 수치는 JSON/DB만*
