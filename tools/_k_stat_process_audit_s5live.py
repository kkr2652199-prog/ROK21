# -*- coding: utf-8 -*-
"""K-STAT-PROCESS-AUDIT-S5LIVE — S5라이브 프로세스 READ.

원장·캐시·숙제 + 라이브 expand(쓰기없음)로
S1 source · S3 쿼터 · S4 보완 · 역할 5+3+2 · n_pos 재실측.
ge3 클레임 금지. 1237아님. DB 쓰기 없음.
"""
from __future__ import annotations

import json
import random
import sqlite3
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KSTAT_PROCESS_AUDIT_S5LIVE.json"
OUT_MD = ROOT / "reports" / "20260815_KSTAT_PROCESS_AUDIT_S5LIVE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236
SEED = 42
TAG = "stat"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _open() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _parse_nums(raw: Any) -> list[int]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []
    if not isinstance(raw, list):
        return []
    return [int(x) for x in raw if str(x).lstrip("-").isdigit()]


def _npos(payload: str) -> int:
    try:
        d = json.loads(payload or "{}")
    except json.JSONDecodeError:
        return 0
    if not isinstance(d, dict):
        return 0
    return sum(1 for i in range(1, 46) if float(d.get(str(i), d.get(i, 0)) or 0) > 0)


def _role_from_set(sn: int, kind: str) -> str:
    if kind == "repack":
        return "focus_r1"
    if 1 <= sn <= 5:
        return "skill_native"
    if 6 <= sn <= 8:
        return "cover_r3"
    if 9 <= sn <= 10:
        return "shape_r2"
    return "?"


def _sn_role(sn: int) -> str:
    if 1 <= sn <= 5:
        return "skill"
    if 6 <= sn <= 8:
        return "cover"
    if 9 <= sn <= 10:
        return "shape"
    return "other"


def _jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _flags() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.role_homework import COVER_MIN_HITS
    from app.testlotto.role_slots import COVER_SELECT_MODE, SHAPE_CORE_MODE
    from app.testlotto.stat_pool_learn import STAT_POOL_LEARN_WIRE

    return {
        "ROLE_SLOTS_WIRE": bool(sp.ROLE_SLOTS_WIRE),
        "ROLE_TIER_LEARN_WIRE": bool(sp.ROLE_TIER_LEARN_WIRE),
        "ROLE_TIER_LEARN_BRAINS": sorted(sp.ROLE_TIER_LEARN_BRAINS),
        "COVER_MIN_HITS": int(COVER_MIN_HITS),
        "STAT_POOL_LEARN_WIRE": bool(STAT_POOL_LEARN_WIRE),
        "COVER_SELECT_MODE": COVER_SELECT_MODE,
        "SHAPE_CORE_MODE": SHAPE_CORE_MODE,
        "REPACK_ROLE_QUOTA_WIRE": bool(sp.REPACK_ROLE_QUOTA_WIRE),
        "REPACK_RECOMBINE_MODE": sp.REPACK_RECOMBINE_MODE,
    }


def _flags_ok(f: dict[str, Any]) -> bool:
    return bool(
        f["ROLE_SLOTS_WIRE"]
        and f["ROLE_TIER_LEARN_WIRE"]
        and f["ROLE_TIER_LEARN_BRAINS"] == ["stat"]
        and f["COVER_MIN_HITS"] == 3
        and f["STAT_POOL_LEARN_WIRE"]
        and f["COVER_SELECT_MODE"] == "outside_union"
        and f["SHAPE_CORE_MODE"] == "set1"
        and f["REPACK_ROLE_QUOTA_WIRE"]
        and f["REPACK_RECOMBINE_MODE"] == "complement"
    )


