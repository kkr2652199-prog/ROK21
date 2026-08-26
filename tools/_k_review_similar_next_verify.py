# -*- coding: utf-8 -*-
"""K-REVIEW-SIMILAR-NEXT-VERIFY — 직전닮은과거→다음회차 가설 검증.

S0 READ-ONLY. peek=T 번호 미입력(채점 라벨만). 보너스 미사용.
APPLY 없음. 1237예측 없음. 몰아주기 없음.
"""
from __future__ import annotations

import json
import math
import random
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260827_KREVIEW_SIMILAR_NEXT_VERIFY.json"
OUT_MD = ROOT / "reports" / "20260827_KREVIEW_SIMILAR_NEXT_VERIFY.md"
DB = ROOT / "data" / "lotto_testlotto.db"
T_LO, T_HI = 2, 1237
HORIZONS = (1, 5, 10)
TOP_NS = (6, 10, 15)
THRESHS = (3, 4, 5)
PRIMARY_H = 1
PRIMARY_TOP = 6
PRIMARY_THR = 4
# 실질 편향: 널(0.80)에서 +0.05 이상이며 단측 p<0.01
P_GATE = 0.01
DELTA_GATE = 0.05
RNG_SEED = 42


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _sim(a: frozenset[int], b: frozenset[int]) -> int:
    """직접겹침 + (A에만 있는 번호의 ±1이 B에 있으면 1). 순서 무관 방향=A(직전)→B(과거)."""
    exact = len(a & b)
    neigh = 0
    for x in a - b:
        if (x - 1 in b) or (x + 1 in b):
            neigh += 1
    return exact + neigh


def _bucket(score: int) -> int:
    return min(5, max(0, int(score)))


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


def _hits(actual: set[int], top: set[int]) -> int:
    return len(actual & top)


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


def _load() -> tuple[list[int], dict[int, frozenset[int]], int, int, int, int]:
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
        try:
            assoc_n = int(
                conn.execute("SELECT COUNT(*) FROM testlotto_draw_assoc").fetchone()[0]
            )
        except sqlite3.OperationalError:
            assoc_n = -1
        rows = conn.execute(
            "SELECT draw_no, num1, num2, num3, num4, num5, num6 FROM lotto_draws "
            "WHERE draw_no BETWEEN 1 AND ? ORDER BY draw_no",
            (dmax,),
        ).fetchall()
    finally:
        conn.close()
    by: dict[int, frozenset[int]] = {}
    order: list[int] = []
    for r in rows:
        dno = int(r[0])
        nums = frozenset(int(x) for x in r[1:7])
        if len(nums) != 6:
            continue
        by[dno] = nums
        order.append(dno)
    return order, by, dmax, pred_1237, pred_1239, assoc_n


