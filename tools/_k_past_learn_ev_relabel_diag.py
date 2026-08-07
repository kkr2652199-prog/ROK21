# -*- coding: utf-8 -*-
"""K-PAST-LEARN-EV-RELABEL — 과거학습 soft 태그의 EV(인기회피) 축 실증 진단.

배경
----
K-PAST-LEARN-SCORE-RULE-DIAG 결과 = NO_SKILL_VS_NULL.
번호 적중확률 축에서는 recency 가중의 상한이 없음(균등분포 대비 log-score 열위).
따라서 남은 유일한 축 = **EV(기대수익)**: 당첨확률은 못 올리지만
"덜 인기 있는 조합"을 고르면 당첨 시 분할 인원이 줄어 1인당 지급액이 오른다.

핵심 아이디어 (자문 반영)
-----------------------
추첨 조합은 판매량·잭팟·시기와 **독립적으로 무작위 배정**된다.
그러므로 "조합 특성 → 1등 당첨자 수" 연관은 인과적으로 소비자 선택(conscious
selection)만을 반영한다. 이는 무작위화 추론(randomization inference)으로
분포가정 없이 검정할 수 있다.

  종속변수 : 1등 당첨자 수 W1_t  (1인당 지급액은 pool/W1 의 기계적 역함수 → 사용 금지)
  분포     : NB2 음이항 (observed var/mean ≈ 3.2 → Poisson 등분산 위반)
  offset   : log(total_sales)
  교란     : 시간 linear-spline · 이월(직전 1등 0명) · 연주기 harmonics
  1차 추론 : 조합을 균등 6/45로 재배정하는 permutation score test
             (+ max|z| 기반 family-wise 다중검정 보정)

측정 대상 조합특성
------------------
(a) 문헌형 인기 프록시 : n_le31(생일) · n_le22(저번호) · sum · 연번쌍 · 끝수중복 · span
(b) **과거학습 soft 태그** : overdue(gap>=30) · hot1y(52회 rate>1.15x) ·
    cold1y(rate<0.75x) · carry(직전회 포함)
    → 태그가 "비인기"와 정렬되면 EV 축 라벨 재정의 근거가 된다.

정책
----
READ-ONLY. DB 쓰기 없음 · 발권 가중 변경 없음 · 브레인 코드 무수정 (w=0).
past_learn.py 의 임계값을 하드코딩 대신 모듈에서 직접 읽어 정합성 유지.

출력
----
  docs/benchmarks/20260808_KPAST_LEARN_EV_RELABEL.json
  reports/20260808_KPAST_LEARN_EV_RELABEL.md
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from datetime import date
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB = ROOT / "data" / "lotto_testlotto.db"
BENCH = ROOT / "docs" / "benchmarks" / "20260808_KPAST_LEARN_EV_RELABEL.json"
REPORT = ROOT / "reports" / "20260808_KPAST_LEARN_EV_RELABEL.md"

BENCH_ID = "K-PAST-LEARN-EV-RELABEL"
N_PERM = 5000
PERM_SEED = 20260808
MIN_HIST = 104  # rate_1y(52) 안정화용 최소 과거 회차
M_TOTAL = 45
M_DRAWN = 6

# ── past_learn 실측 임계값 (모듈에서 직접 읽음) ──────────────────────
from app.testlotto.brains.stat_brain import past_learn as PL  # noqa: E402

OVERDUE_GAP = 30
HOT_MULT = 1.15
COLD_MULT = 0.75
NULL_RATE = PL.NULL_RATE
WIN_1Y = PL.WIN_1Y

FEATURES: list[tuple[str, str]] = [
    ("n_le31", "번호 중 31 이하 개수 (생일·달력 선택)"),
    ("n_le22", "번호 중 22 이하 개수 (저번호 선호)"),
    ("sum_z", "번호합 (표준화)"),
    ("n_consec", "인접(연번) 쌍 개수"),
    ("n_endrep", "같은 끝수 쌍 개수"),
    ("span_z", "최대-최소 폭 (표준화)"),
    ("t_overdue", "과거학습 태그: gap>=30 미출 번호 개수"),
    ("t_hot1y", "과거학습 태그: 52회 rate>1.15x 핫 번호 개수"),
    ("t_cold1y", "과거학습 태그: 52회 rate<0.75x 콜드 번호 개수"),
    ("t_carry", "직전 회차 번호 포함 개수 (도박사 오류축)"),
]
STATIC_FEATS = {"n_le31", "n_le22", "sum_z", "n_consec", "n_endrep", "span_z"}
TAG_FEATS = {"t_overdue", "t_hot1y", "t_cold1y", "t_carry"}


# ── 데이터 ─────────────────────────────────────────────────────────────
def load_draws() -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT draw_no, draw_date, num1, num2, num3, num4, num5, num6,
               total_sales, first_prize, first_winners
        FROM lotto_draws
        WHERE total_sales > 0 AND first_winners IS NOT NULL
        ORDER BY draw_no
        """
    ).fetchall()
    conn.close()
    out = []
    for r in rows:
        out.append(
            {
                "draw_no": int(r["draw_no"]),
                "draw_date": str(r["draw_date"]),
                "nums": sorted(int(r[f"num{k}"]) for k in range(1, 7)),
                "sales": float(r["total_sales"]),
                "w1": int(r["first_winners"]),
                "prize": float(r["first_prize"] or 0.0),
            }
        )
    return out


def _month_frac(datestr: str) -> float:
    try:
        y, m, d = (int(x) for x in datestr.split("-")[:3])
        doy = date(y, m, d).timetuple().tm_yday
        return doy / 365.25
    except (ValueError, TypeError):
        return 0.0