def _expand_stat(draws, dno: int) -> tuple[list[dict], list[dict]]:
    import app.testlotto.signal_pool as sp

    random.seed(SEED)
    pool = sp.expand_pool(draws, dno, seed=SEED, brains=[TAG])
    pool_br = sp._pool_by_brain(pool)
    learner = sp.RollingSignalLearner()
    num_ema, pos_ema = learner.snapshot()
    repacked = sp.repack_by_brain(
        pool_br,
        sp._build_hint(draws, dno),
        num_ema,
        pos_ema,
        target_draw_no=dno,
        hint_by_brain=sp.build_hint_by_brain(draws, dno),
    )
    return pool_br.get(TAG) or [], [x for x in repacked if str(x.get("brain_tag")) == TAG]


def main() -> int:
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of

    flags = _flags()
    hard: list[str] = []
    soft: list[str] = []
    if not _flags_ok(flags):
        hard.append(f"FLAG {flags}")

    conn = _open()

    def scalar(sql: str, args: tuple = ()) -> Any:
        row = conn.execute(sql, args).fetchone()
        return None if row is None else row[0]

    census = {
        "draws_max": scalar("SELECT MAX(draw_no) FROM lotto_draws"),
        "pred": scalar("SELECT COUNT(*) FROM lotto_predictions"),
        "pred_1237": scalar(
            "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
        ),
        "cache": scalar("SELECT COUNT(*) FROM testlotto_pool_view_cache"),
        "ledger": scalar("SELECT COUNT(*) FROM testlotto_pool_hit_ledger"),
        "ledger_stat": scalar(
            "SELECT COUNT(*) FROM testlotto_pool_hit_ledger WHERE brain_tag='stat'"
        ),
        "ledger_other": scalar(
            "SELECT COUNT(*) FROM testlotto_pool_hit_ledger WHERE brain_tag!='stat'"
        ),
        "role_hw": scalar("SELECT COUNT(*) FROM testlotto_role_homework"),
        "skill_hw": scalar("SELECT COUNT(*) FROM testlotto_skill_homework"),
        "brain_review": scalar("SELECT COUNT(*) FROM testlotto_brain_review"),
        "review_stat": scalar(
            "SELECT COUNT(*) FROM testlotto_brain_review WHERE brain_tag='stat'"
        ),
        "bt_runs": scalar("SELECT COUNT(*) FROM testlotto_backtest_runs"),
    }
    if int(census["draws_max"] or 0) != 1236:
        hard.append(f"draws_max={census['draws_max']}")
    if int(census["pred_1237"] or 0) != 0:
        hard.append("pred_1237>0")
    if int(census["ledger_stat"] or 0) != 3000:
        hard.append(f"ledger_stat={census['ledger_stat']}!=3000")
    if int(census["ledger_other"] or 0) != 0:
        hard.append(f"ledger_other={census['ledger_other']}")

    led = list(
        conn.execute(
            """
            SELECT draw_no, brain_tag, kind, set_no, nums_json, role
            FROM testlotto_pool_hit_ledger
            WHERE draw_no BETWEEN ? AND ?
            """,
            (LO, HI),
        )
    )
    draws_led = sorted({int(r["draw_no"]) for r in led})
    if len(draws_led) != 200:
        hard.append(f"ledger_draws={len(draws_led)}")
    role_c: Counter[str] = Counter()
    role_mismatch = bad_nums = pool10_bad = repack5_bad = 0
    by_dk: dict[tuple, list] = defaultdict(list)
    for r in led:
        nums = _parse_nums(r["nums_json"])
        if len(nums) != 6 or len(set(nums)) != 6 or min(nums) < 1 or max(nums) > 45:
            bad_nums += 1
        sn = int(r["set_no"] or 0)
        kind = str(r["kind"])
        expect = _role_from_set(sn, kind)
        got = str(r["role"] or "")
        role_c[got or expect] += 1
        if got and got != expect:
            role_mismatch += 1
        by_dk[(int(r["draw_no"]), str(r["kind"]))].append(sn)
    for (dno, kind), sns in by_dk.items():
        sns_s = sorted(sns)
        if kind == "pool" and sns_s != list(range(1, 11)):
            pool10_bad += 1
        if kind == "repack" and sns_s != list(range(1, 6)):
            repack5_bad += 1
    if bad_nums:
        hard.append(f"bad_nums={bad_nums}")
    if role_mismatch:
        hard.append(f"role_mismatch={role_mismatch}")
    if pool10_bad:
        hard.append(f"pool10_bad={pool10_bad}")
    if repack5_bad:
        hard.append(f"repack5_bad={repack5_bad}")
    if dict(role_c) != {
        "skill_native": 1000,
        "cover_r3": 600,
        "shape_r2": 400,
        "focus_r1": 1000,
    }:
        hard.append(f"role_counts={dict(role_c)}")

    hw_rows = list(
        conn.execute(
            """
            SELECT as_of_draw, brain_tag, role, payload_json
            FROM testlotto_role_homework
            WHERE as_of_draw BETWEEN ? AND ?
            ORDER BY as_of_draw
            """,
            (LO, HI),
        )
    )
    hw_peek = int(
        scalar("SELECT COUNT(*) FROM testlotto_role_homework WHERE as_of_draw>=1237")
        or 0
    )
    if hw_peek:
        hard.append("role_hw as_of>=1237")
    hw_asofs = sorted({int(r["as_of_draw"]) for r in hw_rows})
    if len(hw_asofs) != 200:
        hard.append(f"hw_asof_n={len(hw_asofs)}")
    hw_npos: dict[str, list[int]] = defaultdict(list)
    for r in hw_rows:
        hw_npos[f"{r['brain_tag']}|{r['role']}"].append(_npos(r["payload_json"]))
    hw_summ = {}
    for k, vs in sorted(hw_npos.items()):
        hw_summ[k] = {
            "n": len(vs),
            "npos_mean": round(mean(vs), 3) if vs else None,
            "npos_min": min(vs) if vs else None,
            "npos_max": max(vs) if vs else None,
            "npos_first10_mean": round(mean(vs[:10]), 3) if len(vs) >= 10 else None,
            "npos_last10_mean": round(mean(vs[-10:]), 3) if len(vs) >= 10 else None,
        }
    stat_cover = hw_summ.get("stat|cover_r3") or {}
    if (stat_cover.get("npos_mean") or 0) <= 0:
        hard.append("stat_cover n_pos mean 0")

    cache_rows = list(
        conn.execute(
            """
            SELECT draw_no, brain, pool_json, repack_json
            FROM testlotto_pool_view_cache
            WHERE draw_no BETWEEN ? AND ?
            """,
            (LO, HI),
        )
    )
    cache_by: dict[int, dict[str, Any]] = {}
    cache_pool_src: Counter[str] = Counter()
    cache_rep_src: Counter[str] = Counter()
    cache_stat_ok = 0
    empty_other = 0
    quota_fail = 0
    copy4_fail = 0
    jac_vals: list[float] = []
    jac_nonzero = 0
    s3_role: Counter[str] = Counter()
    for r in cache_rows:
        tag = str(r["brain"])
        dno = int(r["draw_no"])
        pool = json.loads(r["pool_json"] or "[]")
        rep = json.loads(r["repack_json"] or "[]")
        if tag != TAG:
            if len(pool) == 0 and len(rep) == 0:
                empty_other += 1
            continue
        if len(pool) != 10 or len(rep) != 5:
            hard.append(f"cache_size d={dno} p{len(pool)} r{len(rep)}")
            continue
        cache_stat_ok += 1
        cache_by[dno] = {"pool": pool, "repack": rep}
        for s in pool:
            cache_pool_src[str(s.get("source") or "")] += 1
        copied: list[dict] = []
        rec: list[dict] = []
        for s in rep:
            src = str(s.get("source") or "")
            cache_rep_src[src] += 1
            if src == "pool":
                copied.append(s)
            else:
                rec.append(s)
        if len(copied) != 4 or len(rec) != 1:
            copy4_fail += 1
        roles = [_sn_role(int(s.get("source_set_no") or 0)) for s in copied]
        for rr in roles:
            s3_role[rr] += 1
        if roles.count("skill") < 1 or roles.count("cover") < 1 or roles.count("shape") > 1:
            quota_fail += 1
        cu = set()
        for s in copied:
            cu.update(_parse_nums(s.get("nums")))
        ru: set[int] = set()
        for s in rec:
            ru.update(_parse_nums(s.get("nums")))
        j = _jaccard(ru, cu)
        jac_vals.append(j)
        if j > 0:
            jac_nonzero += 1
    if cache_stat_ok != 200:
        hard.append(f"cache_stat_ok={cache_stat_ok}")
    if copy4_fail:
        hard.append(f"copy4_fail={copy4_fail}")
    if quota_fail:
        hard.append(f"quota_fail={quota_fail}")
    if jac_nonzero:
        hard.append(f"complement_jaccard_nonzero={jac_nonzero}")
    if empty_other != 400:
        soft.append(f"empty_other_cache={empty_other} (기대400)")
    if dict(cache_pool_src) != {"": 2000}:
        soft.append(f"cache_pool_source_dropped={dict(cache_pool_src)}")
    if census["bt_runs"] == 0:
        soft.append("UI backtest_runs=0 (원장≠강제백테표)")

    conn.close()

    print("== LIVE expand 200 (no write) ==", flush=True)
    t0 = time.perf_counter()
    peek = 0
    live_cover_src: Counter[str] = Counter()
    live_shape_src: Counter[str] = Counter()
    live_rep_src: Counter[str] = Counter()
    live_role_bad = 0
    cache_mismatch = 0
    n_ok = 0
    for i, dno in enumerate(range(LO, HI + 1)):
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        max_mat = max((int(d["draw_no"]) for d in draws), default=0)
        if max_mat >= dno:
            peek += 1
            hard.append(f"PEEK {dno}")
            continue
        pool, rep = _expand_stat(draws, dno)
        skill = [s for s in pool if str(s.get("role")) == "skill_native"]
        cover = [s for s in pool if str(s.get("role")) == "cover_r3"]
        shape = [s for s in pool if str(s.get("role")) == "shape_r2"]
        if len(skill) != 5 or len(cover) != 3 or len(shape) != 2 or len(rep) != 5:
            live_role_bad += 1
        for s in cover:
            live_cover_src[str(s.get("source") or "")] += 1
        for s in shape:
            live_shape_src[str(s.get("source") or "")] += 1
        for s in rep:
            live_rep_src[str(s.get("source") or "")] += 1
        cached = cache_by.get(dno)
        if cached:
            cpool = [tuple(sorted(int(x) for x in (s.get("nums") or []))) for s in cached["pool"]]
            lpool = [tuple(sorted(int(x) for x in (s.get("nums") or []))) for s in pool]
            crep = [tuple(sorted(int(x) for x in (s.get("nums") or []))) for s in cached["repack"]]
            lrep = [tuple(sorted(int(x) for x in (s.get("nums") or []))) for s in rep]
            if cpool != lpool or crep != lrep:
                cache_mismatch += 1
        n_ok += 1
        if (i + 1) % 40 == 0 or dno == HI:
            print(f"  live {i+1}/200 d={dno} peek={peek} mismatch={cache_mismatch}", flush=True)

    if peek:
        hard.append(f"peek={peek}")
    if live_role_bad:
        hard.append(f"live_role_bad={live_role_bad}")
    if cache_mismatch:
        hard.append(f"cache_live_mismatch={cache_mismatch}")
    if n_ok != 200:
        hard.append(f"live_n_ok={n_ok}")
    cover_ok = live_cover_src.get("cover_r3_outside_union", 0)
    if cover_ok + live_cover_src.get("cover_fill_morph", 0) != 600:
        hard.append(f"live_cover_src={dict(live_cover_src)}")
    if cover_ok < 500:
        hard.append(f"outside_union_too_few={cover_ok}")

    s1 = {
        "live_cover_source": dict(live_cover_src),
        "live_shape_source": dict(live_shape_src),
        "cache_pool_source": dict(cache_pool_src),
        "note": "캐시는 pool source 미저장. 라이브 expand가 S1 라벨 SSOT.",
    }
    s3 = {
        "copy4_fail": copy4_fail,
        "quota_fail": quota_fail,
        "copied_role_counts": dict(s3_role),
        "expect": "skill>=1 cover>=1 shape<=1 per draw ×4 copies",
    }
    s4 = {
        "cache_repack_source": dict(cache_rep_src),
        "live_repack_source": dict(live_rep_src),
        "complement_jaccard_mean": round(mean(jac_vals), 6) if jac_vals else None,
        "complement_jaccard_nonzero": jac_nonzero,
        "label_note": "보완1장 source=score_repack (complement 문자열 아님·SOFT). 번호 Jaccard=0이 S4 증거.",
    }
    if "score_repack" not in dict(cache_rep_src) and "score_repack" not in dict(live_rep_src):
        soft.append("repack 5번째 source 라벨 없음")

    hard_ok = len(hard) == 0
    out = {
        "id": "K-STAT-PROCESS-AUDIT-S5LIVE",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "read_only": True,
        "db_write": False,
        "flags": flags,
        "census": census,
        "ledger": {
            "n_draws": len(draws_led),
            "role_counts": dict(role_c),
            "bad_nums": bad_nums,
            "role_mismatch": role_mismatch,
            "pool10_bad": pool10_bad,
            "repack5_bad": repack5_bad,
        },
        "homework": {
            "asof_n": len(hw_asofs),
            "asof_min": min(hw_asofs) if hw_asofs else None,
            "asof_max": max(hw_asofs) if hw_asofs else None,
            "npos": hw_summ,
            "peek_ge_1237": hw_peek,
        },
        "s1_cover_source": s1,
        "s3_quota": s3,
        "s4_complement": s4,
        "live": {
            "n_ok": n_ok,
            "peek": peek,
            "role_bad": live_role_bad,
            "cache_mismatch": cache_mismatch,
            "elapsed_s": round(time.perf_counter() - t0, 1),
        },
        "hard": hard,
        "soft": soft,
        "hard_ok": hard_ok,
        "verdict": "PASS" if hard_ok else "FAIL",
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _md(out)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({
        "verdict": out["verdict"],
        "hard": hard,
        "soft": soft,
        "s1": s1["live_cover_source"],
        "s3_quota_fail": quota_fail,
        "s4_j": s4["complement_jaccard_mean"],
        "npos_stat_cover": hw_summ.get("stat|cover_r3"),
        "live": out["live"],
        "census": {k: census[k] for k in ("ledger_stat", "review_stat", "pred_1237", "draws_max")},
    }, ensure_ascii=False, indent=2))
    return 0 if hard_ok else 1


