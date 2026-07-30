"""한국어 라벨 — REPORT_STYLE.md §2·§용어表 SSOT (형·UI용)."""

from __future__ import annotations

# ── 과제/설문 ID ──
SURVEY_ID_KO: dict[str, str] = {
    "K-SIGNAL-SELECT-FULL": "신호 선별 전체 검증(1182회)",
    "K-SIGNAL-SELECT-01": "신호 선별 빠른 검증(200회)",
    "K-SIGNAL-REPACK-01": "번호 몰아주기 빠른 검증(200회)",
    "K-SIGNAL-REPACK-FULL": "번호 몰아주기 전체 검증(1182회)",
    "K-SIGNAL-BACKTEST-TAIL100": "신호 백테스트 최근100회",
}

# ── 지표·약어 (REPORT_STYLE §2) ──
METRIC_KO: dict[str, str] = {
    "ge3": "3개 이상 적중률",
    "ge3_rate": "3개 이상 적중률",
    "ge4": "4개 이상 적중률",
    "ge4_rate": "4개 이상 적중률",
    "ge3_cnt": "3개 이상 적중 횟수",
    "mean": "평균 적중 개수",
    "repack": "몰아주기",
    "tier": "등수",
    "r1": "1등 횟수",
    "r2": "2등 횟수",
    "r3": "3등 횟수",
    "r4": "4등 횟수",
    "r5": "5등 횟수",
    "null": "이론 무작위 기준",
    "pin": "현재 고정 기준선",
    "p": "유의확률(p값)",
    "PASS": "통과",
    "FAIL": "실패",
    "gate": "통과 조건",
    "QUICK": "빠른 검증",
    "full": "전체 검증",
    "seed": "난수 시드",
    "n_eval": "평가 회차 수",
    "verdict": "판정",
}

# ── 전략/선별 방식 ──
STRATEGY_KO: dict[str, str] = {
    "signal_repack": "신호 몰아주기",
    "hint_only_repack": "힌트만 몰아주기",
    "random_repack": "무작위 몰아주기",
    "set_no_asc": "세트번호 오름차순",
    "k_signal_select_combined": "통합 선별(몰아주기 비교)",
    "combined": "통합 선별",
    "bin_match": "구간(bin) 일치",
    "jaccard_div": "겹침(Jaccard) 분산",
    "window_overlap": "기간창 겹침",
}

# ── 평가 경로 ──
EVAL_MODE_KO: dict[str, str] = {
    "best_of_15": "15장 중 최고 1장 평가",
    "best_of_5": "5장 중 최고 1장 평가",
    "best_of_5_from_30": "30장→상위 5장 발권",
    "top5_from_15": "15장→상위 5장 발권",
}


def survey_label_ko(survey_id: str) -> str:
    return SURVEY_ID_KO.get(survey_id, survey_id)


def strategy_label_ko(strategy_id: str) -> str:
    return STRATEGY_KO.get(strategy_id, strategy_id)


def metric_label_ko(key: str) -> str:
    return METRIC_KO.get(key, key)


def eval_mode_label_ko(mode: str) -> str:
    return EVAL_MODE_KO.get(mode, mode)


def tier_rank_label(tier_rank: int) -> str:
    labels = {0: "미당첨", 1: "1등", 2: "2등", 3: "3등", 4: "4등", 5: "5등"}
    return labels.get(int(tier_rank), str(tier_rank))
