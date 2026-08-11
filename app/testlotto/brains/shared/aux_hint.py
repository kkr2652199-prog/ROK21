"""shared.aux_hint — 생성 전 aux hint 가중치 조정 유틸.

각 뇌의 engine.generate 호출 전,
전용 aux의 score_set을 번호별로 사전 계산해
candidate pool 가중치에 hint로 반영한다.

설계 원칙:
- hint_weight 기본값=0.15 (약한 nudge · 기존 생성 로직 우세 유지)
- score_set 반환 0~1 → 가중치 배율: 1.0 + hint_weight * (score - 0.5)
  (score=0.5 기준 중립 · score>0.5 소폭 상향 · score<0.5 소폭 하향)
- 번호 단위가 아닌 세트 단위 점수이므로
  세트 후보 oversample 후 re-rank에 적용
- 기존 random.choices 라인 수정 금지
  → generate 후 결과 리스트 re-rank 방식으로 구현

K-HINT-WEIGHT-BY-BRAIN: 뇌별 강도 SSOT=`HINT_WEIGHT_BY_BRAIN`.
"""

from __future__ import annotations

DEFAULT_HINT_WEIGHT: float = 0.15
HINT_WEIGHT_BY_BRAIN: dict[str, float] = {
    "stat": 0.15,
    "markov": 0.15,
    "review": 0.15,
}


def hint_weight_for(brain_tag: str) -> float:
    return float(HINT_WEIGHT_BY_BRAIN.get(brain_tag, DEFAULT_HINT_WEIGHT))


def rerank_by_aux(
    candidates: list[dict],
    draws: list[dict],
    target_draw_no: int,
    aux_module,
    brain_tag: str,
    hint_weight: float | None = None,
) -> list[dict]:
    """generate 결과 리스트를 aux score 기반으로 re-rank.

    candidates: engine.generate 반환 list[dict] (nums/confidence 포함)
    aux_module: score_set(nums, draws, target_draw_no, brain_tag) 인터페이스 보유
    hint_weight: aux 반영 강도 (0=무효·기존동일, 1=완전 aux 우선).
      None 이면 HINT_WEIGHT_BY_BRAIN[brain_tag].
    반환: re-ranked list[dict] (nums·confidence 유지, aux_hint_score 추가)
    """
    if hint_weight is None:
        hint_weight = hint_weight_for(brain_tag)
    if not candidates or hint_weight == 0:
        return candidates

    scored = []
    for c in candidates:
        try:
            aux_s = float(
                aux_module.score_set(
                    c["nums"], draws, target_draw_no, brain_tag=brain_tag
                )
            )
        except Exception:
            aux_s = 0.5
        # confidence 원본 유지. pick_score=aux 반영 정렬키
        # (구버전은 리스트만 재정렬하고 diversity.pick이 confidence만 봐 DEAD_WIRE)
        hint_score = float(c.get("confidence", 60)) * (
            1.0 + hint_weight * (aux_s - 0.5)
        )
        scored.append(
            {
                **c,
                "aux_hint_score": round(aux_s, 4),
                "pick_score": round(hint_score, 6),
            }
        )

    scored.sort(key=lambda x: x["pick_score"], reverse=True)
    return scored
