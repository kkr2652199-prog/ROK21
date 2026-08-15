# -*- coding: utf-8 -*-
"""K-STAT-EVOLVE-DIAG-LOG — stat 래퍼. 본체는 evolve_diag.write_evolve_diag."""
from __future__ import annotations

from typing import Any

from app.testlotto.evolve_diag import get_evolve_diag, write_evolve_diag

TAG = "stat"


def write_evolve_diag_stat(draw_no: int) -> dict[str, Any]:
    """회차 N 확정 후 stat 캐시만 채점 append. 타뇌 미접촉."""
    return write_evolve_diag(int(draw_no), TAG)


def get_evolve_diag_stat(draw_no: int) -> dict[str, Any] | None:
    """읽기: brain_tag='stat' 필수. 3뇌 합산 없음."""
    return get_evolve_diag(int(draw_no), TAG)