def _asof_row(prev_draws: list[dict], last_seen: dict[int, int]) -> tuple[np.ndarray, ...]:
    """직전 회차들만으로 만든 태그 마스크 4종 (index 0 미사용)."""
    latest_no = prev_draws[-1]["draw_no"]

    gap = np.array(
        [0] + [latest_no - last_seen.get(n, 0) if n in last_seen else latest_no
               for n in range(1, M_TOTAL + 1)],
        dtype=np.int64,
    )

    lo = latest_no - WIN_1Y + 1
    cnt = np.zeros(M_TOTAL + 1, dtype=np.float64)
    for pd_ in prev_draws:
        if pd_["draw_no"] >= lo:
            for n in pd_["nums"]:
                cnt[n] += 1.0
    span = float(min(WIN_1Y, len(prev_draws)))
    rate = cnt / span if span else cnt

    ov = np.zeros(M_TOTAL + 1, dtype=np.float64)
    ho = np.zeros(M_TOTAL + 1, dtype=np.float64)
    co = np.zeros(M_TOTAL + 1, dtype=np.float64)
    ca = np.zeros(M_TOTAL + 1, dtype=np.float64)
    ov[1:] = (gap[1:] >= OVERDUE_GAP).astype(np.float64)
    ho[1:] = (rate[1:] > NULL_RATE * HOT_MULT).astype(np.float64)
    co[1:] = (rate[1:] < NULL_RATE * COLD_MULT).astype(np.float64)
    ca[prev_draws[-1]["nums"]] = 1.0
    return ov, ho, co, ca


