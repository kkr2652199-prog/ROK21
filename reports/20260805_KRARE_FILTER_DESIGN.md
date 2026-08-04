# K-RARE-FILTER-DESIGN — 극소수 필터 패치 준비 (설계 · wire 금지)

📅 2026-08-05 KST · **DOC** · wire=**False**  
📌 형 의도: 1236 대기 · 컨닝 금지 · 등확률 사실 · 극소수 **군** 분석 · 일괄 패치 금지

---

## 0) 초보용 한 줄

로또 **한 장**의 당첨 확률은 모두 같다(1/814만).  
그래도 814만 안에서는 「6연속」「전부 홀수」처럼 **묶음(군)** 크기가 달라서, 그 묶음은 드물거나 흔하다.  
이 문서는 그 **군을 정의·재고·태그**할 준비만 한다. 발권 스위치는 켜지 않는다.

---

## 1) 형 의도 고정

| 명제 | 취급 |
|------|------|
| 앱 목적 ≠ 미래 100% 맞춤 | 확정 |
| 단일회차 · 티켓별 P = 1/C(45,6) | **100% 사실** |
| 컨닝 불가 (`_get_draws_before` · as_of · 미추첨 1236 미사용) | 동결 유지 |
| 1~1235 실측은 **군 분포 검증 데이터** | 예측 엔진 아님 |
| 당첨 집합 중복 0 | 우주 미덮음 · 「나온번호 제외」≠당첨P↑ |
| λ / structure·pair cover / ultra→ge3 일괄 wire | **금지**(실패 교훈) |

---

## 2) 이중층 아키텍처

1. **진단층 (읽기):** 템플릿 taxonomy · 이론 \(w\) · 실측 대조 · 문헌 · catalog  
2. **정책층 (기본 OFF):** include / exclude / boost — `RARE_ANNOTATE_WIRE=False` · `RARE_POLICY_MODE=off`

```
티켓등확률 → 조합군 w → 군확률 w/8145060 → 1..1235 실측대조
                ↓
         3뇌 후보 → annotate(rare_tags) → policy OFF → 발권 불변
```

---

## 3) 기존 자산 지도

| 자산 | 역할 | 한계 |
|------|------|------|
| `rare_bundle.py` / catalog 213 · ultra 183 | 극소 인스턴스·패턴 v0 | 템플릿 **전수** 아님 |
| `KMATH_PATTERN_WARRANT` | 1~1235 구조 명분 | 발권 필터 아님 |
| `structure_cover` / `pair_cover` | covering 실험 | ge3↓ **HOLD** |
| `feature_lambda` | 특성 λ | full/tail 기각 **OFF** |
| AUTO S0~S4 | 예측→채점 운송벨트 | rare와 독립 |

---

## 4) 문헌 시드

| ID | 내용 |
|----|------|
| arXiv:math/0507469 | 연속번호 확률 (6/49) |
| arXiv:1001.2972 | SuperEnalotto consecutive |
| arXiv:2307.12430 | UK covering 27장 (t보장 ≠ 1등P↑) |
| arXiv:2408.06857 | Mandel combinatorial condensation |
| LotteryCodex | composition / sum distribution (군빈도 교육) |
| 내부 | WARRANT · K-RARE-BUNDLE · 본 DESIGN |

---

## 5) 단계 (R0~R4)

| Step | ID | 상태 |
|------|-----|------|
| R0 | K-RARE-FILTER-DESIGN | **본 문서** |
| R1 | K-RARE-TEMPLATE-TAXONOMY | 동팩 |
| R2 | K-RARE-MEASURE-1_1235 | 동팩 측정 |
| R3 | K-RARE-TAG-SPEC | 동팩 · stub `rare_annotate.py` · signal_pool 주석 |
| R4 | 정책 wire + QUICK | **형 GO 전 금지** |

---

## 6) 비목표

- 당첨확률↑ 약속 · best학습 · 동결 토큰 변조 · kweon 접촉 · 1236 사전 사용  
- covering/λ 재wire · 일괄 정책 ON  

성공(준비): 극소군 **정의·열거·가중·실측·태그스키마·삽입점** 문서화. ge3↑ 비약속.

---

## 7) 나중 wire 게이트

G0 형 GO · G1 플래그 기본 0 · G2 QUICK n200 · G3 FULL 붕괴 금지 · G4 동결 diff · G5 「당첨P↑」클레임 금지

---

## 8) 관련 파일

- `reports/20260805_KRARE_FILTER_DESIGN.md` (본문)
- `docs/benchmarks/20260805_KRARE_FILTER_DESIGN.json`
- `reports/20260805_KRARE_TEMPLATE_TAXONOMY.md`
- `docs/benchmarks/20260805_KRARE_MEASURE_1_1235.json`
- `reports/20260805_KRARE_TAG_SPEC.md`
- `app/testlotto/rare_annotate.py` (WIRE=False)
- `app/testlotto/signal_pool.py` (삽입점 주석만)

판정: **DOC · PASS(준비)** · wire 없음
