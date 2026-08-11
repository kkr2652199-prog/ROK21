# K-F 지시서 팩트체크 — **실행 중단 · 재작성 필요**

📅 2026-08-11 KST · 형 「방향 맞으면 진행 / 틀리면 젠스파크 질문」

## 판정
| 항목 | 결과 |
|------|------|
| NEXT 큐에 K-F 있는가 | **예** (후보 목록과 방향 일치) |
| 지시서 그대로 실행 | **아니오 — REJECT_REWRITE** |

## 핵심 실측 (기억 아님)
1. `LEARN_WIRED = True` **이미 ON** (`markov_brain/learn.py`)
2. live pool/발권 경로 = `markov_brain.predict` → `engine` → `apply_learn_boost` **이미 호출**
3. `testlotto_brain_learn_state` **0행** · adjustments **전부 0.0** · evolve **0**  
   → True/False A/B는 **noop** (성적 동일 → 판정 무효)
4. FINDINGS K-F가 가리키는 `predict_flow_shaman` 는 **구·DEPRECATED 경로** (learn 없음)

## 지시서 vs 현실
| 지시서 | 현실 |
|--------|------|
| 현재 LEARN_WIRED=False | **True** |
| 스위치 켜서 반영 | **이미 켜져 있음** (재료 0이라 효과 0) |
| 평균적중만으로 유지/롤백 | K-O/R38과 충돌 가능 · prefer축이 현행 |
| K-F OPEN 닫기 | 닫을 정의를 다시 써야 함 |

## 다음
젠스파크 질문안: `reports/20260811_KF_GENSPARK_QUESTIONS.md`  
JSON: `docs/benchmarks/20260811_KF_INSTRUCTION_FACTCHECK.json`