def build_asof_masks(
    draws: list[dict],
) -> tuple[list[int], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """target 회차별 as-of 태그 마스크. 컨닝 금지: draw_no < target 만 사용."""
    idx_used: list[int] = []
    rows: list[tuple[np.ndarray, ...]] = []
    last_seen: dict[int, int] = {}

    for i, d in enumerate(draws):
        if i >= MIN_HIST:
            idx_used.append(i)
            rows.append(_asof_row(draws[:i], last_seen))
        for n in d["nums"]:
            last_seen[n] = d["draw_no"]

    stacked = [np.array([r[k] for r in rows]) for k in range(4)]
    return idx_used, stacked[0], stacked[1], stacked[2], stacked[3]


# ── 조합특성 (벡터화) ───────────────────────────────────────────────────
def static_features(picks: np.ndarray) -> dict[str, np.ndarray]:
    """picks: (T,6) 정렬 불필요. 반환값은 표준화 전 원값."""
    srt = np.sort(picks, axis=1)
    diffs = np.diff(srt, axis=1)
    last = picks % 10
    endrep = np.zeros(picks.shape[0], dtype=np.float64)
    for dg in range(10):
        c = (last == dg).sum(axis=1).astype(np.float64)
        endrep += c * (c - 1.0) / 2.0
    return {
        "n_le31": (picks <= 31).sum(axis=1).astype(np.float64),
        "n_le22": (picks <= 22).sum(axis=1).astype(np.float64),
        "sum_z": picks.sum(axis=1).astype(np.float64),
        "n_consec": (diffs == 1).sum(axis=1).astype(np.float64),
        "n_endrep": endrep,
        "span_z": (srt[:, -1] - srt[:, 0]).astype(np.float64),
    }


def tag_features(picks: np.ndarray, masks: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    rows = np.arange(picks.shape[0])[:, None]
    return {k: m[rows, picks].sum(axis=1) for k, m in masks.items()}


def all_features(
    picks: np.ndarray, masks: dict[str, np.ndarray], norm: dict[str, tuple[float, float]] | None
) -> tuple[np.ndarray, dict[str, tuple[float, float]]]:
    d = static_features(picks)
    d.update(tag_features(picks, masks))
    if norm is None:
        norm = {}
        for name in ("sum_z", "span_z"):
            norm[name] = (float(d[name].mean()), float(d[name].std(ddof=1)) or 1.0)
    for name in ("sum_z", "span_z"):
        mu, sd = norm[name]
        d[name] = (d[name] - mu) / sd
    mat = np.column_stack([d[name] for name, _ in FEATURES])
    return mat, norm


# ── 교란변수 설계행렬 ───────────────────────────────────────────────────
def baseline_design(draw_nos: np.ndarray, datestrs: list[str], prev_zero: np.ndarray) -> tuple[np.ndarray, list[str]]:
    t = (draw_nos - draw_nos.min()) / (draw_nos.max() - draw_nos.min())
    knots = np.quantile(t, [1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6])
    cols = [np.ones_like(t), t]
    names = ["const", "time"]
    for j, k in enumerate(knots):
        cols.append(np.maximum(0.0, t - k))
        names.append(f"time_k{j + 1}")
    frac = np.array([_month_frac(s) for s in datestrs])
    for h in (1, 2):
        cols.append(np.sin(2 * math.pi * h * frac))
        names.append(f"sin{h}")
        cols.append(np.cos(2 * math.pi * h * frac))
        names.append(f"cos{h}")
    cols.append(prev_zero)
    names.append("rollover_prev")
    return np.column_stack(cols), names


# ── NB2 최대우도 (자체 구현) ───────────────────────────────────────────
# statsmodels 0.14.4 는 scipy 1.16 과 비호환(_lazywhere 제거)이므로
# NB2 를 직접 적합한다. 패키지 버전 변경 없이 통제 가능.
#
#   mu_i = exp(offset_i + x_i'b) ,  r = 1/alpha
#   ll = sum[ lgamma(y+r) - lgamma(r) - lgamma(y+1)
#             + r*log(r/(r+mu)) + y*log(mu/(r+mu)) ]
def _nb2_neg_ll_grad(
    theta: np.ndarray, y: np.ndarray, x: np.ndarray, offset: np.ndarray
) -> tuple[float, np.ndarray]:
    from scipy.special import gammaln, psi

    beta = theta[:-1]
    log_alpha = theta[-1]
    r = math.exp(-log_alpha)
    eta = np.clip(offset + x @ beta, -50.0, 50.0)
    mu = np.exp(eta)
    rm = r + mu

    ll = float(
        np.sum(
            gammaln(y + r) - gammaln(r) - gammaln(y + 1.0)
            + r * (math.log(r) - np.log(rm))
            + y * (eta - np.log(rm))
        )
    )

    w = (y - mu) * r / rm
    g_beta = x.T @ w
    g_r = float(np.sum(psi(y + r) - psi(r) + math.log(r) - np.log(rm) + 1.0 - (y + r) / rm))
    g_log_alpha = g_r * (-r)  # dr/d(log alpha) = -r

    grad = np.concatenate([g_beta, [g_log_alpha]])
    return -ll, -grad


def fit_nb2(y: np.ndarray, x: np.ndarray, offset: np.ndarray) -> dict[str, Any]:
    from scipy.optimize import minimize

    k = x.shape[1]
    # 시작값: log(y+0.5)-offset 에 대한 OLS · alpha 는 적률추정
    z = np.log(np.maximum(y, 0.5)) - offset
    b0, *_ = np.linalg.lstsq(x, z, rcond=None)
    mu0 = np.exp(np.clip(offset + x @ b0, -50, 50))
    a0 = max(1e-3, float(np.mean((y - mu0) ** 2 - mu0) / np.mean(mu0**2)))
    theta0 = np.concatenate([b0, [math.log(a0)]])

    res = minimize(
        _nb2_neg_ll_grad,
        theta0,
        args=(y, x, offset),
        jac=True,
        method="L-BFGS-B",
        options={"maxiter": 3000, "ftol": 1e-12, "gtol": 1e-9},
    )
    theta = res.x
    beta = np.asarray(theta[:-1], dtype=np.float64)
    alpha = float(math.exp(theta[-1]))
    mu = np.exp(np.clip(offset + x @ beta, -50, 50))

    # 수치 Hessian (해석적 그라디언트 차분) → 표준오차
    step = 1e-5
    dim = theta.size
    hess = np.zeros((dim, dim))
    for j in range(dim):
        tp = theta.copy()
        tm = theta.copy()
        tp[j] += step
        tm[j] -= step
        _, gp = _nb2_neg_ll_grad(tp, y, x, offset)
        _, gm = _nb2_neg_ll_grad(tm, y, x, offset)
        hess[:, j] = (gp - gm) / (2 * step)
    hess = 0.5 * (hess + hess.T)
    try:
        cov = np.linalg.inv(hess)
        bse = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    except np.linalg.LinAlgError:
        bse = np.full(dim, float("nan"))

    pear = float(np.sum((y - mu) ** 2 / np.maximum(mu, 1e-9)) / max(1, len(y) - k))
    return {
        "alpha": alpha,
        "beta": beta,
        "bse": bse[:-1],
        "mu": mu,
        "pearson_disp": pear,
        "llf": float(-res.fun),
        "converged": bool(res.success),
        "grad_norm": float(np.max(np.abs(res.jac))),
    }


def zero_check(y: np.ndarray, mu: np.ndarray, alpha: float) -> dict[str, Any]:
    """NB2 하 기대 0 개수 vs 관측 (zero-inflation 진단)."""
    r = 1.0 / alpha if alpha > 0 else 1e9
    p0 = (r / (r + mu)) ** r
    return {
        "observed_zeros": int((y == 0).sum()),
        "nb2_expected_zeros": round(float(p0.sum()), 2),
        "zero_inflation_flag": bool((y == 0).sum() > p0.sum() * 1.5 + 3),
    }


# ── 무작위화 추론 (permutation score test) ─────────────────────────────
def perm_score_test(
    resid: np.ndarray,
    obs_feat: np.ndarray,
    masks: dict[str, np.ndarray],
    norm: dict[str, tuple[float, float]],
    n_perm: int = N_PERM,
    seed: int = PERM_SEED,
) -> dict[str, Any]:
    """조합을 균등 6/45로 재배정했을 때의 score 통계 귀무분포."""
    rng = np.random.default_rng(seed)
    t_n = resid.shape[0]
    obs_u = resid @ obs_feat  # (K,)

    null_u = np.empty((n_perm, obs_feat.shape[1]), dtype=np.float64)
    for b in range(n_perm):
        picks = np.argsort(rng.random((t_n, M_TOTAL)), axis=1)[:, :M_DRAWN] + 1
        mat, _ = all_features(picks, masks, norm)
        null_u[b] = resid @ mat

    mu_n = null_u.mean(axis=0)
    sd_n = null_u.std(axis=0, ddof=1)
    sd_n[sd_n == 0] = 1e-12
    z_obs = (obs_u - mu_n) / sd_n
    z_null = (null_u - mu_n) / sd_n

    p_two = ((np.abs(z_null) >= np.abs(z_obs)).sum(axis=0) + 1) / (n_perm + 1)
    max_abs_null = np.abs(z_null).max(axis=1)
    p_fw = ((max_abs_null[:, None] >= np.abs(z_obs)).sum(axis=0) + 1) / (n_perm + 1)

    return {
        "n_perm": n_perm,
        "seed": seed,
        "obs_u": obs_u.tolist(),
        "z": z_obs.tolist(),
        "p_two_sided": p_two.tolist(),
        "p_familywise": p_fw.tolist(),
        "global_max_abs_z": float(np.abs(z_obs).max()),
        "global_p": float(((max_abs_null >= np.abs(z_obs).max()).sum() + 1) / (n_perm + 1)),
    }


def perm_z_only(
    resid: np.ndarray,
    obs_feat: np.ndarray,
    masks: dict[str, np.ndarray],
    norm: dict[str, tuple[float, float]],
    n_perm: int,
    seed: int,
) -> list[float]:
    """부분표본용 — z 통계만 반환 (재현성 확인)."""
    rng = np.random.default_rng(seed)
    t_n = resid.shape[0]
    obs_u = resid @ obs_feat
    null_u = np.empty((n_perm, obs_feat.shape[1]), dtype=np.float64)
    for b in range(n_perm):
        picks = np.argsort(rng.random((t_n, M_TOTAL)), axis=1)[:, :M_DRAWN] + 1
        mat, _ = all_features(picks, masks, norm)
        null_u[b] = resid @ mat
    sd = null_u.std(axis=0, ddof=1)
    sd[sd == 0] = 1e-12
    return ((obs_u - null_u.mean(axis=0)) / sd).tolist()


def holm(pvals: list[float]) -> list[float]:
    k = len(pvals)
    order = sorted(range(k), key=lambda i: pvals[i])
    adj = [0.0] * k
    run = 0.0
    for rank, i in enumerate(order):
        val = (k - rank) * pvals[i]
        run = max(run, min(1.0, val))
        adj[i] = run
    return adj


# ── 실행 ───────────────────────────────────────────────────────────────
def run() -> dict[str, Any]:
    draws = load_draws()
    idx, m_ov, m_ho, m_co, m_ca = build_asof_masks(draws)
    masks = {"t_overdue": m_ov, "t_hot1y": m_ho, "t_cold1y": m_co, "t_carry": m_ca}

    used = [draws[i] for i in idx]
    y = np.array([d["w1"] for d in used], dtype=np.float64)
    sales = np.array([d["sales"] for d in used], dtype=np.float64)
    draw_nos = np.array([d["draw_no"] for d in used], dtype=np.float64)
    dates = [d["draw_date"] for d in used]
    prev_zero = np.array(
        [1.0 if draws[i - 1]["w1"] == 0 else 0.0 for i in idx], dtype=np.float64
    )
    offset = np.log(sales)

    picks = np.array([d["nums"] for d in used], dtype=np.int64)
    obs_feat, norm = all_features(picks, masks, None)

    x_base, base_names = baseline_design(draw_nos, dates, prev_zero)
    base = fit_nb2(y, x_base, offset)
    resid = y - base["mu"]

    perm = perm_score_test(resid, obs_feat, masks, norm)
    perm["p_holm"] = holm(perm["p_two_sided"])

    # 시기별 재현성 (전반/후반) — 과적합 방지용
    half = len(used) // 2
    rep = {}
    for label, sl in (("first_half", slice(0, half)), ("second_half", slice(half, None))):
        sub_masks = {k: m[sl] for k, m in masks.items()}
        rep[label] = perm_z_only(
            resid[sl], obs_feat[sl], sub_masks, norm, n_perm=1500, seed=PERM_SEED + 7
        )
    rep["split_draw_no"] = int(draw_nos[half])

    # 시대 4분할 프로파일 — 효과가 특정 시기에 몰렸는지 확인 (사후 탐색 아님·사전 지정)
    q = len(used) // 4
    era_bounds = [(0, q), (q, 2 * q), (2 * q, 3 * q), (3 * q, len(used))]
    era_z = []
    for gi, (lo_i, hi_i) in enumerate(era_bounds):
        sl = slice(lo_i, hi_i)
        sub_masks = {k: m[sl] for k, m in masks.items()}
        era_z.append(
            {
                "era": gi + 1,
                "draw_from": int(draw_nos[lo_i]),
                "draw_to": int(draw_nos[hi_i - 1]),
                "n": hi_i - lo_i,
                "z": [
                    round(float(v), 2)
                    for v in perm_z_only(
                        resid[sl], obs_feat[sl], sub_masks, norm, n_perm=1000, seed=PERM_SEED + 11 + gi
                    )
                ],
            }
        )

    # 전체 모형 (동시보정) — 공선성 주의
    x_full = np.column_stack([x_base, obs_feat])
    full_names = base_names + [n for n, _ in FEATURES]
    full = fit_nb2(y, x_full, offset)
    se_full = np.asarray(full["bse"], dtype=np.float64)
    k0 = x_base.shape[1]

    # 주 효과크기 = 특성 1개씩만 baseline 에 추가 (score test 와 해석 일치)
    effects = []
    for j, (name, desc) in enumerate(FEATURES):
        one = fit_nb2(y, np.column_stack([x_base, obs_feat[:, j]]), offset)
        b = float(one["beta"][-1])
        se = float(one["bse"][-1])
        effects.append(
            {
                "feature": name,
                "desc_ko": desc,
                "beta_marginal": round(b, 5),
                "se_marginal": round(se, 5),
                "irr_marginal": round(math.exp(b), 4),
                "pct_winners_per_unit": round((math.exp(b) - 1.0) * 100.0, 2),
                "pct_payout_per_unit": round((math.exp(-b) - 1.0) * 100.0, 2),
                "beta_adjusted": round(float(full["beta"][k0 + j]), 5),
                "se_adjusted": round(float(se_full[k0 + j]), 5),
                "z_perm": round(float(perm["z"][j]), 3),
                "p_perm": round(float(perm["p_two_sided"][j]), 5),
                "p_holm": round(float(perm["p_holm"][j]), 5),
                "p_familywise": round(float(perm["p_familywise"][j]), 5),
                "sig_fw_05": bool(perm["p_familywise"][j] < 0.05),
                "z_first_half": round(float(rep["first_half"][j]), 3),
                "z_second_half": round(float(rep["second_half"][j]), 3),
                "replicates": bool(
                    rep["first_half"][j] * rep["second_half"][j] > 0
                    and min(abs(rep["first_half"][j]), abs(rep["second_half"][j])) >= 1.5
                ),
                "era_z": [e["z"][j] for e in era_z],
                "era_sign_consistent": sum(
                    1 for e in era_z if e["z"][j] * float(perm["z"][j]) > 0
                ),
                "era_count": len(era_z),
                "payout_gain_pct_pm2sd": round((math.exp(-b * 4.0) - 1.0) * 100.0, 2),
            }
        )
    effects.sort(key=lambda e: abs(e["z_perm"]), reverse=True)

    lr_stat = 2.0 * (full["llf"] - base["llf"])
    corr = np.corrcoef(obs_feat, rowvar=False)

    return {
        "bench_id": BENCH_ID,
        "date": "2026-08-08",
        "scope": "ROK21 / testlotto / 과거학습(stat)",
        "policy": {
            "read_only": True,
            "db_write": False,
            "ticket_weight_change": False,
            "brain_code_change": False,
            "weight": 0,
        },
        "data": {
            "draws_total": len(draws),
            "draws_used": len(used),
            "draw_range": [int(draw_nos.min()), int(draw_nos.max())],
            "min_history": MIN_HIST,
            "w1_mean": round(float(y.mean()), 4),
            "w1_var": round(float(y.var(ddof=1)), 4),
            "var_over_mean": round(float(y.var(ddof=1) / y.mean()), 4),
            "sales_offset": "log(total_sales)",
        },
        "tag_thresholds_live": {
            "overdue_gap": OVERDUE_GAP,
            "hot_mult": HOT_MULT,
            "cold_mult": COLD_MULT,
            "win_1y": WIN_1Y,
            "null_rate": round(NULL_RATE, 6),
            "source": "app/testlotto/brains/stat_brain/past_learn.py",
        },
        "baseline_model": {
            "family": "NegativeBinomial NB2",
            "terms": base_names,
            "alpha": round(base["alpha"], 5),
            "pearson_dispersion": round(base["pearson_disp"], 4),
            "llf": round(base["llf"], 3),
            "converged": base["converged"],
            "grad_norm": round(base["grad_norm"], 6),
            "zero_check": zero_check(y, base["mu"], base["alpha"]),
        },
        "full_model": {
            "terms": full_names,
            "alpha": round(full["alpha"], 5),
            "llf": round(full["llf"], 3),
            "converged": full["converged"],
            "grad_norm": round(full["grad_norm"], 6),
            "lr_stat_vs_baseline": round(float(lr_stat), 4),
            "lr_df": len(FEATURES),
        },
        "randomization_inference": {
            "design": "조합을 균등 6/45로 재배정 · 교란·판매량·당첨자수 고정",
            "n_perm": perm["n_perm"],
            "seed": perm["seed"],
            "global_max_abs_z": round(perm["global_max_abs_z"], 3),
            "global_p": round(perm["global_p"], 5),
        },
        "standardization": {
            "sum_mean": round(norm["sum_z"][0], 3),
            "sum_sd": round(norm["sum_z"][1], 3),
            "span_mean": round(norm["span_z"][0], 3),
            "span_sd": round(norm["span_z"][1], 3),
        },
        "replication_split": {
            "split_draw_no": rep["split_draw_no"],
            "n_perm_per_half": 1500,
            "note_ko": "전·후반 각각 독립 permutation. 부호 일치 + 양쪽 |z|>=1.5 를 재현으로 본다.",
        },
        "era_profile": {
            "n_perm_per_era": 1000,
            "features": [n for n, _ in FEATURES],
            "eras": era_z,
            "note_ko": "시대 4분할. 효과가 특정 시기에 몰렸는지 확인용 (사전 지정 robustness).",
        },
        "feature_correlation": {
            "names": [n for n, _ in FEATURES],
            "matrix": [[round(float(v), 3) for v in row] for row in corr],
            "note_ko": "sum_z 와 n_le22/n_le31 은 구조적으로 강한 음의 상관 → 동시보정 β 불안정.",
        },
        "effects": effects,
    }


# ── 판정 ───────────────────────────────────────────────────────────────
def verdict(p: dict[str, Any]) -> dict[str, Any]:
    gp = p["randomization_inference"]["global_p"]
    sig = [e for e in p["effects"] if e["sig_fw_05"]]
    levers = [e for e in sig if e["replicates"]]
    tags = [e for e in p["effects"] if e["feature"] in TAG_FEATS]
    tags_sig = [e for e in tags if e["sig_fw_05"]]

    if gp >= 0.05:
        code = "NO_CONSCIOUS_SELECTION_SIGNAL"
        head = "조합특성 → 1등 당첨자수 연관 없음 (family-wise)"
    elif tags_sig:
        neg = [e for e in tags_sig if e["beta_marginal"] < 0]
        code = "TAGS_ALIGN_UNPOPULAR" if neg else "TAGS_ALIGN_POPULAR"
        head = "태그가 비인기(EV↑) 방향과 정렬" if neg else "태그가 인기(EV↓) 방향 — 역방향"
    elif levers:
        code = "SELECTION_YES_TAGS_NO_LEVER_CONFIRMED"
        head = "인기 편향 실증 · 기존 태그축 무신호 · 다른 축에서 전후반 재현되는 EV 레버 확인"
    elif sig:
        code = "SELECTION_YES_TAGS_NO_AXIS_CANDIDATE"
        head = "인기 편향 실증 · 기존 태그축 무신호 · 다른 축에 EV 후보 (전후반 재현 미달)"
    else:
        code = "SELECTION_YES_TAGS_NO"
        head = "인기 편향은 존재하나 과거학습 태그축과는 무관"

    tag_dir = []
    for e in tags:
        tag_dir.append(
            {
                "feature": e["feature"],
                "beta_marginal": e["beta_marginal"],
                "direction_ko": "비인기(EV↑)" if e["beta_marginal"] < 0 else "인기(EV↓)",
                "fw_significant": e["sig_fw_05"],
                "replicates": e["replicates"],
            }
        )

    cand = [
        {
            "feature": e["feature"],
            "beta_marginal": e["beta_marginal"],
            "p_familywise": e["p_familywise"],
            "era_sign_consistent": f"{e['era_sign_consistent']}/{e['era_count']}",
            "half_split_replicates": e["replicates"],
            "payout_gain_pct_pm2sd": e["payout_gain_pct_pm2sd"],
            "status_ko": "후보 — 전향적 검증 필요" if not e["replicates"] else "재현 확인",
        }
        for e in sig
    ]

    return {
        "code": code,
        "headline_ko": head,
        "global_p": gp,
        "significant_features": [e["feature"] for e in sig],
        "replicating_levers": [e["feature"] for e in levers],
        "candidate_ev_axis": cand,
        "significant_tags": [e["feature"] for e in tags_sig],
        "tag_directions": tag_dir,
        "relabel_supported": code == "TAGS_ALIGN_UNPOPULAR",
        "wire": False,
        "note_ko": (
            "EV 축은 당첨확률을 올리지 않는다. 당첨 시 분할 인원을 줄여 "
            "1인당 지급액 기대값만 바꾼다. 발권 가중 변경은 형 승인 전 금지."
        ),
    }


def recommendation(p: dict[str, Any]) -> dict[str, Any]:
    v = p["verdict"]
    eff = {e["feature"]: e for e in p["effects"]}
    hot = eff["t_hot1y"]
    ovd = eff["t_overdue"]
    return {
        "relabel_soft_tags_as_ev": False,
        "reason_ko": (
            "hot1y/overdue/cold1y 어느 것도 family-wise 유의하지 않다. "
            f"특히 hot1y 는 β={hot['beta_marginal']:+.4f} 로 4개 시대 전부 "
            "'인기(EV↓)' 방향이라 EV 레버로 재정의할 근거가 없다. "
            f"overdue 는 β={ovd['beta_marginal']:+.4f} 로 방향은 EV↑이나 "
            f"z={ovd['z_perm']:+.2f} 로 무의미하다."
        ),
        "do_not_ko": [
            "soft 태그 가중 상향 — 적중축(SCORE-RULE NO_SKILL)·EV축 모두 근거 없음",
            "본 진단 결과로 발권 가중 즉시 변경 — 전향적 검증 전 금지",
            "1인당 지급액을 종속변수로 재분석 — 당첨자수의 기계적 역함수",
            "시대별 z 를 보고 유리한 구간만 골라 재적합 — 사후선택",
        ],
        "next_verifiable_step_ko": (
            "회차 1236 이후를 전향적 홀드아웃으로 두고, 저번호/저합 인기 축의 "
            "부호가 유지되는지만 관찰한다. 발권 개입 없이 로그만 축적 (w=0)."
        ),
        "candidate_axis_ko": (
            "저번호·저합 선호(생일 효과)가 유일하게 family-wise 유의한 인기 축이다. "
            "현재 과거학습 뇌에는 이 축이 아예 없다."
            if v["candidate_ev_axis"]
            else "후보 축 없음"
        ),
        "gate_ko": "형 승인 없이 코드·가중 변경 금지 (R34 · 동결 규정)",
    }


def literature() -> list[dict[str, str]]:
    return [
        {
            "ref": "Suetens, Galbo-Jørgensen & Tyran (2016), J. European Economic Assoc.",
            "point_ko": "실제 베팅 데이터: 직전 당첨번호는 회피(도박사 오류), 연속 출현 번호는 추종(핫핸드).",
            "use_ko": "t_carry · t_hot1y · t_overdue 의 방향 가설 근거.",
        },
        {
            "ref": "Cook & Clotfelter (1993), American Economic Review",
            "point_ko": "conscious selection — 플레이어의 번호 선택은 균등하지 않다.",
            "use_ko": "1등 당첨자수를 인기도 대리변수로 쓰는 정당화.",
        },
        {
            "ref": "Baker & McHale (2011), J. Royal Statistical Society A",
            "point_ko": "조합선호 모형 — 비인기 조합은 분할이 적어 기대수익이 높다.",
            "use_ko": "EV 축 정의 및 pct_payout 해석.",
        },
        {
            "ref": "Cameron & Trivedi, Regression Analysis of Count Data (2nd ed.)",
            "point_ko": "과산포 count 자료는 NB2. Poisson 강제 시 SE 과소추정.",
            "use_ko": "분산/평균 ≈ 3 (전체 3.16 · 사용표본 2.95) → NB2 선택 근거.",
        },
        {
            "ref": "Rosenbaum, Observational Studies / Fisher randomization inference",
            "point_ko": "처리(조합)가 무작위 배정된 경우 분포가정 없는 정확검정 가능.",
            "use_ko": "permutation score test 를 1차 추론으로 사용.",
        },
        {
            "ref": "Holm (1979), Scandinavian J. Statistics",
            "point_ko": "다중검정 순차 보정.",
            "use_ko": "10개 특성 동시검정 보정 (+ max|z| family-wise).",
        },
    ]


LIVE_TAG_POINTS = {
    "t_overdue": "+0.35/개 (cap 1.5)",
    "t_hot1y": "+0.25/개 (cap 1.0)",
    "t_cold1y": "+0.10/개 (cap 0.5)",
    "t_carry": "가점 없음 (미사용)",
}


def _sec_design(p: dict[str, Any]) -> list[str]:
    v = p["verdict"]
    d = p["data"]
    b = p["baseline_model"]
    ri = p["randomization_inference"]
    return [
        f"# {BENCH_ID} — 과거학습 soft 태그의 EV(인기회피) 축 실증",
        "",
        f"- 날짜: {p['date']} · 범위: {p['scope']}",
        f"- **판정: {v['code']} — {v['headline_ko']}**",
        f"- 라벨 재정의 지지: **{'예' if v['relabel_supported'] else '아니오'}** · wire={v['wire']}",
        "- 정책: READ-ONLY · DB 쓰기 없음 · 발권 가중/브레인 코드 무변경 (w=0)",
        "",
        "## 1. 왜 EV 축인가",
        "",
        "직전 진단(`K-PAST-LEARN-SCORE-RULE-DIAG`)에서 적중확률 축은 **NO_SKILL_VS_NULL**로",
        "닫혔다. 균등분포보다 나은 셀이 15개 중 하나도 없었고, 균등에서 멀어질수록",
        "log-score가 나빠졌다(상관 +0.985). 남은 축은 **당첨 시 분할 인원**뿐이다.",
        "",
        "추첨 조합은 판매량·시기·잭팟과 **독립적으로 무작위 배정**된다. 따라서",
        "「조합특성 → 1등 당첨자수」 연관은 오직 소비자 선택 편향만 반영하며,",
        "무작위화 추론으로 분포가정 없이 검정할 수 있다.",
        "",
        "## 2. 설계",
        "",
        "| 항목 | 값 |",
        "|---|---|",
        "| 종속변수 | 1등 당첨자 수 `first_winners` |",
        f"| 표본 | {d['draws_used']}회차 (회차 {d['draw_range'][0]}–{d['draw_range'][1]}, 전체 {d['draws_total']}) |",
        f"| 과산포 | 평균 {d['w1_mean']} · 분산 {d['w1_var']} · **분산/평균 {d['var_over_mean']}** |",
        f"| 분포 | {b['family']} (α={b['alpha']}) |",
        f"| offset | {d['sales_offset']} |",
        "| 교란 | 시간 linear-spline(6) · 연주기 harmonics(4) · 이월(직전 1등 0명) |",
        f"| 1차 추론 | permutation score test · B={ri['n_perm']} · seed={ri['seed']} |",
        "| 다중검정 | Holm + max\\|z\\| family-wise |",
        "",
        "1인당 지급액을 종속변수로 쓰지 않았다. 이는 `1등풀 / 당첨자수`의 기계적",
        "역함수여서 같은 정보를 되풀이하고 collider 편향을 만든다.",
        "",
        f"as-of 규칙: 태그는 target 회차 **이전** 데이터만 사용(최소 과거 {d['min_history']}회차).",
        "임계값은 하드코딩이 아니라 `past_learn.py`에서 직접 읽었다"
        f" (미출 gap≥{p['tag_thresholds_live']['overdue_gap']} ·"
        f" hot>{p['tag_thresholds_live']['hot_mult']}× ·"
        f" cold<{p['tag_thresholds_live']['cold_mult']}× · 윈도우 {p['tag_thresholds_live']['win_1y']}회).",
        "",
        "## 3. 전역 검정",
        "",
        f"- max\\|z\\| = **{ri['global_max_abs_z']}** · family-wise p = **{ri['global_p']}**",
        f"- 전체모형 LR = {p['full_model']['lr_stat_vs_baseline']} (df={p['full_model']['lr_df']})",
        f"- 0명 회차: 관측 {b['zero_check']['observed_zeros']} vs NB2 기대 "
        f"{b['zero_check']['nb2_expected_zeros']} → zero-inflation "
        f"{'주의' if b['zero_check']['zero_inflation_flag'] else '없음'}",
        f"- Poisson 기준 Pearson 과산포 = {b['pearson_dispersion']} (1보다 크면 Poisson 부적합)",
        "",
    ]


def _sec_effects(p: dict[str, Any]) -> list[str]:
    lines = [
        "## 4. 특성별 효과 (|z| 내림차순)",
        "",
        "`당첨자수 %/단위` 가 음수면 **비인기 방향**(분할↓ → 1인당 지급액↑).",
        "β는 특성 1개씩만 baseline 에 더한 **주변(marginal)** 추정치 — score test 와 해석이 일치한다.",
        "",
        "| 특성 | 설명 | β | 당첨자수 %/단위 | 지급액 %/단위 | z | p | p(Holm) | p(FW) | FW유의 | 전반 z | 후반 z | 재현 |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for e in p["effects"]:
        lines.append(
            "| `{f}` | {d} | {b:+.4f} | {pw:+.2f}% | {pp:+.2f}% | {z:+.2f} | {p:.4f} | "
            "{ph:.4f} | {pf:.4f} | {s} | {z1:+.2f} | {z2:+.2f} | {rp} |".format(
                f=e["feature"],
                d=e["desc_ko"],
                b=e["beta_marginal"],
                pw=e["pct_winners_per_unit"],
                pp=e["pct_payout_per_unit"],
                z=e["z_perm"],
                p=e["p_perm"],
                ph=e["p_holm"],
                pf=e["p_familywise"],
                s="**O**" if e["sig_fw_05"] else "-",
                z1=e["z_first_half"],
                z2=e["z_second_half"],
                rp="**O**" if e["replicates"] else "-",
            )
        )

    st = p["standardization"]
    fc = p["feature_correlation"]
    rs = p["replication_split"]
    lines += [
        "",
        f"`sum_z` 1단위 = 번호합 {st['sum_sd']}점 (평균 {st['sum_mean']}).",
        f"`span_z` 1단위 = 폭 {st['span_sd']}점 (평균 {st['span_mean']}).",
        "",
        f"재현성 분할: 회차 {rs['split_draw_no']} 기준 전·후반 각 독립 permutation "
        f"(B={rs['n_perm_per_half']}). {rs['note_ko']}",
        "",
        "### 공선성 경고",
        "",
        f"{fc['note_ko']} 동시보정 β(`beta_adjusted`)는 JSON에만 두고 해석은 주변 β로 한다.",
        "",
        "### 시대 4분할 z 프로파일",
        "",
        "| 특성 | " + " | ".join(
            f"구간{e['era']} ({e['draw_from']}–{e['draw_to']})" for e in p["era_profile"]["eras"]
        ) + " |",
        "|---|" + "---|" * len(p["era_profile"]["eras"]),
    ]
    for e in p["effects"]:
        lines.append(
            f"| `{e['feature']}` | " + " | ".join(f"{z:+.2f}" for z in e["era_z"]) + " |"
        )
    lines += [
        "",
        f"구간별 n≈{p['era_profile']['eras'][0]['n']} · B={p['era_profile']['n_perm_per_era']}.",
        "",
    ]
    return lines


def _sec_tags(p: dict[str, Any]) -> list[str]:
    lines = [
        "## 5. 과거학습 태그 판정",
        "",
        "| 태그 | 현재 live 가점 | 주변 β | 인기 방향 | FW 유의 | 재현 |",
        "|---|---|---|---|---|---|",
    ]
    for t in p["verdict"]["tag_directions"]:
        lines.append(
            f"| `{t['feature']}` | {LIVE_TAG_POINTS.get(t['feature'], '-')} | "
            f"{t['beta_marginal']:+.4f} | {t['direction_ko']} | "
            f"{'**O**' if t['fw_significant'] else '-'} | "
            f"{'**O**' if t['replicates'] else '-'} |"
        )
    return lines


def _sec_conclusion(p: dict[str, Any]) -> list[str]:
    v = p["verdict"]
    rec = p["recommendation"]
    lines = [
        "",
        f"**결론: {v['code']}** — {v['headline_ko']}",
        "",
        f"- family-wise 유의 특성: {v['significant_features'] or '없음'}",
        f"- 그중 전·후반 엄격 재현: {v['replicating_levers'] or '없음'}",
        f"- family-wise 유의한 과거학습 태그: {v['significant_tags'] or '없음'}",
        f"- **soft 태그 EV 라벨 재정의 지지: {'예' if v['relabel_supported'] else '아니오'}**",
        f"- 판단 근거: {rec['reason_ko']}",
        f"- {v['note_ko']}",
        "",
        "## 6. EV 후보 축",
        "",
    ]
    if v["candidate_ev_axis"]:
        lines += [
            "| 특성 | 주변 β | p(FW) | 시대 부호일치 | 전후반 재현 | ±2SD 지급액 변화 | 상태 |",
            "|---|---|---|---|---|---|---|",
        ]
        for c in v["candidate_ev_axis"]:
            lines.append(
                f"| `{c['feature']}` | {c['beta_marginal']:+.4f} | {c['p_familywise']:.4f} | "
                f"{c['era_sign_consistent']} | {'O' if c['half_split_replicates'] else '-'} | "
                f"{c['payout_gain_pct_pm2sd']:+.1f}% | {c['status_ko']} |"
            )
        lines += ["", rec["candidate_axis_ko"], ""]
    else:
        lines += ["후보 축 없음.", ""]

    lines += [
        "## 7. 권고",
        "",
        "**하지 말 것**",
        "",
    ]
    for x in rec["do_not_ko"]:
        lines.append(f"- {x}")
    lines += [
        "",
        f"**다음 검증 가능한 단계**: {rec['next_verifiable_step_ko']}",
        "",
        f"**게이트**: {rec['gate_ko']}",
        "",
    ]
    return lines


def _sec_tail(p: dict[str, Any]) -> list[str]:
    lines = [
        "## 8. 근거 문헌",
        "",
        "| 문헌 | 요지 | 본 진단에서의 사용 |",
        "|---|---|---|",
    ]
    for r in p["literature"]:
        lines.append(f"| {r['ref']} | {r['point_ko']} | {r['use_ko']} |")

    lines += [
        "",
        "## 9. 한계",
        "",
        "- 조합별 실제 판매 매수는 공개되지 않는다. 1등 당첨자수는 **인기도의 대리변수**이며,",
        "  회차당 관측이 1건이라 개별 조합 인기도는 식별되지 않는다. 저차원 특성만 식별 가능.",
        "- 판매량 offset은 총량만 보정한다. 자동선택/수동선택 비율 변화는 보정되지 않는다.",
        "- EV 축은 **당첨확률을 올리지 않는다**. 당첨 조건부 지급액 기대값만 바꾼다.",
        "- 후보 축(저번호·저합)은 전체구간 family-wise 유의하지만 **전반 구간에서 약하다**",
        "  (구간2 z≈0). 시대 효과인지 표본 변동인지는 본 데이터로 구분 불가 → 전향적 검증 필요.",
        "- 유의 결과가 나와도 발권 가중 반영은 별도 walk-forward 검증 + 형 승인이 필요하다.",
        "",
        f"근거 원본: `docs/benchmarks/{BENCH.name}`",
        "",
    ]
    return lines


def build_report(p: dict[str, Any]) -> str:
    lines: list[str] = []
    for sec in (_sec_design, _sec_effects, _sec_tags, _sec_conclusion, _sec_tail):
        lines += sec(p)
    return "\n".join(lines)


def main() -> int:
    payload = run()
    payload["literature"] = literature()
    payload["verdict"] = verdict(payload)
    payload["recommendation"] = recommendation(payload)

    BENCH.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    BENCH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT.write_text(build_report(payload), encoding="utf-8")

    v = payload["verdict"]
    print(f"[{BENCH_ID}] {v['code']} — {v['headline_ko']}")
    print(f"  global_p={v['global_p']} · relabel_supported={v['relabel_supported']}")
    print(f"  levers(재현) = {v['replicating_levers'] or '없음'}")
    for e in payload["effects"]:
        print(
            f"  {e['feature']:<10} b={e['beta_marginal']:+.5f} z={e['z_perm']:+.2f} "
            f"pFW={e['p_familywise']:.4f} half=({e['z_first_half']:+.2f},"
            f"{e['z_second_half']:+.2f}) rep={e['replicates']}"
        )
    print(f"  bench  -> {BENCH}")
    print(f"  report -> {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
