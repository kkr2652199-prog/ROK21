# -*- coding: utf-8 -*-
"""K-REVIEW-POS-TRANSITION-VERIFY — 자리값→다음회 전체 전이 가설 검증.

S0 READ-ONLY. peek=T 번호 미입력(채점 라벨만). 보너스 미사용.
APPLY 없음. 1237예측 없음. 몰아주기 없음. review만.
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260827_KREVIEW_POS_TRANSITION_VERIFY.json"
OUT_MD = ROOT / "reports" / "20260827_KREVIEW_POS_TRANSITION_VERIFY.md"
DB = ROOT / "data" / "lotto_testlotto.db"
T_LO, T_HI = 2, 1237
TOP_NS = (6, 10, 15)
PRIMARY_TOP = 6
N_BINS_3 = 3
N_BINS_5 = 5
N_MIN_THIN = 10
P_GATE = 0.01
DELTA_GATE = 0.05
RNG_SEED = 42


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _hyper_mu_var(top_n: int) -> tuple[float, float]:
    n, n_pop, k = 6.0, 45.0, float(top_n)
    mu = n * k / n_pop
    var = n * (k / n_pop) * (1.0 - k / n_pop) * (n_pop - n) / (n_pop - 1.0)
    return mu, var


def _z_p_greater(mean: float, mu: float, var: float, n: int) -> tuple[float, float]:
    if n < 2 or var <= 0:
        return 0.0, 1.0
    se = math.sqrt(var / n)
    z = (mean - mu) / se
    p = 0.5 * math.erfc(z / math.sqrt(2.0))
    return round(z, 6), round(float(p), 8)


def _top_set(freq: Counter[int], k: int) -> set[int]:
    if not freq or k <= 0:
        return set()
    return {n for n, _ in freq.most_common(int(k))}


def _pack_hits(xs: list[int], top_n: int) -> dict[str, Any]:
    n = len(xs)
    mu, var = _hyper_mu_var(top_n)
    mean = (sum(xs) / n) if n else 0.0
    z, p = _z_p_greater(mean, mu, var, n) if n else (0.0, 1.0)
    hist = Counter(xs)
    return {
        "n": n,
        "mean_hits": round(mean, 6),
        "null": round(mu, 6),
        "delta": round(mean - mu, 6),
        "z": z,
        "p_greater": p,
        "hist": {str(i): int(hist.get(i, 0)) for i in range(7)},
    }


def _percentile(sorted_vals: list[int], q: float) -> float:
    if not sorted_vals:
        return 0.0
    if q <= 0:
        return float(sorted_vals[0])
    if q >= 1:
        return float(sorted_vals[-1])
    x = (len(sorted_vals) - 1) * q
    lo = int(math.floor(x))
    hi = int(math.ceil(x))
    if lo == hi:
        return float(sorted_vals[lo])
    w = x - lo
    return sorted_vals[lo] * (1.0 - w) + sorted_vals[hi] * w


def _edges(values: list[int], n_bins: int) -> list[float] | None:
    if len(values) < n_bins:
        return None
    s = sorted(values)
    return [_percentile(s, i / n_bins) for i in range(1, n_bins)]


def _bin_id(v: int, edges: list[float]) -> int:
    b = 0
    for e in edges:
        if v > e:
            b += 1
        else:
            break
    return b


def _load() -> tuple[dict[int, tuple[int, ...]], int, int, int]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    try:
        dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
        pred_1237 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
            ).fetchone()[0]
        )
        pred_1239 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1239"
            ).fetchone()[0]
        )
        rows = conn.execute(
            "SELECT draw_no, num1, num2, num3, num4, num5, num6 FROM lotto_draws "
            "WHERE draw_no BETWEEN 1 AND ? ORDER BY draw_no",
            (dmax,),
        ).fetchall()
    finally:
        conn.close()
    by: dict[int, tuple[int, ...]] = {}
    for r in rows:
        dno = int(r[0])
        nums = tuple(sorted(int(x) for x in r[1:7]))
        if len(set(nums)) != 6:
            continue
        by[dno] = nums
    return by, dmax, pred_1237, pred_1239


def _add_trans(
    trans: list[tuple[tuple[int, ...], tuple[int, ...]]],
    val_n: list[Counter[int]],
    val_freq: list[dict[int, Counter[int]]],
    src: tuple[int, ...],
    nxt: tuple[int, ...],
) -> None:
    trans.append((src, nxt))
    for i, v in enumerate(src):
        val_n[i][v] += 1
        val_freq[i][v].update(nxt)


def _lookup_value(
    prev: tuple[int, ...],
    val_n: list[Counter[int]],
    val_freq: list[dict[int, Counter[int]]],
) -> tuple[Counter[int], int, int, list[int]]:
    """합산 빈도. 반환: freq, n_novel_pos, n_thin_pos, per-pos n."""
    freq: Counter[int] = Counter()
    n_novel = n_thin = 0
    ns: list[int] = []
    for i, v in enumerate(prev):
        n = int(val_n[i].get(v, 0))
        ns.append(n)
        if n == 0:
            n_novel += 1
            continue
        if n < N_MIN_THIN:
            n_thin += 1
        freq.update(val_freq[i][v])
    return freq, n_novel, n_thin, ns


def _lookup_bin(
    prev: tuple[int, ...],
    trans: list[tuple[tuple[int, ...], tuple[int, ...]]],
    n_bins: int,
) -> tuple[Counter[int], int, int]:
    if not trans:
        return Counter(), 6, 0
    vals_by_pos = [[src[i] for src, _ in trans] for i in range(6)]
    edges = [_edges(vals_by_pos[i], n_bins) for i in range(6)]
    if any(e is None for e in edges):
        return Counter(), 6, 0
    bin_n = [Counter() for _ in range(6)]
    bin_freq: list[dict[int, Counter[int]]] = [defaultdict(Counter) for _ in range(6)]
    for src, nxt in trans:
        for i, v in enumerate(src):
            b = _bin_id(v, edges[i])  # type: ignore[arg-type]
            bin_n[i][b] += 1
            bin_freq[i][b].update(nxt)
    freq: Counter[int] = Counter()
    n_novel = n_thin = 0
    for i, v in enumerate(prev):
        b = _bin_id(v, edges[i])  # type: ignore[arg-type]
        n = int(bin_n[i].get(b, 0))
        if n == 0:
            n_novel += 1
            continue
        if n < N_MIN_THIN:
            n_thin += 1
        freq.update(bin_freq[i][b])
    return freq, n_novel, n_thin


def _s0() -> dict[str, Any]:
    by, dmax, pred_1237, pred_1239 = _load()
    t_list = [t for t in range(T_LO, T_HI + 1) if t in by and (t - 1) in by]
    t0 = time.perf_counter()
    trans: list[tuple[tuple[int, ...], tuple[int, ...]]] = []
    val_n: list[Counter[int]] = [Counter() for _ in range(6)]
    val_freq: list[dict[int, Counter[int]]] = [defaultdict(Counter) for _ in range(6)]
    peek_fail = 0
    rng = random.Random(RNG_SEED)

    hits_val: dict[int, list[int]] = {k: [] for k in TOP_NS}
    hits_bin3: dict[int, list[int]] = {k: [] for k in TOP_NS}
    hits_bin5: dict[int, list[int]] = {k: [] for k in TOP_NS}
    hits_eqw: list[int] = []
    hits_pos: list[list[int]] = [[] for _ in range(6)]
    hits_ctrl: list[int] = []
    board_hits: list[int] = []
    board_t: list[int] = []

    n_novel_all = 0
    n_novel_any = 0
    n_thin_any = 0
    n_scored_val = 0
    n_scored_bin3 = 0
    n_scored_bin5 = 0
    last10: list[dict[str, Any]] = []

    max_src = 0
    for t in t_list:
        prev_no = t - 1
        prev = by[prev_no]
        actual = set(by[t])
        # incremental: add all D→D+1 with D+1 < t not yet added
        while max_src + 1 < t:
            src_no = max_src + 1
            nxt_no = src_no + 1
            if nxt_no >= t:
                break
            if src_no in by and nxt_no in by:
                _add_trans(trans, val_n, val_freq, by[src_no], by[nxt_no])
            max_src = src_no

        if prev_no >= t:
            peek_fail += 1
            continue

        freq_v, n_nov, n_th, ns = _lookup_value(prev, val_n, val_freq)
        if n_nov == 6:
            n_novel_all += 1
        if n_nov > 0:
            n_novel_any += 1
        if n_th > 0:
            n_thin_any += 1

        if freq_v:
            n_scored_val += 1
            for k in TOP_NS:
                hits_val[k].append(len(actual & _top_set(freq_v, k)))
            h6 = hits_val[PRIMARY_TOP][-1]
            board_hits.append(h6)
            board_t.append(t)
            # equal-weight: 자리별 정규화 후 합
            eq: Counter[float] = Counter()
            for i, v in enumerate(prev):
                c = val_freq[i].get(v)
                tot = sum(c.values()) if c else 0
                if tot:
                    for num, cnt in c.items():
                        eq[num] += cnt / tot
            if eq:
                top6 = {n for n, _ in eq.most_common(PRIMARY_TOP)}
                hits_eqw.append(len(actual & top6))
            for i, v in enumerate(prev):
                c = val_freq[i].get(v)
                if not c:
                    continue
                hits_pos[i].append(len(actual & _top_set(c, PRIMARY_TOP)))
            # random past draw lookup (not T-1)
            cands = [d for d in range(1, prev_no) if d in by]
            if cands:
                fake = by[rng.choice(cands)]
                ff, _, _, _ = _lookup_value(fake, val_n, val_freq)
                if ff:
                    hits_ctrl.append(len(actual & _top_set(ff, PRIMARY_TOP)))

        freq3, _, _ = _lookup_bin(prev, trans, N_BINS_3)
        if freq3:
            n_scored_bin3 += 1
            for k in TOP_NS:
                hits_bin3[k].append(len(actual & _top_set(freq3, k)))
        freq5, _, _ = _lookup_bin(prev, trans, N_BINS_5)
        if freq5:
            n_scored_bin5 += 1
            for k in TOP_NS:
                hits_bin5[k].append(len(actual & _top_set(freq5, k)))

        last10.append(
            {
                "t": t,
                "prev_pos": list(prev),
                "hits_val6": hits_val[PRIMARY_TOP][-1] if freq_v else None,
                "n_lookup": ns,
                "n_novel_pos": n_nov,
                "n_thin_pos": n_th,
            }
        )
        if len(last10) > 10:
            last10.pop(0)

    # 전이표 요약 (as_of = T_HI-1 까지 전이, 마지막 T 채점 후 max_src)
    pos_summary = []
    for i in range(6):
        ns_map = dict(val_n[i])
        n_keys = len(ns_map)
        nvals = sorted(ns_map.values()) if ns_map else []
        thin_keys = sum(1 for n in nvals if n < N_MIN_THIN)
        # 각 v의 다음회 top3
        examples = []
        for v, n in sorted(ns_map.items(), key=lambda kv: -kv[1])[:5]:
            top = val_freq[i][v].most_common(3)
            examples.append({"v": v, "n": n, "next_top3": [[a, b] for a, b in top]})
        pos_summary.append(
            {
                "pos": i + 1,
                "n_keys": n_keys,
                "n_trans": int(sum(nvals)),
                "n_min": int(nvals[0]) if nvals else 0,
                "n_median": int(nvals[len(nvals) // 2]) if nvals else 0,
                "n_max": int(nvals[-1]) if nvals else 0,
                "n_thin_keys": thin_keys,
                "v_min": min(ns_map) if ns_map else None,
                "v_max": max(ns_map) if ns_map else None,
                "top_v_examples": examples,
            }
        )

    hist_board = Counter(board_hits)
    elapsed = round(time.perf_counter() - t0, 1)

    def pack_by_k(store: dict[int, list[int]]) -> dict[str, Any]:
        return {str(k): _pack_hits(store[k], k) for k in TOP_NS}

    primary = _pack_hits(hits_val[PRIMARY_TOP], PRIMARY_TOP)
    return {
        "def": {
            "pos": "본번호6 오름차순 pos1=min .. pos6=max. 보너스 미사용",
            "trans": "D의 pos_i=v → D+1 본번호6 전체 빈도. D+1 < T",
            "pool": "6자리 조회 빈도 합산 후 상위 K",
            "bins": "walk-forward 자리별 분위 3구간/5구간",
            "thin": f"n_trans < {N_MIN_THIN}",
            "primary": "value top6 합산",
            "p_gate": P_GATE,
            "delta_gate": DELTA_GATE,
            "null_top6": round(6 * 6 / 45, 6),
            "peek": "T nums = label only",
        },
        "dmax": dmax,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "t_lo": T_LO,
        "t_hi": T_HI,
        "n_t": len(t_list),
        "n_trans": len(trans),
        "peek_fail": peek_fail,
        "elapsed_s": elapsed,
        "n_novel_all6": n_novel_all,
        "n_novel_any": n_novel_any,
        "n_thin_any": n_thin_any,
        "n_scored_val": n_scored_val,
        "n_scored_bin3": n_scored_bin3,
        "n_scored_bin5": n_scored_bin5,
        "n_min_thin": N_MIN_THIN,
        "primary": primary,
        "value_by_k": pack_by_k(hits_val),
        "bin3_by_k": pack_by_k(hits_bin3),
        "bin5_by_k": pack_by_k(hits_bin5),
        "value_eq_weight_top6": _pack_hits(hits_eqw, PRIMARY_TOP),
        "value_per_pos_top6": {str(i + 1): _pack_hits(hits_pos[i], PRIMARY_TOP) for i in range(6)},
        "control_random_prev_top6": _pack_hits(hits_ctrl, PRIMARY_TOP),
        "pos_table_summary": pos_summary,
        "scoreboard": {
            "n": len(board_hits),
            "mean": round(sum(board_hits) / len(board_hits), 6) if board_hits else 0.0,
            "hist": {str(i): int(hist_board.get(i, 0)) for i in range(7)},
            "last10": last10,
            "note": "hits=모니터·적중클레임아님. 전체 hits 시계열은 hist로 요약",
        },
    }


def _s1_from(s0: dict[str, Any]) -> tuple[str, str, str, str]:
    prim = s0["primary"]
    p = float(prim.get("p_greater") or 1)
    delta = float(prim.get("delta") or 0)
    peek = int(s0.get("peek_fail") or 0)
    pred = int(s0.get("pred_1237") or 0)
    if peek != 0 or pred != 0:
        return "HOLD_HARD", "HOLD_HARD", "peek 또는 pred_1237 이상.", "skipped"
    if delta >= DELTA_GATE and p < P_GATE:
        reason = (
            f"주정의 값버전 top6 mean={prim.get('mean_hits')} null={prim.get('null')} "
            f"Δ={delta} z={prim.get('z')} p_greater={p}. 널 대비 양의 편향. "
            "이번 턴 배선 없음. 다음=DB n개조합 통계 결합은 별도 오더."
        )
        return "DISCUSS_OK", "BIAS_POS_NO_WIRE", reason, "skipped_propose_next"
    reason = (
        f"주정의 값버전 top6 mean={prim.get('mean_hits')} null={prim.get('null')} "
        f"Δ={delta} z={prim.get('z')} p_greater={p} "
        f"(게이트 Δ≥{DELTA_GATE} and p<{P_GATE}). 편향 없음. "
        "전이표는 모니터/스코어보드만. 배선 금지. 신설 테이블 없음."
    )
    return "HOLD_NO_WIRE", "HOLD_NO_WIRE", reason, "skipped"


def _write_md(doc: dict[str, Any]) -> str:
    s0 = doc["s0"]
    prim = s0["primary"]
    vb = s0["value_by_k"]
    b3 = s0["bin3_by_k"]
    b5 = s0["bin5_by_k"]
    eq = s0["value_eq_weight_top6"]
    ctrl = s0["control_random_prev_top6"]
    sb = s0["scoreboard"]
    lines = [
        "# K-REVIEW-POS-TRANSITION-VERIFY (2026-08-27)",
        "",
        f"- **판정:** `{doc['verdict']}` · S0 READ-ONLY · APPLY **없음** · review만 · 몰아주기 **미접촉**",
        f"- 시각: {doc['ts']}",
        "- 형: 자리값→다음회 전체번호 조건부 빈도. 도전이론이 널 대비 편향이 있는지. 편향 0도 정상.",
        f"- 근거: `{OUT_JSON.name}`",
        "- K-O: hits는 **가설검정 모니터**. 적중률 클레임 아님.",
        "",
        "## 정의",
        "",
        "- 자리: 본번호 6 오름차순 pos1=최소 … pos6=최대. 보너스 미사용(라벨 전용).",
        "- 전이: 과거 D의 pos_i=v → D+1 본번호 6개 전체 빈도. 사용 조건 D+1 < T. T 번호 미입력.",
        "- predicted_pool: 직전(T-1) 6자리 조회 빈도를 **합산**한 뒤 상위 K.",
        "- 값 버전 = 자리값 그대로. 구간 버전 = 자리별 walk-forward 분위 3구간·5구간.",
        f"- 얇은표본: 해당 조건 n_trans < {s0['n_min_thin']}.",
        f"- 유의미: Δ≥{s0['def']['delta_gate']} 이고 단측 p_greater<{s0['def']['p_gate']} (유사도 검증과 동일).",
        "",
        "## S0 HARD",
        "",
        f"- n_T `{s0['n_t']}` 전이쌍 `{s0['n_trans']}` peek `{s0['peek_fail']}` pred_1237 `{s0['pred_1237']}` pred_1239 `{s0['pred_1239']}` MAX `{s0['dmax']}`",
        f"- 채점 n 값 `{s0['n_scored_val']}` bin3 `{s0['n_scored_bin3']}` bin5 `{s0['n_scored_bin5']}`",
        f"- 신규 6자리모두 `{s0['n_novel_all6']}` · 신규 1자리이상 `{s0['n_novel_any']}` · 얇은 1자리이상 `{s0['n_thin_any']}`",
        f"- elapsed `{s0['elapsed_s']}`s",
        "",
        "## 주정의 값버전 top6 합산",
        "",
        f"- mean_hits `{prim.get('mean_hits')}` null `{prim.get('null')}` Δ `{prim.get('delta')}` z `{prim.get('z')}` p_greater `{prim.get('p_greater')}` n `{prim.get('n')}`",
        f"- hist `{prim.get('hist')}`",
        f"- 자리 균등가중 top6 `{eq}`",
        f"- 무작위 과거회 조회 통제 `{ctrl}`",
        "",
        "## 값 vs 구간 대조 (K=6/10/15)",
        "",
    ]
    for k in TOP_NS:
        vk, a, b = vb[str(k)], b3[str(k)], b5[str(k)]
        lines.append(
            f"- K={k} 값 mean `{vk.get('mean_hits')}` Δ `{vk.get('delta')}` p `{vk.get('p_greater')}` "
            f"· 3구간 mean `{a.get('mean_hits')}` Δ `{a.get('delta')}` p `{a.get('p_greater')}` "
            f"· 5구간 mean `{b.get('mean_hits')}` Δ `{b.get('delta')}` p `{b.get('p_greater')}`"
        )
    lines += ["", "## 자리별 값버전 top6 (모니터)", ""]
    for i in range(1, 7):
        cell = s0["value_per_pos_top6"][str(i)]
        lines.append(
            f"- pos{i} mean `{cell.get('mean_hits')}` Δ `{cell.get('delta')}` p `{cell.get('p_greater')}` n `{cell.get('n')}`"
        )
    lines += ["", "## 전이표 요약 (walk-forward 종료 시점)", ""]
    for row in s0["pos_table_summary"]:
        lines.append(
            f"- pos{row['pos']} keys `{row['n_keys']}` trans `{row['n_trans']}` "
            f"v `{row['v_min']}–{row['v_max']}` n min/med/max `{row['n_min']}/{row['n_median']}/{row['n_max']}` "
            f"얇은키 `{row['n_thin_keys']}` 예 `{row['top_v_examples'][:3]}`"
        )
    lines += [
        "",
        "## 도전 스코어보드 (모니터)",
        "",
        f"- n `{sb['n']}` mean `{sb['mean']}` hist `{sb['hist']}`",
        f"- last10 `{sb['last10']}`",
        "",
        "## S1 판정",
        "",
        f"- `{doc['s1']}`",
        f"- 사유: {doc['reason']}",
        f"- S2 `{doc['s2']}`",
        "- 배선 플래그 **신설하지 않음**. 신설 테이블 **없음**. 엔진·stat/markov·7번 WIRE **불변**.",
        "",
        "## 이번 턴에 하지 않음",
        "",
        "- T 번호를 전이표에 입력 — 금지(지킴).",
        "- 보너스 재료 · 몰아주기 · 전체조합 · `random.choices` · kweon · 자동화 · 1237예측 · APPLY.",
        "",
        "## 롤백",
        "",
        "- WIRE 키: **해당 없음**(플래그·표 없음)",
        "",
        "## 파일",
        "",
        f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
    ]
    return "\n".join(lines)


def main() -> None:
    print("S0 pos-transition", flush=True)
    s0 = _s0()
    verdict, s1, reason, s2 = _s1_from(s0)
    doc = {
        "id": "K-REVIEW-POS-TRANSITION-VERIFY",
        "ts": _now(),
        "verdict": verdict,
        "s0": s0,
        "s1": s1,
        "reason": reason,
        "s2": s2,
        "apply": False,
        "live_pass": False,
        "repack": "untouched",
        "all_combos": "untouched",
        "automation": False,
        "predict": False,
        "brain": "review_only",
        "ko": "hits=가설검정모니터·성적클레임아님",
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(_write_md(doc) + "\n", encoding="utf-8")
    prim = s0["primary"]
    print(
        verdict,
        "mean",
        prim.get("mean_hits"),
        "delta",
        prim.get("delta"),
        "p",
        prim.get("p_greater"),
        "novel_all",
        s0["n_novel_all6"],
        flush=True,
    )


if __name__ == "__main__":
    main()
