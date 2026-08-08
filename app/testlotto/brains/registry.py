"""테스트로또 뇌 레지스트리 — 3 미래예측 + 4 보조."""

from __future__ import annotations

PREDICT_BRAINS: list[dict[str, str]] = [
    {
        "tag": "stat",
        "code": "stat_fairy",
        "name": "과거학습",
        "role": "predict",
        "desc": "회차 숙제: 과거 당첨번호 빈도·끝수·이월 패턴 (군중선호와 별개)",
        "short_desc": "N회 숙제=1..(N-1) 당첨번호로 패턴·명분을 쌓는다",
    },
    {
        "tag": "markov",
        "code": "flow_shaman",
        "name": "선호번호",
        "role": "predict",
        "desc": "사람들이 선호하는 번호(1등당첨자 많은 회차·생일대) 축",
        "short_desc": "인기 회차·저번호를 학습해 선호 조합을 잡는다",
    },
    {
        "tag": "review",
        "code": "review_king",
        "name": "금액뇌",
        "role": "predict",
        "desc": "비선호 번호(저당첨자수·고번호)로 당첨 시 몫(금액) 축",
        "short_desc": "사람들이 덜 고르는 쪽으로 당첨금 기댓값을 노린다",
    },
]

AUX_BRAINS: list[dict[str, str]] = [
    {
        "tag": "miss_aux",
        "code": "miss_detective",
        "name": "오답탐정",
        "role": "aux",
        "desc": "과거 오답 패턴 페널티",
        "short_desc": "자주 틀린 패턴을 찾아 경고한다",
    },
    {
        "tag": "pattern_aux",
        "code": "pattern_spotlight",
        "name": "패턴돋보기",
        "role": "aux",
        "desc": "쌍수·연속수·AC값 신호",
        "short_desc": "쌍수·연속수·AC값 신호를 읽는다",
    },
    {
        "tag": "balance_aux",
        "code": "balance_keeper",
        "name": "균형지킴이",
        "role": "aux",
        "desc": "홀짝·고저·구간 쏠림 방지",
        "short_desc": "홀짝·고저·합계 균형을 점검한다",
    },
    {
        "tag": "referee_aux",
        "code": "referee",
        "name": "심판관",
        "role": "aux",
        "desc": "최근 성적 좋은 예측뇌 가중치 배분",
        "short_desc": "세트 간 겹침·쏠림을 최종 판정한다",
    },
]

SETS_PER_PREDICT_BRAIN = 5

METHOD_TO_TAG: dict[str, str] = {
    "과거학습": "stat",
    "통계요정": "stat",  # 구명칭 호환(DB method 잔존)
    "선호번호": "markov",
    "흐름술사": "markov",  # 구명칭 호환
    "금액뇌": "review",
    "복습왕": "review",  # 구명칭 호환
}

DISPLAY_NAMES: dict[str, str] = {b["tag"]: b["name"] for b in PREDICT_BRAINS + AUX_BRAINS}
SHORT_DESCS: dict[str, str] = {b["tag"]: b.get("short_desc", "") for b in PREDICT_BRAINS + AUX_BRAINS}
ALL_BRAINS: list[dict[str, str]] = PREDICT_BRAINS + AUX_BRAINS


def get_brain_meta(tag: str) -> dict[str, str]:
    """뇌 tag → 이름·역할·필살기 한 줄."""
    for b in ALL_BRAINS:
        if b["tag"] == tag:
            return {
                "tag": tag,
                "name": b["name"],
                "role": b["role"],
                "desc": b.get("desc", ""),
                "short_desc": b.get("short_desc", ""),
            }
    return {"tag": tag, "name": DISPLAY_NAMES.get(tag, tag), "role": "", "desc": "", "short_desc": ""}


def get_short_desc(tag: str) -> str:
    return SHORT_DESCS.get(tag, "")
