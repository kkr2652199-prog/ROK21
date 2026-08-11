# 형 → 젠스파크 붙여넣기 — K-F 지시서 재작성 질문

> 커서 팩트체크: `docs/benchmarks/20260811_KF_INSTRUCTION_FACTCHECK.json`  
> SSOT=ROK21 · 양산前 · 1237아님 · ge3 클레임금지

---

## 붙여넣기 블록 (시작)

```
[ROK21 · K-F 지시서 재검토 요청]

상황 (JSON 실측, 채팅기억 불신):
- NEXT 후보에 K-F markov learn 배선이 있음 → 방향성 자체는 OK.
- 그러나 커서 팩트체크 결과 지시서 전제가 틀림 → 그대로 실행하면 안 됨.
  1) LEARN_WIRED 가 이미 True (markov_brain/learn.py)
  2) live 경로(markov_brain.engine)는 이미 apply_learn_boost 호출
  3) 강제리셋 후 learn_state=0행 · adjustments 전부 0 → True/False A/B = noop
  4) FINDINGS K-F가 인용한 predict_flow_shaman 은 DEPRECATED (pool은 markov_brain 사용)
  5) 지시서 판정축=평균적중만 → 현행(K-O/R38, prefer/prize 튜닝)과 충돌 가능

근거파일 (raw fetch):
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260811_KF_INSTRUCTION_FACTCHECK.json
- https://raw.githubusercontent.com/kkr2652199-prog/ROK21/main/docs/benchmarks/20260811_KEVOLVE_FGJ_AUDIT.json

질문 (답만 번호·짧게):
Q1. K-F를 어떻게 재정의할까?
  A) 이미 ON → DOC_CLOSE(오진 정정)만
  B) learn 재료(1137~1236 feedback) 채운 뒤 LEARN_WIRED True vs False A/B
  C) 배선 유지 + boost 값 튜닝(재료 선행)
  D) 다른 정의(서술)

Q2. 판정축은?
  A) markov prefer_delta 1차 + mean_hits 모니터
  B) mean_hits만 (지시서 유지)
  C) ge3 (비권고·이유 필수)
  D) 기타

Q3. 재료 0인 지금 상태에서 True/False 스냅샷을 돌려도 되나?
  A) 금지(무효)
  B) 허용(동일성적=효과없음으로 CLOSE)
  C) 재료 채운 뒤에만

Q4. FINDINGS K-F(OPEN, predict_flow_shaman) 처리?
  A) PATCHED/CLOSED로 정정(live 경로 이미 소비)
  B) OPEN 유지하되 대상을 "재료·효과 검증"으로 문구 변경
  C) 새 ID로 분리

Q5. 다음 실행 순서 추천 1줄 (DB백업 포함 여부·구간·seed 규칙).

제약 재확인: 뇌독립(markov learn만) · random.choices/_get_draws_before/boost상한 동결 · kweon미접촉 · 1237양산아님.
```

## 붙여넣기 블록 (끝)

---

커서는 젠스파크 답 + 형 GO 전까지 **지시서 실행 보류**.
