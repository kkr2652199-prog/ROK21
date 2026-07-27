# STATUS_LATEST.md — ROK21 현재 상태

📅 최종 갱신: 2026-07-27 KST  
📌 사유: K-AC 압축대비 룰 현황·RESTORE 보강

---

## 0) 정체

| 항목 | 값 |
|------|-----|
| SSOT | `kkr2652199-prog/ROK21` · **7021** |
| kweon | `264de3c` 동결 |
| 문서원본 | 수치=benchmarks · 결함=FINDINGS · 라벨=WARRANT |

---

## 1) K-AC 요지

| 항목 | 결과 |
|------|------|
| rules | alwaysApply 2개 (core · drive-sync) |
| hooks | boot 주입 확인 · path/stop 발동횟수 모름 |
| R28 | **매턴 ✅3줄 미수행** (자인) |
| RESTORE | C/E/F/B 보정 · drift **0** |
| RULES/CURSOR | **초안만** (형 승인 대기) |

> 이 작업은 예측력과 무관하다. 압축으로 인한 방향 상실 방지다.

---

## 2) OPEN / PATCHED

K-AC OPEN · K-AB·07·AA·Z·V·S PATCHED · K-06 OPEN · K-M/N HOLD

---

## 3) 다음 (형)

1. RULES_FIXED R35·R36 · CURSOR_RULES §6 초안 **승인/반영**  
2. K-06 팬아웃 구현 승인  
3. pair/30·zone · 미소비 키