def _s0() -> dict[str, Any]:
    order, by, dmax, pred_1237, pred_1239, assoc_n = _load()
    nos = [d for d in order if d in by]
    idx = {d: i for i, d in enumerate(nos)}
    t_list = [t for t in range(T_LO, T_HI + 1) if t in by and (t - 1) in by]
    t0 = time.perf_counter()
    peek_fail = 0
    n_novel = {str(th): 0 for th in THRESHS}
    # per (h, top, thr) hits
    hits: dict[tuple[int, int, int], list[int]] = {
        (h, top, th): [] for h in HORIZONS for top in TOP_NS for th in THRESHS
    }
    ctrl: dict[tuple[int, int, int], list[int]] = {
        (h, top, th): [] for h in HORIZONS for top in TOP_NS for th in THRESHS
    }
    n_sim_used: dict[tuple[int, int], list[int]] = {
        (h, th): [] for h in HORIZONS for th in THRESHS
    }
    max_bucket_hist: Counter[int] = Counter()
    bucket_count_sum: Counter[int] = Counter()
    n_bucket_t = 0
    n_scored_primary = 0
    rng = random.Random(RNG_SEED)

    for t in t_list:
        prev = t - 1
        a = by[prev]
        past_nos = [d for d in nos if d < prev]
        if not past_nos:
            for th in THRESHS:
                n_novel[str(th)] += 1
            max_bucket_hist[0] += 1
            continue
        scores: list[tuple[int, int]] = []
        bcount: Counter[int] = Counter()
        max_b = 0
        for d in past_nos:
            s = _sim(a, by[d])
            b = _bucket(s)
            bcount[b] += 1
            if b > max_b:
                max_b = b
            scores.append((d, s))
        max_bucket_hist[max_b] += 1
        for b in range(6):
            bucket_count_sum[b] += bcount[b]
        n_bucket_t += 1

        similar: dict[int, list[int]] = {}
        for th in THRESHS:
            similar[th] = [d for d, s in scores if s >= th]
            if not similar[th]:
                n_novel[str(th)] += 1

        actual = by[t]
        # peek guard: never put t into the pool
        for h in HORIZONS:
            for th in THRESHS:
                nxt_list: list[int] = []
                for s_no in similar[th]:
                    nxt = s_no + h
                    if nxt >= t:
                        continue
                    if nxt not in by:
                        continue
                    nxt_list.append(nxt)
                n_sim_used[(h, th)].append(len(nxt_list))
                freq: Counter[int] = Counter()
                for nxt in nxt_list:
                    for n in by[nxt]:
                        freq[n] += 1
                for top in TOP_NS:
                    if not freq:
                        continue
                    topset = _top_set(freq, top)
                    hits[(h, top, th)].append(_hits(actual, topset))
                    if h == PRIMARY_H and top == PRIMARY_TOP and th == PRIMARY_THR:
                        n_scored_primary += 1
                # random-past control: same count, valid next
                cand = [d for d in past_nos if (d + h) < t and (d + h) in by]
                n_take = len(nxt_list)
                if n_take and len(cand) >= n_take:
                    picked = rng.sample(cand, n_take)
                    cf: Counter[int] = Counter()
                    for d in picked:
                        for n in by[d + h]:
                            cf[n] += 1
                    for top in TOP_NS:
                        ctrl[(h, top, th)].append(_hits(actual, _top_set(cf, top)))

        # no use of `t` except actual label above
        if prev >= t:
            peek_fail += 1

    elapsed = round(time.perf_counter() - t0, 1)
    mean_bucket_n = {
        str(b): round(bucket_count_sum[b] / n_bucket_t, 4) if n_bucket_t else 0.0
        for b in range(6)
    }

    def cell(h: int, top: int, th: int) -> dict[str, Any]:
        pack = _pack_hits(hits[(h, top, th)], top)
        cpack = _pack_hits(ctrl[(h, top, th)], top) if ctrl[(h, top, th)] else {}
        used = n_sim_used[(h, th)]
        pack["mean_n_next"] = round(sum(used) / len(used), 4) if used else 0.0
        pack["control_random"] = cpack
        return pack

    primary = cell(PRIMARY_H, PRIMARY_TOP, PRIMARY_THR)
    by_h = {}
    for h in HORIZONS:
        by_h[str(h)] = cell(h, PRIMARY_TOP, PRIMARY_THR)
    by_th = {}
    for th in THRESHS:
        by_th[str(th)] = cell(PRIMARY_H, PRIMARY_TOP, th)
    by_top = {}
    for top in TOP_NS:
        by_top[str(top)] = cell(PRIMARY_H, top, PRIMARY_THR)

    # exact-only similar4 (기존 씨앗, 이웃 없이 직접겹침>=4)
    exact4_hits: list[int] = []
    for t in t_list:
        prev = t - 1
        if prev not in by:
            continue
        a = by[prev]
        freq: Counter[int] = Counter()
        for d in nos:
            if d >= prev:
                continue
            if len(a & by[d]) < 4:
                continue
            nxt = d + 1
            if nxt >= t or nxt not in by:
                continue
            for n in by[nxt]:
                freq[n] += 1
        if not freq:
            continue
        exact4_hits.append(_hits(by[t], _top_set(freq, PRIMARY_TOP)))
    exact4 = _pack_hits(exact4_hits, PRIMARY_TOP)

    return {
        "def": {
            "similarity": "exact(|A∩B|) + neighbor(a in A\\B and (a±1 in B))",
            "bucket": "min(5, score) · 0~5",
            "similar": f"score>={PRIMARY_THR}",
            "mains_only": True,
            "bonus_used": False,
            "peek": "past draw_no < T-1; next = similar+h < T; T nums = label only",
            "primary_horizon": PRIMARY_H,
            "primary_top": PRIMARY_TOP,
            "primary_thresh": PRIMARY_THR,
            "p_gate": P_GATE,
            "delta_gate": DELTA_GATE,
            "null_top6": round(6 * 6 / 45, 6),
        },
        "dmax": dmax,
        "pred_1237": pred_1237,
        "pred_1239": pred_1239,
        "assoc_n": assoc_n,
        "t_lo": T_LO,
        "t_hi": T_HI,
        "n_t": len(t_list),
        "n_bucket_t": n_bucket_t,
        "peek_fail": peek_fail,
        "elapsed_s": elapsed,
        "n_novel": n_novel,
        "n_scored_primary": n_scored_primary,
        "mean_n_past_by_bucket": mean_bucket_n,
        "n_t_max_bucket": {str(b): int(max_bucket_hist[b]) for b in range(6)},
        "primary": primary,
        "by_horizon_top6_thr4": by_h,
        "by_thresh_h1_top6": by_th,
        "by_top_h1_thr4": by_top,
        "exact_share4_h1_top6": exact4,
        "idx_note": f"nos={len(nos)} last={nos[-1] if nos else None} idx_ok={len(idx)}",
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
            f"주정의 h=1 top6 thr=4 mean={prim.get('mean_hits')} null={prim.get('null')} "
            f"Δ={delta} z={prim.get('z')} p_greater={p}. 널 대비 양의 편향. "
            "S2는 형 GO 후에만. 이번 턴 라이브 안 켬."
        )
        return "DISCUSS_OK", "WIRE_CANDIDATE", reason, "deferred_need_hyung_go"
    reason = (
        f"주정의 h=1 top6 thr=4 mean={prim.get('mean_hits')} null={prim.get('null')} "
        f"Δ={delta} z={prim.get('z')} p_greater={p} "
        f"(게이트 Δ≥{DELTA_GATE} and p<{P_GATE}). 편향 없음(또는 미달). "
        "라이브 배선 금지. 유사도는 기존 similar4/5 + 본 벤치 모니터."
    )
    return "HOLD_NO_WIRE", "HOLD_NO_WIRE", reason, "skipped"


