# -*- coding: utf-8 -*-
"""K-TL-DASH-LEARN-VS-RANDOM — 대시보드 4등+ 0건이 학습인지 랜덤인지 READ-ONLY."""
from __future__ import annotations

import json
import math
import os
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.evolve_auto import evolve_auto_enabled
from app.testlotto.evolve_log import WEIGHT_APPLIED
from app.testlotto.signal_pool import (
    FEATURE_LAMBDA_WIRE,
    REPACK_HYENA_MODE_BY_BRAIN,
    ROLE_TIER_LEARN_BRAINS,
    ROLE_TIER_LEARN_WIRE,
)
from app.testlotto.stat_pool_learn import STAT_POOL_LEARN_WIRE

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260822_KTL_DASH_LEARN_VS_RANDOM.json"
OUT_MD = ROOT / "reports" / "20260822_KTL_DASH_LEARN_VS_RANDOM.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
BRAINS = ("stat", "markov", "review")
N_POP, K_DRAW, K_WIN = 45, 6, 6
C45_6 = math.comb(N_POP, K_DRAW)


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _hg_p(k: int) -> float:
    return math.comb(K_WIN, k) * math.comb(N_POP - K_WIN, K_DRAW - k) / C45_6


def main() -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    hist = {i: 0 for i in range(-1, 7)}
    for r in conn.execute(
        "SELECT matched_count, COUNT(*) n FROM lotto_predictions "
        "WHERE brain_tag IN ('stat','markov','review') GROUP BY matched_count"
    ):
        hist[int(r["matched_count"])] = int(r["n"])
    n_pred = sum(hist.values())
    n_scored = sum(hist[k] for k in range(0, 7))
    ge4 = hist[4] + hist[5] + hist[6]
    ge3 = ge4 + hist[3]
    hits_sum = sum(k * hist[k] for k in range(0, 7))
    mean_hits = (hits_sum / n_scored) if n_scored else None

    by_brain: dict[str, Any] = {}
    for tag in BRAINS:
        h = {i: 0 for i in range(-1, 7)}
        for r in conn.execute(
            "SELECT matched_count, COUNT(*) n FROM lotto_predictions "
            "WHERE brain_tag=? GROUP BY matched_count",
            (tag,),
        ):
            h[int(r["matched_count"])] = int(r["n"])
        ns = sum(h[k] for k in range(0, 7))
        hs = sum(k * h[k] for k in range(0, 7))
        by_brain[tag] = {
            "n": sum(h.values()),
            "n_scored": ns,
            "hist": {str(k): h[k] for k in range(-1, 7)},
            "ge4": h[4] + h[5] + h[6],
            "ge3": h[3] + h[4] + h[5] + h[6],
            "mean_hits": (hs / ns) if ns else None,
        }

    ev_n = int(conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log").fetchone()[0])
    ev_w = [
        (float(r[0]), int(r[1]))
        for r in conn.execute(
            "SELECT weight_applied, COUNT(*) FROM testlotto_evolve_log GROUP BY weight_applied"
        )
    ]
    ev_peek = int(
        conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log WHERE as_of >= draw_no").fetchone()[0]
    )
    ev_asof = conn.execute(
        "SELECT MIN(as_of), MAX(as_of), MIN(draw_no), MAX(draw_no) FROM testlotto_evolve_log"
    ).fetchone()

    learn_n = int(conn.execute("SELECT COUNT(*) FROM testlotto_brain_learn_state").fetchone()[0])
    learn_tags = [
        str(r[0])
        for r in conn.execute("SELECT DISTINCT brain_tag FROM testlotto_brain_learn_state")
    ]
    adj_sample: dict[str, Any] = {}
    for tag in BRAINS:
        row = conn.execute(
            "SELECT state_json, review_count, last_draw_no FROM testlotto_brain_learn_state WHERE brain_tag=?",
            (tag,),
        ).fetchone()
        if not row:
            adj_sample[tag] = None
            continue
        st = json.loads(row[0] or "{}")
        adj_sample[tag] = {
            "review_count": int(row[1] or 0),
            "last_draw_no": int(row[2] or 0),
            "adjustments": st.get("adjustments") or {},
            "miss_counts": st.get("miss_counts") or {},
            "state_keys": sorted(st.keys()),
        }

    skill_hw = int(conn.execute("SELECT COUNT(*) FROM testlotto_skill_homework").fetchone()[0])
    role_hw = int(conn.execute("SELECT COUNT(*) FROM testlotto_role_homework").fetchone()[0])
    ledger = {
        str(r[0]): int(r[1])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) FROM testlotto_pool_hit_ledger GROUP BY brain_tag"
        )
    }
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0] or 0)
    conn.close()

    p = {k: _hg_p(k) for k in range(0, 7)}
    e_ge4_indep = n_scored * (p[4] + p[5] + p[6]) if n_scored else 0.0
    e_ge3_indep = n_scored * (p[3] + p[4] + p[5] + p[6]) if n_scored else 0.0
    e_mean = 6 * 6 / 45

    from app.testlotto.brains.markov_brain.learn import LEARN_WIRED as MARKOV_LEARN
    from app.testlotto.brains.stat_brain.past_learn import PAST_LEARN_WIRE

    flags = {
        "FEATURE_LAMBDA_WIRE": bool(FEATURE_LAMBDA_WIRE),
        "EVOLVE_AUTO_env": os.environ.get("EVOLVE_AUTO", "0"),
        "evolve_auto_enabled": bool(evolve_auto_enabled()),
        "WEIGHT_APPLIED": float(WEIGHT_APPLIED),
        "ROLE_TIER_LEARN_WIRE": bool(ROLE_TIER_LEARN_WIRE),
        "ROLE_TIER_LEARN_BRAINS": sorted(ROLE_TIER_LEARN_BRAINS),
        "STAT_POOL_LEARN_WIRE": bool(STAT_POOL_LEARN_WIRE),
        "PAST_LEARN_WIRE": bool(PAST_LEARN_WIRE),
        "MARKOV_LEARN_WIRED": bool(MARKOV_LEARN),
        "review_apply_learn_boost": False,
        "REPACK_HYENA_MODE_BY_BRAIN": dict(REPACK_HYENA_MODE_BY_BRAIN),
        "backfill_learner": "RollingSignalLearner() empty — warm_learner_to_draw 없음",
    }

    verdict = {
        "dashboard_ge4_zero": ge4 == 0,
        "ge4_vs_indep_null": "below" if ge4 < e_ge4_indep else "at_or_above",
        "mean_near_null_0_80": (
            abs((mean_hits or 0) - e_mean) <= 0.05 if mean_hits is not None else None
        ),
        "evolve_changes_weights": False,
        "evolve_is_monitor_log": True,
        "live_learn_consume": sorted(ROLE_TIER_LEARN_BRAINS) == ["stat"],
        "auto_evolve_running": False,
        "prediction_is_pure_uniform_random": False,
        "note": (
            "발권은 균등 random.choices가 아님(빈도/prefer/prize·숙제·score5). "
            "다만 진화 루프는 weight=0·EVOLVE_AUTO OFF라 적중을 학습해 다음 발권을 바꾸지 않음. "
            "4등+는 널도 희귀. 독립가정 E[ge4]와 비교만. 우열 클레임 금지."
        ),
    }

    payload = {
        "id": "K-TL-DASH-LEARN-VS-RANDOM",
        "as_of": _now(),
        "read_only": True,
        "draw_1237": False,
        "n_pred": n_pred,
        "n_scored": n_scored,
        "hist": {str(k): hist[k] for k in range(-1, 7)},
        "ge4": ge4,
        "ge3": ge3,
        "mean_hits": mean_hits,
        "by_brain": by_brain,
        "hypergeometric": {
            "C45_6": C45_6,
            "E_hits": e_mean,
            "P_k": {str(k): p[k] for k in range(0, 7)},
            "P_ge4": p[4] + p[5] + p[6],
            "P_ge3": p[3] + p[4] + p[5] + p[6],
            "E_ge4_if_indep": e_ge4_indep,
            "E_ge3_if_indep": e_ge3_indep,
            "source": "Siegrist LibreTexts 13.7 · K-O · 20260814_KSTAT_POOL_LEARN_EVOLVE.json",
        },
        "evolve": {
            "n": ev_n,
            "weight_applied_groups": ev_w,
            "peek": ev_peek,
            "as_of_min": ev_asof[0],
            "as_of_max": ev_asof[1],
            "draw_min": ev_asof[2],
            "draw_max": ev_asof[3],
        },
        "learn_state_n": learn_n,
        "learn_tags": learn_tags,
        "adj_sample": adj_sample,
        "skill_hw": skill_hw,
        "role_hw": role_hw,
        "ledger_by": ledger,
        "pred_1237": pred_1237,
        "draws_max": dmax,
        "flags": flags,
        "verdict": verdict,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    pge4 = p[4] + p[5] + p[6]
    lines = [
        "# K-TL-DASH-LEARN-VS-RANDOM (2026-08-22)",
        "",
        "- **판정:** `DISCUSS_OK` · READ-ONLY · APPLY **없음**",
        "- 형 질문: 테스트 대시보드 4등+ 0건 · 학습진화가 도나, 랜덤인가",
        f"- 근거: `{OUT_JSON.as_posix().replace(str(ROOT).replace(chr(92), '/') + '/', '')}`",
        "",
        "## 1) 대시보드 기록 (우열 아님)",
        "",
        "| 항목 | 값 |",
        "|------|-----|",
        f"| pred 3뇌 | **{n_pred}** · 채점 **{n_scored}** |",
        f"| matched hist 0/1/2/3/4/5/6 | {hist[0]} / {hist[1]} / {hist[2]} / {hist[3]} / {hist[4]} / {hist[5]} / {hist[6]} |",
        f"| 4등+(matched≥4) | **{ge4}** |",
        f"| 5등+(matched≥3) | **{ge3}** |",
        f"| mean hits | **{mean_hits}** |",
        f"| 뇌별 ge4 | stat {by_brain['stat']['ge4']} · markov {by_brain['markov']['ge4']} · review {by_brain['review']['ge4']} |",
        f"| 뇌별 mean | stat {by_brain['stat']['mean_hits']} · markov {by_brain['markov']['mean_hits']} · review {by_brain['review']['mean_hits']} |",
        f"| pred_1237 / MAX | **{pred_1237}** / **{dmax}** |",
        "",
        "## 2) 널(초기하) — 독립 가정 참고만",
        "",
        "한 장 E[hits]=6×6/45=**0.80** (K-O). 4등=정확히 4맞.",
        "",
        "| k맞 | P | 독립가정 E[건] (n=채점) |",
        "|-----|---|------------------------|",
    ]
    for k in range(0, 7):
        lines.append(f"| {k} | {p[k]:.8f} | {n_scored * p[k]:.2f} |")
    lines += [
        f"| ≥4 | {pge4:.8f} | **{e_ge4_indep:.2f}** |",
        "",
        "- 같은 회 15장은 번호가 겹침(pool+score5) → 독립가정보다 분산이 큼. E[건]은 **상한 참고**이지 게이트가 아님.",
        "- 4등+ 0건은 ‘학습 실패’ 증거가 아님. 널도 희귀(P≥4≈0.00139). 반대로 0이 독립기대보다 낮아도 **회차 상관**이면 가능.",
        "",
        "## 3) 학습·진화가 도나",
        "",
        "| 스위치 | 값 | 의미 |",
        "|--------|-----|------|",
        f"| EVOLVE_AUTO | **{flags['evolve_auto_enabled']}** (env={flags['EVOLVE_AUTO_env']}) | 자동 진화 **꺼짐** |",
        f"| FEATURE_LAMBDA | **{flags['FEATURE_LAMBDA_WIRE']}** | 특징λ 미적용 |",
        f"| weight_applied | **{flags['WEIGHT_APPLIED']}** · evolve 그룹 {ev_w} | 로그는 써도 발권 가중 **0** |",
        f"| evolve_log 행 | **{ev_n}** · peek **{ev_peek}** · as_of {ev_asof[0]}–{ev_asof[1]} | 모니터 로그 |",
        f"| 역할숙제 소비 | **{flags['ROLE_TIER_LEARN_BRAINS']}** | stat만 |",
        f"| STAT_POOL_LEARN | **{flags['STAT_POOL_LEARN_WIRE']}** | stat 풀 학습 배선 ON |",
        f"| PAST_LEARN / markov LEARN | {flags['PAST_LEARN_WIRE']} / {flags['MARKOV_LEARN_WIRED']} | 엔진 부스팅 함수는 있음 |",
        f"| review apply_learn_boost | **없음** | 이월·prize만 |",
        f"| 몰아주기 | {flags['REPACK_HYENA_MODE_BY_BRAIN']} | score5 |",
        f"| 이번 백필 learner | **빈 RollingSignalLearner()** | B1과 같음 · 200회 warm 없음 |",
        f"| skill_hw / role_hw / learn_state | {skill_hw} / {role_hw} / {learn_n} {learn_tags} |",
        f"| 원장 | {ledger} |",
        "",
        "### learn_state adjustments (실측)",
        "",
        "```json",
        json.dumps(adj_sample, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 4) 결론 (형 질문에 대한 답)",
        "",
        "1. **미래를 맞히는 학습은 가동 중이 아니다.** 진화 자동 OFF · weight=0 · λ OFF. evolve_log는 채점 일기이지 다음 회 발권을 바꾸지 않는다.",
        "2. **완전 균등 랜덤도 아니다.** 번호 선택은 빈도/prefer/prize·stat 숙제·score5 몰아주기를 탄다. 다만 그 축은 당첨확률 향상이 목표가 아니고(K-O), mean은 널 0.80 근처가 정상이다.",
        "3. **4등+ 0건은 실망스러울 수 있으나, 단일게임·초기하에서는 흔한 침묵이다.** 독립가정 E[ge4]≈"
        + f"{e_ge4_indep:.1f}"
        + "인데 실제 0이면 ‘널보다 덜 겹침/상관/표본’이지 엔진이 죽었다는 뜻은 아님.",
        "4. 백필 발권은 **콜드 learner**라 라이브 발권(warm 200)과 다를 수 있음(B1). 대시보드 숫자는 그 콜드 백필 기록이다.",
        "",
        "- 1237아님 · APPLY없음 · ge3/4 성능 클레임 금지.",
        "",
        "## 파일",
        "",
        "- `tools/_k_tl_dash_learn_vs_random.py`",
        f"- `{OUT_JSON.name}`",
    ]
    text = "\n".join(lines) + "\n"
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"ge4": ge4, "mean": mean_hits, "n": n_scored, "E_ge4": e_ge4_indep}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
