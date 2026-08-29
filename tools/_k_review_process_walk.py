# -*- coding: utf-8 -*-
"""K-REVIEW-PROCESS-WALK — 금액뇌 가동 경로를 부품 시점으로 실측. 억지 결함 금지. READ-ONLY."""
from __future__ import annotations

import json
import random
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.brains.review_brain import engine as rev_eng
from app.testlotto.brains.review_brain.engine import neutralize_ending_digit_mass
from app.testlotto.brains.review_brain.kb7_future import REVIEW_KB7_WIRE
from app.testlotto.brains.review_brain.rare_consec import REVIEW_CONSEC_PASS_WIRE
from app.testlotto.brains.review_brain.rare_pass_store import should_pass
from app.testlotto.brains.review_brain.rare_slice import REVIEW_RARE_SLICE_WIRE
from app.testlotto.brains.review_brain.shape_table import REVIEW_SHAPE_WIRE
from app.testlotto.brains.review_brain.draw_shape_kb import (
    REVIEW_SHAPE_KB_WEIGHT_WIRE,
    keep_set_by_hist,
)
from app.testlotto.brains.shared import crowd_signal as cs
from app.testlotto.data_service import _get_draws_before
from app.testlotto.features.draw_features import sorted_nums
from app.testlotto.filters import tier1_filter
from app.testlotto.learn_state_cutoff import set_learn_as_of
from app.testlotto.signal_pool import ROLE_SLOTS_WIRE, ROLE_TIER_LEARN_BRAINS

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260829_KREVIEW_PROCESS_WALK.json"
OUT_MD = ROOT / "reports" / "20260829_KREVIEW_PROCESS_WALK.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
AS_OF = 1236
SEED = 42


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _instrument_generate(draws: list[dict], n_sets: int, adj: dict | None) -> dict[str, Any]:
    """engine.generate와 동일 루프 + 거절 사유 카운트. 저장 없음."""
    from app.testlotto.brains.review_brain.kb7_future import collect_before

    weights = rev_eng.build_review_weights(draws, adj)
    kb7 = collect_before(draws)
    prev_nums = set(sorted_nums(draws[-1]))
    used: set[tuple[int, ...]] = set()
    results: list[list[int]] = []
    why: Counter[str] = Counter()
    attempts = 0
    random.seed(SEED)
    while len(results) < n_sets and attempts < 3000:
        attempts += 1
        pool = list(range(1, 46))
        w = [weights[n] for n in pool]
        if any(x < 0 for x in w):
            why["neg_weight"] += 1
        if sum(w) <= 0:
            why["zero_mass"] += 1
            break
        pick: list[int] = []
        for _ in range(6):
            if not pool:
                break
            chosen = random.choices(pool, weights=w, k=1)[0]
            pick.append(chosen)
            idx = pool.index(chosen)
            pool.pop(idx)
            w.pop(idx)
        pick = sorted(pick)
        if len(pick) != 6:
            why["short"] += 1
            continue
        key = tuple(pick)
        if key in used:
            why["dup"] += 1
            continue
        if not tier1_filter(pick):
            why["tier1"] += 1
            continue
        if REVIEW_RARE_SLICE_WIRE and should_pass(pick):
            why["rare_pass"] += 1
            continue
        if REVIEW_SHAPE_KB_WEIGHT_WIRE:
            hist = (kb7 or {}).get("shape")
            if not keep_set_by_hist(pick, hist):
                why["shape_kb"] += 1
                continue
        if REVIEW_KB7_WIRE:
            why["kb7_skip_armed"] += 1
        used.add(key)
        why["accept"] += 1
        results.append(pick)
    zero_w = [n for n in range(1, 46) if float(weights.get(n, 0)) <= 0]
    carry = neutralize_ending_digit_mass(
        {
            n: (1.8 if n in prev_nums else 0.85)
            * (0.08)
            for n in range(1, 46)
        }
    )
    return {
        "n_want": n_sets,
        "n_got": len(results),
        "attempts": attempts,
        "reject": dict(why),
        "zero_weight_after_build": zero_w,
        "sets": results,
        "carry_in_sets_mean": round(
            sum(len([n for n in s if n in prev_nums]) for s in results) / max(len(results), 1),
            4,
        ),
    }