def _write_md(doc: dict[str, Any]) -> str:
    s0 = doc["s0"]
    prim = s0["primary"]
    nb = s0["mean_n_past_by_bucket"]
    mb = s0["n_t_max_bucket"]
    lines = [
        "# K-REVIEW-SIMILAR-NEXT-VERIFY (2026-08-27)",
        "",
        f"- **판정:** `{doc['verdict']}` · S0 READ-ONLY · APPLY **없음** · 핫쌍/인기 가중 **없음** · 몰아주기 **미접촉**",
        f"- 시각: {doc['ts']}",
        "- 형: 직전 회차와 닮은 과거의 **다음 회차** 번호를 참고 신호로 쓸 수 있는지. 편향 0이어도 정상(모니터).",
        f"- 근거: `{OUT_JSON.name}`",
        "",
        "## 정의",
        "",
        "- similarity(A,B) = 본번호6 **직접겹침** `|A∩B|` + **이웃겹침** (A에만 있는 a의 a±1이 B에 있으면 1). 보너스 미사용. 순서 무관.",
        "- 버킷 = min(5, score) · 0~5단계.",
        f"- 닮음(주정의) = score ≥ **{PRIMARY_THR}**. 감도 3/5.",
        "- 타깃 T: 직전=T-1. 과거 회차 draw_no **< T-1**. 다음=닮은회차+h, **< T**. T 본번호는 채점 라벨만.",
        f"- predicted_pool = 그 다음회차 번호 빈도 상위 **{PRIMARY_TOP}**. 널 E[겹침]={s0['def']['null_top6']} (6×6/45).",
        f"- 유의미 = Δ≥{DELTA_GATE} 이고 단측 p_greater<{P_GATE} (주정의 h=1).",
        "",
        "## S0 walk-forward 2–1237",
        "",
        f"- n_T `{s0['n_t']}` peek `{s0['peek_fail']}` pred_1237 `{s0['pred_1237']}` pred_1239 `{s0['pred_1239']}` MAX `{s0['dmax']}` assoc `{s0['assoc_n']}`",
        f"- 신규(닮음0) thr3/4/5 `{s0['n_novel']}`",
        f"- 주정의 채점 n `{s0['n_scored_primary']}`",
        f"- 회당 과거 버킷평균 n `{nb}`",
        f"- T별 max버킷 도수 `{mb}`",
        f"- elapsed `{s0['elapsed_s']}`s",
        "",
        "## 주정의 h=1 top6 thr=4",
        "",
        f"- mean_hits `{prim.get('mean_hits')}` null `{prim.get('null')}` Δ `{prim.get('delta')}` z `{prim.get('z')}` p_greater `{prim.get('p_greater')}`",
        f"- hist `{prim.get('hist')}`",
        f"- 사용 다음회 평균 `{prim.get('mean_n_next')}`",
        f"- 무작위과거 통제 `{prim.get('control_random')}`",
        "",
        "## 지평 1/5/10 (top6 thr4)",
        "",
    ]
    for h in HORIZONS:
        cell = s0["by_horizon_top6_thr4"][str(h)]
        lines.append(
            f"- h={h} mean `{cell.get('mean_hits')}` Δ `{cell.get('delta')}` z `{cell.get('z')}` p `{cell.get('p_greater')}` n `{cell.get('n')}` 다음평균 `{cell.get('mean_n_next')}`"
        )
    lines += [
        "",
        "## 감도 thr·top (h=1)",
        "",
    ]
    for th in THRESHS:
        cell = s0["by_thresh_h1_top6"][str(th)]
        lines.append(
            f"- thr={th} mean `{cell.get('mean_hits')}` Δ `{cell.get('delta')}` p `{cell.get('p_greater')}` n `{cell.get('n')}`"
        )
    for top in TOP_NS:
        cell = s0["by_top_h1_thr4"][str(top)]
        lines.append(
            f"- top={top} mean `{cell.get('mean_hits')}` null `{cell.get('null')}` Δ `{cell.get('delta')}` p `{cell.get('p_greater')}` n `{cell.get('n')}`"
        )
    ex = s0["exact_share4_h1_top6"]
    lines += [
        "",
        "## 기존 씨앗(직접4겹만, 이웃 없음) h=1 top6",
        "",
        f"- mean `{ex.get('mean_hits')}` Δ `{ex.get('delta')}` z `{ex.get('z')}` p `{ex.get('p_greater')}` n `{ex.get('n')}` hist `{ex.get('hist')}`",
        "",
        "## S1 판정",
        "",
        f"- `{doc['s1']}`",
        f"- 사유: {doc['reason']}",
        f"- S2 `{doc['s2']}`",
        "- `REVIEW_SIMILAR_NEXT_WIRE` **신설하지 않음**(배선 분기 아님). 엔진·stat/markov·7번 WIRE **불변**.",
        "- 모니터: 기존 `testlotto_draw_assoc` similar4/5 + 본 JSON. 신설 테이블 없음.",
        "",
        "## 이번 턴에 하지 않음",
        "",
        "- T 번호를 유사도·풀에 입력 — 금지.",
        "- 보너스 재료 · 인기쌍 가중 · 몰아주기 · 전체조합 · `random.choices` · kweon · 자동화 · 1237예측 · APPLY.",
        "",
        "## 롤백",
        "",
        "- WIRE 키: **해당 없음**(플래그 없음). 읽기 기존: `REVIEW_ASSOC_KB_READ=False`",
        "",
        "## 파일",
        "",
        f"- `{OUT_JSON.name}` · `{OUT_MD.name}`",
    ]
    return "\n".join(lines)


