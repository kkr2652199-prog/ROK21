# PINNED_BASELINE — K-Z~K-AG 완료분 고정

📅 핀 시각: 2026-07-27 KST  
📌 **BASELINE_PIN:** `640cb67` (이 커밋 이후 본선만 진행 · 인프라 재작업 금지)  
📌 SSOT=`kkr2652199-prog/ROK21` · `D:\ROK21` · 포트 7021 · kweon `264de3c` 동결

> 이 문서는 **완료 스택 고정**용이다. OPEN 결함 일괄 패치 목록이 아니다.

---

## 1) 불변 (핀 이후에도 유지)

| 항목 | 값 |
|------|-----|
| 테스트로또 구조 | **3예측 + 4보조** (stat/markov/review + miss/pattern/balance/referee) |
| 학습 컷오프 | **CUTOFF 기본 ON** · `set_learn_as_of` 필수 |
| 발권 dedup | **ROK21_DEDUP 기본 ON** · E[k]=100 |
| 평가 축 | **적중↑ 폐기** · 명분=WARRANT · 수치=benchmarks JSON |
| 동결 | `random.choices` · `_get_draws_before` · boost 상한 |
| 1~3군 | **미접촉** · kweon 미접촉 |

---

## 2) 완료 스택 (PATCHED · 벤치 근거)

| ID | 요지 | 벤치/근거 |
|----|------|-----------|
| K-Z | C(45,6) 이론상수 | `docs/benchmarks/20260727_KZ_theory_constants.json` |
| K-AA | AC8·합138·consec PMF·명분복귀 | `docs/benchmarks/20260727_KAA_apply_verify.json` |
| K-AB | 회차갭 hyodo 정합 | `docs/benchmarks/20260727_KAB_draw_gap.json` |
| K-06/07 | 팬아웃 영구화·갭해소 | KAE/KAF JSON |
| K-AC/AD/AE | 룰·훅·복귀·§6 | drafts 이력 · `rok21_inject.py` |
| K-AF | 팬아웃 잔여정합 | `docs/benchmarks/20260727_KAF_fanout_followup.json` |
| K-AG | pair÷32·LMH zone·3키 배선 | `docs/benchmarks/20260727_KAG_pair_zone_learnkeys.json` |
| K-S/V | as_of·dedup 선결 | KV/KAE 회귀 |

---

## 3) 핀 직전 검증 (2026-07-27 실측 · K-PIN-CLOSE 갱신)

| 게이트 | 결과 | 출처 |
|--------|------|------|
| K-PIN-CLOSE verify_pass | **true** | `20260727_KPIN_CLOSE.json` |
| drift n_issues | **0** | `20260727_KAC_doc_drift.json` |
| 3DB MAX | **1234/1234/1234** · mismatch **0** | `20260727_PIN_3db_smoke.json` |
| K-AG verify_pass | **true** · E[k]=100 | `_kag_pair_zone_verify.py` |
| K-AF verify_pass | **true** | `20260727_KAF_fanout_followup.json` |

---

## 4) 다음 본선 (형 1개만 선택)

| ID | 내용 |
|----|------|
| **P1** | UI 쓸모 — 명분·제약·학습키 (**완료 K-P1**) |
| **P2** | 기각뇌 정책 — 제거 금지·표시 (**완료 K-P2**) |
| **P3** | K-X review 끝수 — 형 승인 후 교정 (**완료 K-P3**) |
| **P4** | hyodo LSTM 샌드박스 (**완료 K-P4**) |
| **P5** | hyodo LSTM·인프라 UI (**완료 K-P5**) |

NEXT: `K-AWAIT` — 형 다음 본선 1건 지시 대기.

---

## 5) 복귀 큐

```
동생, EXTERNAL_START.md(또는 이 PINNED_BASELINE) 읽고 시작해.
```

HEAD는 `git rev-parse --short HEAD` 실측. 문서 HEAD는 1커밋 지연 가능.
