# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-27 KST  
📌 사유: K-07 testlotto 복구검증 + 테스트로또 정밀정찰(READ-ONLY)

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| 로컬 | `D:\ROK21` · **7021** |
| SSOT | `kkr2652199-prog/ROK21` |
| 원본 | `D:\3kweon` 미접촉 |
| 복원 | `RESTORE.md` |

---

## 1) K-07 (이번 턴)

| 항목 | 값 |
|------|-----|
| 백업 | `backups/20260726_K07복구전/lotto_testlotto.db` |
| testlotto MAX | **1234** (이미 충족 · fetch→None=1235미발표) |
| 1232~1234 공식대조 | **전부 MATCH** |
| predictions 1232~1234 | 각 15행 (stat/markov/review) |
| brain_review MAX | **1234** |
| hyodo MAX | **1231** (미접촉 · OPEN 잔여) |
| lotto4 | read-only · MAX 1234 |

---

## 2) 정밀정찰 요약

| 항목 | 값 |
|------|-----|
| 활성 | 3예측 + 4보조 (coordinator) |
| 클릭 경로 fusion | **없음** |
| AUX 가중 | 하드코딩 0.25×4 |
| referee live | ≈0.335 / 0.332 / 0.334 |
| seed | 미고정 · cache 없으면 비재현 |
| 코드 패치 | **0건** |
| 보고서 | `reports/20260726_테스트로또_정밀정찰.md` |

---

## 3) EV / CUTOFF (이전 확정 유지)

| 플래그 | 기본 |
|--------|------|
| `ROK21_EV_RERANK` | OFF |
| `ROK21_LEARN_CUTOFF` | OFF |
| K-09 | **CLOSED** |

---

## 4) 동결

- `random.choices` · `_get_draws_before` · boost 상한

---

## 5) 다음

1. hyodo 1232~1234 동기화 (형 승인)
2. 정찰 관찰목록 → 형·외부AI가 K-A~ 부여
3. (선택) EV/CUTOFF opt-in 운영시험

---

## 6) 산출물

`reports/20260726_테스트로또_정밀정찰.md`  
`My_Drive_Sync/커서보고서/` 동일 복사
