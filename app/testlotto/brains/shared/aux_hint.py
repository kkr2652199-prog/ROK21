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
"""

from __future__ import annotations


def rerank_by_aux(
    candidates: list[dict],
    draws: list[dict],
    target_draw_no: int,
    aux_module,
    brain_tag: str,
    hint_weight: float = 0.15,
) -> list[dict]:
    """generate 결과 리스트를 aux score 기반으로 re-rank.

    candidates: engine.generate 반환 list[dict] (nums/confidence 포함)
    aux_module: score_set(nums, draws, target_draw_no, brain_tag) 인터페이스 보유
    hint_weight: aux 반영 강도 (0=무효·기존동일, 1=완전 aux 우선)
    반환: re-ranked list[dict] (nums·confidence 유지, aux_hint_score 추가)
    """
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
        # confidence는 변경 금지 · 정렬용 hint_score만 별도 계산
        hint_score = float(c.get("confidence", 60)) * (
            1.0 + hint_weight * (aux_s - 0.5)
        )
        scored.append({**c, "aux_hint_score": round(aux_s, 4), "_hint_sort": hint_score})

    scored.sort(key=lambda x: x["_hint_sort"], reverse=True)
    # _hint_sort 임시 키 제거
    for s in scored:
        s.pop("_hint_sort", None)
    return scored