def main() -> int:
    set_learn_as_of(AS_OF)
    draws = _get_draws_before(AS_OF)
    peek = max((int(d["draw_no"]) for d in draws), default=0)
    fw_pos = sum(1 for d in draws if int(d.get("first_winners") or 0) > 0)
    fw_zero = sum(1 for d in draws if int(d.get("first_winners") or 0) == 0)
    fw_missing = sum(1 for d in draws if "first_winners" not in d)
    from app.testlotto.brains.review_brain import learn

    adj_pack = learn.get_adjustments()
    adj = adj_pack.get("adjustments", {}) if isinstance(adj_pack, dict) else {}
    inst = _instrument_generate(draws, 10, adj if isinstance(adj, dict) else None)

    import app.testlotto.signal_pool as sp

    random.seed(SEED)
    pool = sp.expand_pool(draws, AS_OF, seed=SEED, brains=["review"])
    roles = Counter(str(x.get("role")) for x in pool)
    sources = Counter(str(x.get("source")) for x in pool)
    kinds = Counter(str(x.get("kind")) for x in pool)

    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    cache_n = int(
        conn.execute(
            "SELECT COUNT(*) FROM testlotto_pool_view_cache WHERE brain='review' AND draw_no BETWEEN 1037 AND 1236"
        ).fetchone()[0]
    )
    short_cache = 0
    role_src = Counter()
    for r in conn.execute(
        "SELECT pool_json FROM testlotto_pool_view_cache WHERE brain='review' AND draw_no BETWEEN 1037 AND 1236"
    ):
        sets = json.loads(r[0] or "[]")
        if len(sets) < 10:
            short_cache += 1
        for s in sets:
            role_src[(str(s.get("role")), str(s.get("source")))] += 1
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    conn.close()

    live = {
        "PRIZE_WIRE": cs.prize_on(),
        "REVIEW_PRIZE_RANK_MIX": rev_eng.REVIEW_PRIZE_RANK_MIX,
        "REVIEW_PRIZE_RANK_ALPHA": rev_eng.REVIEW_PRIZE_RANK_ALPHA,
        "REVIEW_REASONABLE_SET": rev_eng.REVIEW_REASONABLE_SET,
        "compose": rev_eng.review_compose_mode(),
        "REVIEW_SHAPE_WIRE": REVIEW_SHAPE_WIRE,
        "REVIEW_RARE_SLICE_WIRE": REVIEW_RARE_SLICE_WIRE,
        "REVIEW_SHAPE_KB_WEIGHT_WIRE": REVIEW_SHAPE_KB_WEIGHT_WIRE,
        "REVIEW_CONSEC_PASS_WIRE": REVIEW_CONSEC_PASS_WIRE,
        "REVIEW_KB7_WIRE": REVIEW_KB7_WIRE,
        "ROLE_SLOTS_WIRE": ROLE_SLOTS_WIRE,
        "ROLE_TIER_LEARN_BRAINS": sorted(ROLE_TIER_LEARN_BRAINS),
    }

    findings: list[dict[str, str]] = []
    # 라벨 스티커: 10장 모두 같은 source
    if sources and set(sources) == {"review_reasonable"} and roles.get("cover_r3") and roles.get("shape_r2"):
        findings.append(
            {
                "id": "LABEL_STICKER",
                "grade": "실체불일치",
                "text": "6~8 cover / 9~10 shape는 별 엔진이 아님. 같은 generate 10장의 스티커.",
            }
        )
    if inst["n_got"] == 10 and inst["reject"].get("shape_kb", 0) > 0:
        findings.append(
            {
                "id": "SHAPE_KB_RNG",
                "grade": "설계된거절",
                "text": "형태저울이 추가 random으로 장을 다시 뽑게 함. 칼 아님. 시드 경로에 동전 한 장 더 있음.",
            }
        )
    if fw_missing == 0 and fw_pos >= 30:
        findings.append(
            {
                "id": "FW_PROXY_OK",
                "grade": "정상",
                "text": "first_winners가 draws에 있음. 판매수 원본은 없음(프록시). 결함 아님.",
            }
        )
    if not adj or not any(float((adj or {}).get(k, 0) or 0) for k in ("carry_over_boost", "ending_digit_boost")):
        findings.append(
            {
                "id": "LEARN_ADJ_IDLE",
                "grade": "정상",
                "text": "learn 조정값 비어 있음. 라이브 가중은 코드 상수(이월 1.8·순위혼합)로 돔.",
            }
        )
    if inst["zero_weight_after_build"]:
        findings.append(
            {
                "id": "ZERO_WEIGHT",
                "grade": "잔여",
                "text": f"build 후 가중 0 번호={inst['zero_weight_after_build']}. 순위혼합이면 최하위 순위만.",
            }
        )
    if inst["n_got"] < 10:
        findings.append(
            {
                "id": "SHORT_POOL",
                "grade": "장애",
                "text": f"10장 미달 n={inst['n_got']} attempts={inst['attempts']}",
            }
        )
    else:
        findings.append(
            {
                "id": "TEN_OK",
                "grade": "정상",
                "text": f"1236에서 10장 완성. attempts={inst['attempts']} reject={inst['reject']}",
            }
        )
    if REVIEW_KB7_WIRE is False:
        findings.append(
            {
                "id": "KB7_IDLE",
                "grade": "정상",
                "text": "7번은 collect만 하고 가중/거절에 안 들어감. 예측 부품 아님.",
            }
        )

    payload = {
        "id": "K-REVIEW-PROCESS-WALK",
        "as_of": _now(),
        "verdict": "WALK_OK",
        "apply": False,
        "ge3_claim": False,
        "draw_1237": False,
        "as_of_draw": AS_OF,
        "peek_ok": peek < AS_OF,
        "peek_max": peek,
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "fw_used": fw_pos,
        "fw_zero": fw_zero,
        "fw_missing_key": fw_missing,
        "learn_adj": adj,
        "live": live,
        "instrument_1236": inst,
        "expand_pool_1236": {
            "n": len(pool),
            "roles": dict(roles),
            "sources": dict(sources),
            "kinds": dict(kinds),
        },
        "cache_1037_1236": {
            "n": cache_n,
            "short_lt10": short_cache,
            "role_source": {f"{a}|{b}": c for (a, b), c in role_src.items()},
        },
        "findings": findings,
        "out_of_scope": "몰아주기 score5 · 1237예측 · 적중클레임",
    }

    lines = [
        "# K-REVIEW-PROCESS-WALK",
        "",
        f"시각: {payload['as_of']} · **WALK_OK** · READ-ONLY · APPLY없음 · 1237아님 · 억지결함 금지",
        "시점=부품. 금액뇌가 실제로 통과하는 선만 따라감. 없는 문제를 만들지 않음.",
        "",
        "## 0) 내가 어떤 부품인가",
        "",
        "1. `predict.run` → `engine.generate(10)` (reasonable이라 oversample 없음).",
        "2. `build_review_weights`: 이월×1.8 → 끝수균등 → **순위혼합 0.70** → 3연속평탄.",
        "3. 6개를 `random.choices`로 뽑고, tier1·극소패스·형태저울을 통과한 장만 남김.",
        "4. `expand_pool`이 그 10장에 skill/cover/shape **스티커**를 붙임.",
        "5. 몰아주기는 이 10장 이후의 다른 부품. 이번 점검 범위 밖.",
        "",
        f"as_of={AS_OF} peek_ok={peek < AS_OF} · first_winners>0 **{fw_pos}** · 0 **{fw_zero}** · 키없음 **{fw_missing}**.",
        f"learn adj={adj} · pred_1237={pred_1237} · MAX={dmax}.",
        "",
        "## 1) 라이브 스위치",
        "",
        "| 노브 | 값 |",
        "|------|-----|",
    ]
    for k, v in live.items():
        lines.append(f"| {k} | {v} |")
    lines += [
        "",
        "## 2) 1236에서 한 장 만들어 보기 (seed 42)",
        "",
        f"want 10 · got **{inst['n_got']}** · attempts **{inst['attempts']}** · reject `{inst['reject']}`.",
        f"build 후 가중0: {inst['zero_weight_after_build'] or '없음'}.",
        f"장당 직전회 겹침 평균 {inst['carry_in_sets_mean']}.",
        f"expand_pool n={len(pool)} roles={dict(roles)} sources={dict(sources)}.",
        "",
        "## 3) 캐시 1037–1236",
        "",
        f"행 {cache_n} · 10장미만 {short_cache} · role|source `{payload['cache_1037_1236']['role_source']}`.",
        "",
        "## 4) 찾은 것 (억지 아님)",
        "",
    ]
    for f in findings:
        lines.append(f"- **{f['id']}** ({f['grade']}): {f['text']}")
    lines += [
        "",
        "## 5) 인간 입장에서 헷갈리는 것 vs 고장",
        "",
        "고장으로 보지 않음: 판매수 없음(프록시), 7번 읽기만, learn 빈값, 극소패스/tier1 거절.",
        "헷갈림: 6~10장 역할 이름. 화면 문구의 ‘이월힌트’는 자신감 숫자이지 10장 선발이 아님.",
        "이후 패치 자리: 몰아주기. 이번 APPLY 없음.",
        "",
        "## 6) 금지 확인",
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
    print(json.dumps({"verdict": "WALK_OK", "findings": findings, "inst": inst, "roles": dict(roles), "sources": dict(sources)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
