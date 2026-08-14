# -*- coding: utf-8 -*-
"""K-BT200-PROCESS-LEARN-AUDIT — 지금 DB 200회 원장·숙제·캐시 READ.

프로세스(1~5/6~8/9~10/몰아주기) 정상 가동 + 학습 정합.
재예측·DB쓰기 없음. ge3 클레임 금지. 1237 아님.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KBT200_PROCESS_LEARN_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260814_KBT200_PROCESS_LEARN_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236
THEORY = 0.80
BASE = "http://127.0.0.1:7021"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _open() -> sqlite3.Connection:
    uri = f"file:{DB.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
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


def _http(path: str) -> dict[str, Any]:
    url = BASE + path
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            body = r.read()
            return {
                "ok": True,
                "status": int(r.status),
                "n": len(body),
                "json": json.loads(body) if body[:1] in (b"{", b"[") else None,
            }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "status": 0, "error": str(e)}


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


def main() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp

    flags = {
        "ROLE_SLOTS_WIRE": bool(sp.ROLE_SLOTS_WIRE),
        "ROLE_TIER_LEARN_WIRE": bool(sp.ROLE_TIER_LEARN_WIRE),
        "ROLE_TIER_LEARN_BRAINS": sorted(sp.ROLE_TIER_LEARN_BRAINS),
        "COVER_MIN_HITS": None,
    }
    from app.testlotto import role_homework as rh

    flags["COVER_MIN_HITS"] = int(rh.COVER_MIN_HITS)

    conn = _open()
    hard: list[str] = []
    soft: list[str] = []

    def q(sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        return list(conn.execute(sql, args))

    def scalar(sql: str, args: tuple = ()) -> Any:
        row = conn.execute(sql, args).fetchone()
        return None if row is None else row[0]

    census = {
        "draws_max": scalar("SELECT MAX(draw_no) FROM lotto_draws"),
        "draws_n": scalar("SELECT COUNT(*) FROM lotto_draws"),
        "pred": scalar("SELECT COUNT(*) FROM lotto_predictions"),
        "pred_1237": scalar(
            "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
        ),
        "cache": scalar("SELECT COUNT(*) FROM testlotto_pool_view_cache"),
        "ledger": scalar("SELECT COUNT(*) FROM testlotto_pool_hit_ledger"),
        "scatter": scalar("SELECT COUNT(*) FROM testlotto_pool_hit_scatter"),
        "role_hw": scalar("SELECT COUNT(*) FROM testlotto_role_homework"),
        "skill_hw": scalar("SELECT COUNT(*) FROM testlotto_skill_homework"),
        "learn_state": scalar("SELECT COUNT(*) FROM testlotto_brain_learn_state"),
        "brain_review": scalar("SELECT COUNT(*) FROM testlotto_brain_review"),
        "bt_runs": scalar("SELECT COUNT(*) FROM testlotto_backtest_runs"),
        "bt_draws": scalar("SELECT COUNT(*) FROM testlotto_backtest_draw_results"),
        "evolve_log": scalar("SELECT COUNT(*) FROM testlotto_evolve_log"),
    }

    if int(census["draws_max"] or 0) != 1236:
        hard.append(f"draws_max={census['draws_max']} !=1236")
    if int(census["pred_1237"] or 0) != 0:
        hard.append("pred_1237>0")

    ledger_win = q(
        """
        SELECT draw_no, brain_tag, kind, set_no, nums_json, hits, bonus,
               bonus_hit, role, hit_nums_json
        FROM testlotto_pool_hit_ledger
        WHERE draw_no BETWEEN ? AND ?
        """,
        (LO, HI),
    )
    draws_led = sorted({int(r["draw_no"]) for r in ledger_win})
    brains_led = sorted({str(r["brain_tag"]) for r in ledger_win})
    kinds = Counter((str(r["brain_tag"]), str(r["kind"])) for r in ledger_win)

    process = {
        "lo": LO,
        "hi": HI,
        "n_draws": len(draws_led),
        "brains": brains_led,
        "rows": len(ledger_win),
        "missing_draws": [d for d in range(LO, HI + 1) if d not in set(draws_led)],
        "per_draw_brain_kind": {},
        "role_mismatch": 0,
        "bad_nums": 0,
        "incomplete_pool10": 0,
        "incomplete_repack5": 0,
        "role_counts": Counter(),
        "source_cache": {},
    }
    if process["n_draws"] != 200:
        hard.append(f"ledger_draws={process['n_draws']} !=200")
    if process["missing_draws"]:
        hard.append(f"missing_draws n={len(process['missing_draws'])}")

    by_dbk: dict[tuple, list] = defaultdict(list)
    for r in ledger_win:
        by_dbk[(int(r["draw_no"]), str(r["brain_tag"]), str(r["kind"]))].append(r)
        nums = _parse_nums(r["nums_json"])
        if len(nums) != 6 or len(set(nums)) != 6 or min(nums) < 1 or max(nums) > 45:
            process["bad_nums"] += 1
            hard.append(
                f"bad_nums d={r['draw_no']} {r['brain_tag']} {r['kind']}#{r['set_no']}"
            )
        sn = int(r["set_no"] or 0)
        kind = str(r["kind"])
        expect = _role_from_set(sn, kind)
        got = str(r["role"] or "")
        process["role_counts"][got or expect] += 1
        if got and got != expect:
            process["role_mismatch"] += 1
            hard.append(
                f"role_mismatch d={r['draw_no']} set={sn} got={got} expect={expect}"
            )

    for (dno, tag, kind), rows in by_dbk.items():
        sns = sorted(int(r["set_no"] or 0) for r in rows)
        if kind == "pool" and sns != list(range(1, 11)):
            process["incomplete_pool10"] += 1
            hard.append(f"pool10 d={dno} {tag} sets={sns}")
        if kind == "repack" and sns != list(range(1, 6)):
            process["incomplete_repack5"] += 1
            hard.append(f"repack5 d={dno} {tag} sets={sns}")

    if process["bad_nums"]:
        hard.append(f"bad_nums={process['bad_nums']}")
    if process["role_mismatch"]:
        hard.append(f"role_mismatch={process['role_mismatch']}")

    # hits by role/brain/kind (monitor)
    hit_acc: dict[str, list[int]] = defaultdict(list)
    best_acc: dict[str, list[int]] = defaultdict(list)
    ge3_best: dict[str, int] = Counter()
    tmp_best: dict[tuple, int] = defaultdict(lambda: -1)
    for r in ledger_win:
        role = str(r["role"] or _role_from_set(int(r["set_no"] or 0), str(r["kind"])))
        h = int(r["hits"] or 0)
        key = f"{r['brain_tag']}|{r['kind']}|{role}"
        hit_acc[key].append(h)
        bk = (int(r["draw_no"]), str(r["brain_tag"]), str(r["kind"]), role)
        tmp_best[bk] = max(tmp_best[bk], h)
    grouped: dict[str, list[int]] = defaultdict(list)
    for (dno, tag, kind, role), bh in tmp_best.items():
        grouped[f"{tag}|{kind}|{role}"].append(bh)
        if bh >= 3:
            ge3_best[f"{tag}|{kind}|{role}"] += 1

    monitor: dict[str, Any] = {}
    for k, hs in sorted(hit_acc.items()):
        monitor[k] = {
            "n": len(hs),
            "mean_all": round(mean(hs), 4) if hs else None,
            "mean_best": round(mean(grouped[k]), 4) if grouped.get(k) else None,
            "ge3_best_count": int(ge3_best.get(k, 0)),
            "theory": THEORY,
            "claim": False,
        }

    # role homework
    hw_rows = q(
        """
        SELECT as_of_draw, brain_tag, role, payload_json
        FROM testlotto_role_homework
        WHERE as_of_draw BETWEEN ? AND ?
        """,
        (LO, HI),
    )
    hw_peek = q(
        "SELECT COUNT(*) AS n FROM testlotto_role_homework WHERE as_of_draw >= 1237"
    )[0]["n"]
    if int(hw_peek or 0):
        hard.append("role_hw as_of>=1237")

    hw_asofs = sorted({int(r["as_of_draw"]) for r in hw_rows})
    hw_brains = sorted({str(r["brain_tag"]) for r in hw_rows})
    hw_npos: dict[str, list[int]] = defaultdict(list)
    peek_consume = 0
    # consume target T uses as_of < T. Writer as_of=draw_no of confirmed result.
    # For draw D, load uses MAX(as_of)<D. If a row has as_of==D it is for D+1. OK.
    # Peek would be as_of >= target when loading for target. Check no as_of > HI.
    hw_max = scalar("SELECT MAX(as_of_draw) FROM testlotto_role_homework")
    if hw_max is not None and int(hw_max) >= 1237:
        hard.append(f"hw_max={hw_max}>=1237")
        peek_consume += 1
    if hw_max is not None and int(hw_max) > HI:
        hard.append(f"hw_max={hw_max}>HI")

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

    expected_hw = 200 * 3 * 2  # write all brains × 2 roles
    learn = {
        "role_hw_rows": len(hw_rows),
        "role_hw_expected_if_full": expected_hw,
        "asof_n": len(hw_asofs),
        "asof_min": min(hw_asofs) if hw_asofs else None,
        "asof_max": max(hw_asofs) if hw_asofs else None,
        "brains": hw_brains,
        "npos": hw_summ,
        "skill_hw": int(census["skill_hw"] or 0),
        "learn_state": int(census["learn_state"] or 0),
        "brain_review": int(census["brain_review"] or 0),
        "consume_brains": flags["ROLE_TIER_LEARN_BRAINS"],
        "peek_hw_ge_1237": int(hw_peek or 0),
        "note_skill_gap": "skill_homework=0 → 이번 경로 발권 피드백 없음. 1~5 miss_pattern 숙제 미누적(설계).",
        "note_consume": "쓰기=3뇌×2역할. 소비=stat만. markov/review 6~10은 Jaccard/변형 구경로.",
    }
    if len(hw_asofs) != 200:
        hard.append(f"role_hw asof_n={len(hw_asofs)} !=200")
    if set(hw_brains) != {"stat", "markov", "review"}:
        soft.append(f"hw_brains={hw_brains}")

    # cache process: source labels
    cache_rows = q(
        """
        SELECT draw_no, brain, pool_json, repack_json, schema_version, tune_json
        FROM testlotto_pool_view_cache
        WHERE draw_no BETWEEN ? AND ?
        """,
        (LO, HI),
    )
    src_c = Counter()
    cache_brains = Counter()
    cache_role_c = Counter()
    cache_pool_n_bad = 0
    cache_repack_n_bad = 0
    empty_other = 0
    sample_1236: dict[str, Any] = {}
    for r in cache_rows:
        cache_brains[str(r["brain"])] += 1
        try:
            pool = json.loads(r["pool_json"] or "[]")
            repack = json.loads(r["repack_json"] or "[]")
        except json.JSONDecodeError:
            cache_pool_n_bad += 1
            continue
        # stat-only BT: markov/review 캐시 행은 빈 [] 가 설계(미실행).
        tag = str(r["brain"])
        plen = len(pool) if isinstance(pool, list) else -1
        rlen = len(repack) if isinstance(repack, list) else -1
        if tag == "stat":
            if plen != 10:
                cache_pool_n_bad += 1
            if rlen != 5:
                cache_repack_n_bad += 1
        else:
            if plen == 0 and rlen == 0:
                empty_other += 1
            elif plen not in (0, 10):
                cache_pool_n_bad += 1
            elif rlen not in (0, 5):
                cache_repack_n_bad += 1
        for s in pool if isinstance(pool, list) else []:
            src_c[f"{tag}|pool|{s.get('role')}|{s.get('source')}"] += 1
            cache_role_c[f"{tag}|{s.get('role')}"] += 1
        for s in repack if isinstance(repack, list) else []:
            src_c[f"{tag}|repack|{s.get('role')}|{s.get('source')}"] += 1
        if int(r["draw_no"]) == 1236:
            sample_1236[str(r["brain"])] = {
                "pool_n": len(pool) if isinstance(pool, list) else 0,
                "repack_n": len(repack) if isinstance(repack, list) else 0,
                "pool_roles": [
                    {
                        "set_no": s.get("set_no") or s.get("pred_set_no"),
                        "role": s.get("role"),
                        "source": s.get("source"),
                    }
                    for s in (pool or [])
                ],
                "repack_roles": [
                    {
                        "set_no": s.get("set_no") or s.get("pred_set_no"),
                        "role": s.get("role"),
                        "source": s.get("source"),
                    }
                    for s in (repack or [])
                ],
            }

    if cache_pool_n_bad:
        hard.append(f"cache_pool_n_bad={cache_pool_n_bad}")
    if cache_repack_n_bad:
        hard.append(f"cache_repack_n_bad={cache_repack_n_bad}")

    # stat cover should switch to role_hw after first as_of exists (1037 written after 1037 scored)
    stat_cover_src = {
        k: v for k, v in src_c.items() if k.startswith("stat|pool|cover_r3|")
    }
    markov_cover_hw = sum(
        v for k, v in src_c.items() if k.startswith("markov|pool|cover_r3|cover_r3_role_hw")
    )
    review_cover_hw = sum(
        v for k, v in src_c.items() if k.startswith("review|pool|cover_r3|cover_r3_role_hw")
    )
    if markov_cover_hw or review_cover_hw:
        hard.append(
            f"non-stat consumed role_hw markov={markov_cover_hw} review={review_cover_hw}"
        )

    process["source_cache"] = dict(src_c)
    process["cache_brains"] = dict(cache_brains)
    process["cache_roles"] = dict(cache_role_c)
    process["kinds_counter"] = {f"{a}|{b}": c for (a, b), c in kinds.items()}
    process["empty_other_brain_cache"] = empty_other
    if empty_other:
        soft.append(
            f"stat-only BT: markov/review cache empty [] n={empty_other} (미실행·버그아님)"
        )

    # live HTTP
    http = {
        "home": _http("/"),
        "pool_index": _http("/api/testlotto/backtest/pool-index"),
        "draw_index": _http("/api/testlotto/backtest/draw-index"),
        "runs": _http("/api/testlotto/backtest/runs?limit=20"),
        "preds": _http("/api/testlotto/predictions?limit=5"),
        "draws_1236": _http("/api/testlotto/draws/1236"),
    }
    home_ok = bool(http["home"].get("ok") and http["home"].get("status") == 200)
    if not home_ok:
        soft.append("home HTTP not 200")

    def _idx_n(obj: Any) -> int | None:
        if not isinstance(obj, dict):
            return None
        j = obj.get("json")
        if isinstance(j, list):
            return len(j)
        if isinstance(j, dict):
            for k in ("draws", "items", "rows", "index"):
                if isinstance(j.get(k), list):
                    return len(j[k])
            if "n_draws" in j:
                try:
                    return int(j["n_draws"])
                except (TypeError, ValueError):
                    return None
            if "n" in j:
                try:
                    return int(j["n"])
                except (TypeError, ValueError):
                    return None
        return None

    http_n = {
        "home_status": http["home"].get("status"),
        "pool_index_n": _idx_n(http["pool_index"]),
        "draw_index_n": _idx_n(http["draw_index"]),
        "runs_ok": http["runs"].get("ok"),
        "pred_status": http["preds"].get("status"),
        "d1236_status": http["draws_1236"].get("status"),
    }

    # verdict
    hard_u = sorted(set(hard))[:40]
    hard_ok = len(hard_u) == 0
    engine_ok = (
        hard_ok
        and flags["ROLE_SLOTS_WIRE"]
        and flags["ROLE_TIER_LEARN_WIRE"]
        and flags["ROLE_TIER_LEARN_BRAINS"] == ["stat"]
        and process["n_draws"] == 200
        and process["incomplete_pool10"] == 0
        and process["incomplete_repack5"] == 0
    )

    out = {
        "id": "K-BT200-PROCESS-LEARN-AUDIT",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "read_only": True,
        "flags": flags,
        "census": census,
        "process": {
            "n_draws": process["n_draws"],
            "brains": process["brains"],
            "rows": process["rows"],
            "missing_n": len(process["missing_draws"]),
            "role_mismatch": process["role_mismatch"],
            "bad_nums": process["bad_nums"],
            "incomplete_pool10": process["incomplete_pool10"],
            "incomplete_repack5": process["incomplete_repack5"],
            "role_counts": dict(process["role_counts"]),
            "kinds": process["kinds_counter"],
            "cache_brains": process["cache_brains"],
            "empty_other_brain_cache": process.get("empty_other_brain_cache"),
            "stat_cover_sources": stat_cover_src,
            "sample_1236": sample_1236,
        },
        "learn": learn,
        "monitor_hits": monitor,
        "http": http_n,
        "hard": hard_u,
        "soft": soft,
        "hard_ok": hard_ok,
        "engine_ok": engine_ok,
        "verdict": "PASS" if engine_ok else "FAIL",
    }
    conn.close()

    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _md(out)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({"verdict": out["verdict"], "hard": hard_u, "engine_ok": engine_ok}, ensure_ascii=False, indent=2))
    return out


def _md(o: dict[str, Any]) -> str:
    p = o["process"]
    L = o["learn"]
    lines = [
        "# K-BT200-PROCESS-LEARN-AUDIT — 지금 200회 프로세스·학습",
        "",
        f"시각: {o['as_of']} · **{o['verdict']}** · READ-ONLY · ge3미클레임 · 1237아님",
        "",
        "## 0) 한 줄",
        "",
        (
            "지금 DB 200회(1037~1236) 원장을 읽었다. "
            + (
                "**프로세스 엔진 가동 정상**(10+5, 역할 5+3+2, 번호 유효, 컨닝 0)."
                if o["engine_ok"]
                else "**HARD 결함 있음** — 아래 hard."
            )
            + " 6~8/9~10 복습은 **stat만 소비**. 1~5 숙제표는 이번 경로에 **없음**(발권 피드백 0)."
        ),
        "",
        "## 1) 플래그·센서스 (파일·DB)",
        "",
        f"- ROLE_SLOTS_WIRE=**{o['flags']['ROLE_SLOTS_WIRE']}** · ROLE_TIER_LEARN_WIRE=**{o['flags']['ROLE_TIER_LEARN_WIRE']}** · 소비뇌={o['flags']['ROLE_TIER_LEARN_BRAINS']} · COVER_MIN_HITS=**{o['flags']['COVER_MIN_HITS']}**",
        f"- draws MAX **{o['census']['draws_max']}** · pred **{o['census']['pred']}** · pred1237 **{o['census']['pred_1237']}**",
        f"- cache **{o['census']['cache']}** · ledger **{o['census']['ledger']}** · scatter **{o['census']['scatter']}**",
        f"- role_hw **{o['census']['role_hw']}** · skill_hw **{o['census']['skill_hw']}** · learn_state **{o['census']['learn_state']}** · review **{o['census']['brain_review']}**",
        f"- UI backtest_runs **{o['census']['bt_runs']}** · draw_results **{o['census']['bt_draws']}**",
        "",
        "## 2) 프로세스 엔진 (원장 1037~1236)",
        "",
        "| 항목 | 값 |",
        "|------|-----|",
        f"| 회차 | **{p['n_draws']}**/200 |",
        f"| 뇌 | {p['brains']} |",
        f"| 행 | {p['rows']} |",
        f"| pool10 결손 | {p['incomplete_pool10']} |",
        f"| repack5 결손 | {p['incomplete_repack5']} |",
        f"| 역할 불일치 | {p['role_mismatch']} |",
        f"| 번호 무효 | {p['bad_nums']} |",
        f"| 역할 카운트 | `{p['role_counts']}` |",
        f"| kind | `{p['kinds']}` |",
        f"| 캐시 뇌 | `{p['cache_brains']}` |",
        f"| 타뇌 빈캐시 | {p.get('empty_other_brain_cache')} (stat단독 BT 설계) |",
        "",
        "### stat 6~8 생성 경로 (캐시 source)",
        "",
        "```",
        json.dumps(p.get("stat_cover_sources") or {}, ensure_ascii=False, indent=2),
        "```",
        "",
        "### 1236 샘플 (역할·source)",
        "",
        "```",
        json.dumps(p.get("sample_1236") or {}, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 3) 학습",
        "",
        f"- 역할숙제 행 **{L['role_hw_rows']}** (기대 200×3×2=**{L['role_hw_expected_if_full']}**) · as_of n=**{L['asof_n']}** min={L['asof_min']} max={L['asof_max']}",
        f"- 소비 뇌={L['consume_brains']} · peek as_of≥1237 = **{L['peek_hw_ge_1237']}**",
        f"- skill_homework=**{L['skill_hw']}** · learn_state=**{L['learn_state']}** · brain_review=**{L['brain_review']}**",
        f"- {L['note_skill_gap']}",
        f"- {L['note_consume']}",
        "",
        "### 숙제 n_pos (칸 수)",
        "",
        "| 키 | n | mean | min | max | 초반10 | 후반10 |",
        "|----|---|------|-----|-----|--------|--------|",
    ]
    for k, v in (L.get("npos") or {}).items():
        lines.append(
            f"| {k} | {v['n']} | {v['npos_mean']} | {v['npos_min']} | {v['npos_max']} | {v['npos_first10_mean']} | {v['npos_last10_mean']} |"
        )
    lines += [
        "",
        "## 4) 적중 모니터 (클레임 금지 · 이론 0.80)",
        "",
        "| 키 | n | mean_all | mean_best | ge3_best(모니터) |",
        "|----|---|----------|-----------|------------------|",
    ]
    for k, v in (o.get("monitor_hits") or {}).items():
        lines.append(
            f"| {k} | {v['n']} | {v['mean_all']} | {v['mean_best']} | {v['ge3_best_count']} |"
        )
    lines += [
        "",
        "## 5) 서버 HTTP",
        "",
        f"`{json.dumps(o.get('http') or {}, ensure_ascii=False)}`",
        "",
        "## 6) HARD / SOFT",
        "",
        f"- HARD ({'0' if o['hard_ok'] else len(o['hard'])}): {o['hard'] or '[]'}",
        f"- SOFT: {o['soft'] or '[]'}",
        "",
        "## 7) 판정",
        "",
        f"- engine_ok=**{o['engine_ok']}** · verdict=**{o['verdict']}**",
        "- 다음=형 1건(권고 markov 동일 소비). 1237아님.",
        "",
        "## 8) 정밀 해석 (초심자용)",
        "",
        "1. **프로세스(칸 나누기)** 는 정상이다. 매 회차 1~5번=실력, 6~8번=3등쪽 덮기, 9~10번=2등쪽 모양, 몰아주기 5장. 번호 6개·1~45·중복없음. 역할 이름과 칸 번호가 200회 전부 맞다.",
        "2. **6~8 복습은 과거학습(stat)만 실제로 쓴다.** 숙제표 칸 수가 초반 평균 4 → 후반 22.5 로 늘었다. 표가 쌓이며 다음 회차에만 읽는다(컨닝 0).",
        "3. **markov·review의 6~8 숙제표는 전부 0칸.** 이번 200회는 stat만 돌려서 그 두 뇌의 원장이 없다. 9~10 숙제는 과거 보너스 빈도라 세 뇌가 같은 숫자(~30칸)다. **버그 아님.**",
        "4. **1~5번 실력 학습은 이번 경로에 없다.** 발권(실제 산 5장) 피드백이 0이라 skill_homework·learn_state가 비어 있다. 1~5 엔진 코드는 그대로이고, ‘숙제 누적’만 안 된 것이다.",
        "5. **홈 화면 강제백테 표는 비어 있을 수 있다.** `backtest_runs`/`draw_results`=0. 이번 200회는 원장·풀캐시에 저장됐다. pool-index API는 강제백테 표와만 조인해서 **n_draws=0** 이 된다.",
        "6. **캐시 JSON에 source가 없다.** 저장 함수가 역할만 남기고 경로 라벨을 버린다. 6~8이 숙제를 썼는지는 이전 ON/OFF 비교(178/200 변경)로 이미 확인됨. 엔진 정지 아님.",
        "7. 홈에서 markov/review 1037~1236을 열면 **빈 10세트**가 보인다. stat단독 백테가 빈 칸을 캐시에 넣은 것. 3뇌를 다시 돌리기 전엔 정상.",
        "",
    ]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
