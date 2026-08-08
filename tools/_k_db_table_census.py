# -*- coding: utf-8 -*-
"""테스트로또 DB 테이블·행수 조사 (READ-ONLY). 리셋 범위 확정 전 확인용."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.models import get_lotto_db, init_testlotto_db  # noqa: E402

# 예측·백테스트 산출물 = 리셋 후보. 원천 데이터(회차·당첨정보)는 제외 대상.
PREDICT_ARTIFACTS = {
    "lotto_predictions",
    "lotto_analysis",
    "testlotto_brain_review",
    "testlotto_brain_learn_state",
    "testlotto_brain_weights",
    "testlotto_backtest_runs",
    "testlotto_backtest_draw_results",
    "testlotto_pool_view_cache",
    "testlotto_evolve_log",
    "testlotto_evolve_auto_state",
    "testlotto_rare_bundle_hits",
    "hit_warrant_log",
    "transition_log",
}
SOURCE_DATA = {
    "lotto_draws",
    "testlotto_draw_features",
    "testlotto_draw_prize_tiers",
    "testlotto_draw_detail",
    "testlotto_draw_win_stores",
    "testlotto_rare_bundle_catalog",
    "testlotto_brain_page",
}


def main() -> None:
    init_testlotto_db()
    conn = get_lotto_db()
    tabs = [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]
    print(f"{'행수':>10}  {'분류':<8}  테이블")
    print("-" * 60)
    tot_art = 0
    for t in tabs:
        n = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        if t in PREDICT_ARTIFACTS:
            kind, tot_art = "예측산출", tot_art + n
        elif t in SOURCE_DATA:
            kind = "원천데이터"
        else:
            kind = "미분류"
        print(f"{n:>10}  {kind:<8}  {t}")
    print("-" * 60)
    print(f"예측산출물 합계 {tot_art} 행")
    unknown = [t for t in tabs if t not in PREDICT_ARTIFACTS and t not in SOURCE_DATA]
    if unknown:
        print(f"\n미분류(리셋 판단 필요): {unknown}")
    conn.close()


if __name__ == "__main__":
    main()