def _md(o: dict[str, Any]) -> str:
    hw = (o.get("homework") or {}).get("npos") or {}
    led = o.get("ledger") or {}
    s1 = o.get("s1_cover_source") or {}
    s3 = o.get("s3_quota") or {}
    s4 = o.get("s4_complement") or {}
    live = o.get("live") or {}
    lines = [
        "# K-STAT-PROCESS-AUDIT-S5LIVE — S5라이브 프로세스 감사",
        "",
        f"시각: {o['as_of']} · **{o.get('verdict')}** · READ-ONLY · ge3미클레임 · 1237아님",
        "창 1037~1236 · 뇌=stat만 · S1 outside_union · S2 HOLD set1 · S3 쿼터 · S4 보완",
        "",
        "## 0) 한 줄",
        "",
        "원장맞춤 직후 DB와 라이브 expand(쓰기없음)를 대조했다. "
        f"HARD={'통과' if o.get('hard_ok') else '실패'}. "
        "역할 5+3+2 · S1/S3/S4 라벨·번호 규칙 · 숙제 n_pos를 다시 셌다. 등수 클레임 없음.",
        "",
        "## 1) 플래그·센서스",
        "",
        f"`{json.dumps(o.get('flags') or {}, ensure_ascii=False)}`",
        "",
        f"`{json.dumps(o.get('census') or {}, ensure_ascii=False)}`",
        "",
        "## 2) 원장 역할 5+3+2",
        "",
        f"- 회차 **{led.get('n_draws')}**/200 · 번호무효 **{led.get('bad_nums')}** · 역할불일치 **{led.get('role_mismatch')}**",
        f"- pool10결손 **{led.get('pool10_bad')}** · repack5결손 **{led.get('repack5_bad')}**",
        f"- 역할 `{json.dumps(led.get('role_counts') or {}, ensure_ascii=False)}`",
        "",
        "## 3) S1 cover source (라이브)",
        "",
        f"- 라이브 `{json.dumps(s1.get('live_cover_source') or {}, ensure_ascii=False)}`",
        f"- shape `{json.dumps(s1.get('live_shape_source') or {}, ensure_ascii=False)}`",
        f"- 캐시 pool source `{json.dumps(s1.get('cache_pool_source') or {}, ensure_ascii=False)}`",
        f"- {s1.get('note')}",
        "",
        "## 4) S3 몰아주기 쿼터 (캐시 복사4)",
        "",
        f"- copy4 실패 **{s3.get('copy4_fail')}** · 쿼터실패 **{s3.get('quota_fail')}**",
        f"- 복사 역할합 `{json.dumps(s3.get('copied_role_counts') or {}, ensure_ascii=False)}`",
        f"- 기대: {s3.get('expect')}",
        "",
        "## 5) S4 보완조합 (캐시 5번째)",
        "",
        f"- 캐시 repack source `{json.dumps(s4.get('cache_repack_source') or {}, ensure_ascii=False)}`",
        f"- 라이브 `{json.dumps(s4.get('live_repack_source') or {}, ensure_ascii=False)}`",
        f"- 재조합 vs 복사4 Jaccard mean **{s4.get('complement_jaccard_mean')}** · 0아닌회 **{s4.get('complement_jaccard_nonzero')}**",
        f"- {s4.get('label_note')}",
        "",
        "## 6) 숙제 n_pos",
        "",
        "| 키 | n | mean | min | max | 초반10 | 후반10 |",
        "|----|---|------|-----|-----|--------|--------|",
    ]
    for k, v in hw.items():
        lines.append(
            f"| {k} | {v.get('n')} | {v.get('npos_mean')} | {v.get('npos_min')} | "
            f"{v.get('npos_max')} | {v.get('npos_first10_mean')} | {v.get('npos_last10_mean')} |"
        )
    lines += [
        "",
        f"- as_of n={(o.get('homework') or {}).get('asof_n')} "
        f"min={(o.get('homework') or {}).get('asof_min')} "
        f"max={(o.get('homework') or {}).get('asof_max')} "
        f"peek≥1237={(o.get('homework') or {}).get('peek_ge_1237')}",
        "",
        "## 7) 라이브↔캐시",
        "",
        f"- n_ok **{live.get('n_ok')}** · peek **{live.get('peek')}** · "
        f"역할불량 **{live.get('role_bad')}** · 번호불일치 **{live.get('cache_mismatch')}** · "
        f"{live.get('elapsed_s')}s",
        "",
        "## 8) HARD / SOFT",
        "",
        f"- HARD ({len(o.get('hard') or [])}): `{json.dumps(o.get('hard') or [], ensure_ascii=False)}`",
        f"- SOFT: `{json.dumps(o.get('soft') or [], ensure_ascii=False)}`",
        "",
        "## 9) 금지",
        "",
        "- ge3/등수/mean 성적클레임 금지. 코드 APPLY 없음. DB 쓰기 없음. 1237아님.",
        "",
        "## 10) 다음",
        "",
        "리스트 #3 K-A-STALE-DOC (FINDINGS K-A 구표본 표시). 1237아님.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
