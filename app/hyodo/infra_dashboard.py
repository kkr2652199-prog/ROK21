# -*- coding: utf-8 -*-
"""K-P5: hyodo LSTM·인프라 READ-ONLY 대시보드 (표시 전용 · 산출 무관)."""
from __future__ import annotations

from typing import Any

from app.hyodo.predict_lstm import RETRAIN_INTERVAL, SEQ_LEN, lstm_runtime_status

BASELINE_PIN = "640cb67"

FROZEN_TOKENS = [
    "_get_draws_before (hyodo/data_service)",
    "random.choices (testlotto 동결 — hyodo 미해당)",
    "boost 상한 (testlotto learn_state)",
]


def build_infra_dashboard() -> dict[str, Any]:
    """LSTM 런타임·DB·핀·샌드박스 안내 (READ-ONLY)."""
    from app.hyodo.models import get_lotto_db

    conn = get_lotto_db()
    try:
        row = conn.execute(
            "SELECT MIN(draw_no), MAX(draw_no), COUNT(*) FROM lotto_draws"
        ).fetchone()
        mn = int(row[0]) if row and row[0] is not None else 0
        mx = int(row[1]) if row and row[1] is not None else 0
        cnt = int(row[2]) if row and row[2] is not None else 0
    finally:
        conn.close()

    lstm = lstm_runtime_status()
    return {
        "task": "K-P5",
        "baseline_pin": BASELINE_PIN,
        "evaluation_axis": "적중↑ 폐기 · LSTM=다음회차 PMF 추정 · 1등확률 동일 주장 금지",
        "draws": {"min": mn, "max": mx, "count": cnt},
        "lstm": lstm,
        "lstm_config": {
            "seq_len": SEQ_LEN,
            "retrain_interval": RETRAIN_INTERVAL,
            "sandbox_env": "ROK21_HYODO_LSTM_SANDBOX=1",
            "sandbox_ckpt": "models/_kp4_sandbox/lstm_hyodo.pt",
            "prod_ckpt": "models/lstm_hyodo.pt",
        },
        "cutoff_policy": "run_prediction(target): target 이전 draws만 (_get_draws_before)",
        "frozen_tokens": FROZEN_TOKENS,
        "disclaimer": (
            "이 패널은 투명성·운영 상태 표시용입니다. "
            "K-P4 샌드박스 검증과 별개로 서버 env에 따라 ckpt 경로가 달라질 수 있습니다."
        ),
    }