def main() -> None:
    print("S0 similar-next", flush=True)
    s0 = _s0()
    verdict, s1, reason, s2 = _s1_from(s0)
    # HOLD 분기에서 md 문장 고정(배선 후보면 따로)
    doc = {
        "id": "K-REVIEW-SIMILAR-NEXT-VERIFY",
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
        "ko": "hits=가설검정모니터·성적클레임아님",
    }
    if s1 != "HOLD_NO_WIRE":
        # rewrite s2 note in json only; md writer uses skipped text for HOLD
        pass
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _write_md(doc)
    if s1 != "HOLD_NO_WIRE":
        md = md.replace(
            "- `REVIEW_SIMILAR_NEXT_WIRE` **신설하지 않음**(배선 분기 아님). 엔진·stat/markov·7번 WIRE **불변**.",
            "- S2는 형 GO 후. 이번 턴 `REVIEW_SIMILAR_NEXT_WIRE` 라이브 **안 켬**.",
        )
        md = md.replace(
            "- WIRE 키: **해당 없음**(플래그 없음). 읽기 기존: `REVIEW_ASSOC_KB_READ=False`",
            "- 배선 시 롤백: `REVIEW_SIMILAR_NEXT_WIRE=False` (이번 턴 미신설이면 해당없음)",
        )
    OUT_MD.write_text(md + "\n", encoding="utf-8")
    prim = s0["primary"]
    print(
        verdict,
        "mean",
        prim.get("mean_hits"),
        "delta",
        prim.get("delta"),
        "p",
        prim.get("p_greater"),
        "novel4",
        s0["n_novel"].get("4"),
        flush=True,
    )


if __name__ == "__main__":
    main()
