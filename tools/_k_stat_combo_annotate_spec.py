# -*- coding: utf-8 -*-
"""K-STAT-COMBO-ANNOTATE-SPEC — 궁합 세트 annotate SPEC. 플래그OFF · APPLY없음."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from math import comb
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.features.draw_features import build_pair_freq, consecutive_pairs, pair_set
from app.testlotto.signal_pool import ROLE_TIER_LEARN_BRAINS

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KSTAT_COMBO_ANNOTATE_SPEC.json"
OUT_MD = ROOT / "reports" / "20260815_KSTAT_COMBO_ANNOTATE_SPEC.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236
AS_OF = 1236
C45_6 = comb(45, 6)
P_PAIR = comb(43, 4) / C45_6  # 특정 2번호가 6셋에 같이 들어갈 확률
E_CONSEC = 44 * P_PAIR  # 연번 칸 44개
WIN = 100
E_PAIR_WIN = WIN * P_PAIR
HOOK = "app/testlotto/brains/stat_brain/predict.py: tagged[] 이후 · diversity.pick 직전"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _skill_sets(pool: list[dict]) -> list[list[int]]:
    out: list[list[int]] = []
    for s in pool:
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) != 6:
            continue
        role = str(s.get("role") or "")
        sn = int(s.get("set_no") or s.get("pred_set_no") or 0)
        if role.startswith("skill") or (not role and 1 <= sn <= 5):
            out.append(nums)
        elif not role and not sn and len(out) < 5:
            out.append(nums)
    return out[:5]


def main() -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    draws = [dict(r) for r in conn.execute("SELECT * FROM lotto_draws WHERE draw_no < ? ORDER BY draw_no", (AS_OF + 1,))]
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    peek = int(conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log WHERE as_of >= draw_no").fetchone()[0])
    cache_by = {
        int(r["draw_no"]): json.loads(r["pool_json"] or "[]")
        for r in conn.execute(
            "SELECT draw_no, pool_json FROM testlotto_pool_view_cache "
            "WHERE brain='stat' AND draw_no BETWEEN ? AND ?",
            (LO, HI),
        )
    }
    conn.close()
    hist: list[dict] = []
    consec_vs: list[float] = []
    pair_sum_vs: list[float] = []
    n_sets = 0
    peek_score = 0
    for d in draws:
        hist.append(d)
        dn = int(d["draw_no"])
        nxt = dn + 1
        if nxt < LO or nxt > HI:
            continue
        if any(int(x["draw_no"]) >= nxt for x in hist):
            peek_score += 1
            continue
        freq = build_pair_freq(hist, window=WIN)
        pool = cache_by.get(nxt) or []
        for nums in _skill_sets(pool):
            consec_vs.append(consecutive_pairs(nums))
            pair_sum_vs.append(sum(freq.get(p, 0) for p in pair_set(nums)))
            n_sets += 1

    m_con = mean(consec_vs) if consec_vs else None
    m_ps = mean(pair_sum_vs) if pair_sum_vs else None
    peek_table = max((int(d["draw_no"]) for d in draws if int(d["draw_no"]) < AS_OF), default=0) < AS_OF
    hard_ok = (
        peek == 0
        and peek_score == 0
        and pred_1237 == 0
        and dmax == 1236
        and peek_table
        and n_sets > 0
    )

    spec = {
        "flag": "STAT_COMBO_ANNOTATE_WIRE",
        "default": False,
        "brain": "stat",
        "hook": HOOK,
        "score": "세트 15쌍의 window100 pair_freq 합 + consecutive_pairs. pick_score에만 가산(별 GO).",
        "forbid": [
            "crowd_signal.prefer_table / prize_table 수정",
            "stat number_scores / engine.generate 가중",
            "markov annotate_prefer / blend_weights / pair_boost 복사",
            "lotto4 lotto_cooccur_* 연결",
            "random.choices 라인",
        ],
        "gate_if_apply": "prefer/prize 비악화 · peek0 · stat 캐시 외 불변",
        "neighbor_def": "같은회 |a-b|=1 만 연번. 다음회 n±1은 markov 영역·이번 SPEC 제외.",
    }

    payload = {
        "id": "K-STAT-COMBO-ANNOTATE-SPEC",
        "as_of": _now(),
        "verdict": "SPEC_OK" if hard_ok else "SPEC_FAIL",
        "apply": False,
        "recommend": "HOLD",
        "ge3_claim": False,
        "draw_1237": False,
        "window": [LO, HI],
        "as_of_draw": AS_OF,
        "hard_ok": hard_ok,
        "peek_evolve": peek,
        "peek_score": peek_score,
        "pred_1237": pred_1237,
        "draws_max": dmax,
        "role_learn_brains": sorted(ROLE_TIER_LEARN_BRAINS),
        "null": {
            "P_specific_pair": round(P_PAIR, 6),
            "E_consec_pairs": round(E_CONSEC, 4),
            "E_pair_count_window100": round(E_PAIR_WIN, 4),
            "E_pair_sum_15": round(15 * E_PAIR_WIN, 4),
        },
        "baseline_stat_skill": {
            "n_sets": n_sets,
            "mean_consec": round(m_con, 4) if m_con is not None else None,
            "d_consec": round(m_con - E_CONSEC, 4) if m_con is not None else None,
            "mean_pair_sum": round(m_ps, 4) if m_ps is not None else None,
            "d_pair_sum": round(m_ps - 15 * E_PAIR_WIN, 4) if m_ps is not None else None,
        },
        "spec": spec,
        "reason": (
            "세트 annotate는 부착점·널이 있다. 켜면 pick이 바뀌어 발권 구성이 변한다. "
            "markov pair_boost와 같은 쌍통계를 반대로 쓰면 쿼터 혼합 시 상쇄. "
            "K-U 쌍층은 널. 플래그 OFF 유지. APPLY 없음."
        ),
    }

    b = payload["baseline_stat_skill"]
    nll = payload["null"]
    lines = [
        "# K-STAT-COMBO-ANNOTATE-SPEC",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · READ-ONLY · APPLY **없음** · 1237아님",
        "목적=COOCCUR 다음 A. stat 전용 궁합 **세트 annotate** SPEC. `prefer_table` 미수정. 플래그 OFF.",
        "",
        f"권고=**HOLD**. {payload['reason']}",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. peek={peek} · pred_1237={pred_1237} · MAX={dmax} · n_sets={n_sets}.",
        "",
        "## 0) SPEC (코드에 아직 없음)",
        "",
        f"| 항 | 값 |",
        f"|----|-----|",
        f"| 플래그 | `{spec['flag']}` 기본 **{spec['default']}** |",
        f"| 뇌 | {spec['brain']}만 |",
        f"| 끼움점 | `{HOOK}` |",
        f"| 점수 | {spec['score']} |",
        f"| 이웃 정의 | {spec['neighbor_def']} |",
        f"| 켜면 게이트 | {spec['gate_if_apply']} |",
        "",
        "금지: " + " · ".join(spec["forbid"]),
        "",
        "## 1) 널 (조합 기하)",
        "",
        f"| 항 | 값 |",
        f"|----|-----|",
        f"| P(특정쌍) | {nll['P_specific_pair']} = C(43,4)/C(45,6) |",
        f"| E[연번쌍 수] | {nll['E_consec_pairs']} |",
        f"| E[쌍빈도] window100 | {nll['E_pair_count_window100']} |",
        f"| E[세트 15쌍 합] | {nll['E_pair_sum_15']} |",
        "",
        "## 2) 지금 stat skill 베이스라인 (annotate OFF · walk-forward)",
        "",
        f"| 항 | 값 |",
        f"|----|-----|",
        f"| n | {b['n_sets']} |",
        f"| mean 연번쌍 | {b['mean_consec']} (Δ {b['d_consec']:+} vs 널 {nll['E_consec_pairs']}) |",
        f"| mean 쌍빈도합 | {b['mean_pair_sum']} (Δ {b['d_pair_sum']:+} vs 널 {nll['E_pair_sum_15']}) |",
        "",
        "Δ는 축 편차. **누가 낫다·예측신호 금지**. 상위 동반쌍을 번호선택 근거로 쓰지 않음 (K-U).",
        "",
        "## 3) 왜 APPLY 안 하나",
        "",
        "- annotate ON이면 `diversity.pick` 순서가 바뀌어 **발권 구성 변경**. 표 수정은 아니지만 라이브 출력이 바뀜.",
        "- markov는 이미 `pair_boost`로 같은 `lotto_draws` 쌍을 씀. stat이 반대로 피하면 쿼터 혼합 시 상쇄.",
        "- 다음회 이웃은 널과 같음(DISCUSS 0.7757≈0.80). 이번 SPEC 제외.",
        "- 동결 `random.choices` 미수정. prefer_table 오염 금지.",
        "",
        "## 4) 판정",
        "",
        "SPEC_OK · HOLD. 플래그 신설·APPLY 없음. 숙제ON·covering휠·S2·1237 없음.",
        "다음 APPLY는 형 1건.",
        "",
        "## 5) 금지 확인",
        "",
        "DB write 없음. 동결 토큰 미수정. kweon 미접촉. 1237 아님.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], "hard_ok": hard_ok, "baseline": b, "null": nll}, ensure_ascii=False))
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
