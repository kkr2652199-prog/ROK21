# -*- coding: utf-8 -*-
"""K-STAT-TIER3-ENGINE-SPEC — 3등 엔진 정밀분석. READ-ONLY. 새 knob 없음.

범위=stat만. ge3/등수 성적클레임 금지. 1237아님. DB 쓰기 없음.
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KSTAT_TIER3_ENGINE_SPEC.json"
OUT_MD = ROOT / "reports" / "20260815_KSTAT_TIER3_ENGINE_SPEC.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

C45_6 = 8145060
N_T3 = 228  # C(6,5)*38
N_T2 = 6
N_H5 = 234  # 5맞 = 2등+3등
P_T3 = N_T3 / C45_6
P_H5 = N_H5 / C45_6


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _db() -> sqlite3.Connection:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
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


def _fours(nums: list[int]) -> set[tuple[int, ...]]:
    return set(combinations(sorted(nums), 4))


def _fives(nums: list[int]) -> set[tuple[int, ...]]:
    return set(combinations(sorted(nums), 5))


def schonheim_c_v65(v: int) -> int:
    """Schönheim lower bound C(v,6,5) >= ceil(C(v,5)/C(6,5))."""
    if v < 5:
        return 0
    c_v5 = math.comb(v, 5)
    return math.ceil(c_v5 / 6)


def measure() -> dict[str, Any]:
    conn = _db()
    try:
        draws_max = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
        n_draws = int(conn.execute("SELECT COUNT(*) FROM lotto_draws").fetchone()[0])
        pred_1237 = int(
            conn.execute(
                "SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237"
            ).fetchone()[0]
        )

        led = conn.execute(
            """
            SELECT role, hits, bonus_hit, nums_json
            FROM testlotto_pool_hit_ledger
            WHERE brain_tag='stat' AND kind='pool'
            """
        ).fetchall()
        by_role_hits: dict[str, Counter] = {}
        h5 = 0
        h5_role: Counter[str] = Counter()
        for r in led:
            role = str(r["role"] or "")
            h = int(r["hits"] or 0)
            by_role_hits.setdefault(role, Counter())[h] += 1
            if h >= 5:
                h5 += 1
                h5_role[role] += 1

        cover_src: Counter[str] = Counter()
        t4_skill: list[int] = []
        t4_cover: list[int] = []
        t4_union: list[int] = []
        t5_skill: list[int] = []
        t5_cover: list[int] = []
        outside_mean: list[float] = []
        n_cache_stat = 0
        role_ok = 0
        role_bad = 0
        cache_rows = conn.execute(
            """
            SELECT draw_no, pool_json FROM testlotto_pool_view_cache
            WHERE brain='stat' AND draw_no BETWEEN 1037 AND 1236
            ORDER BY draw_no
            """
        ).fetchall()
        for row in cache_rows:
            sets = json.loads(row["pool_json"] or "[]")
            if not isinstance(sets, list):
                continue
            stat_sets = [s for s in sets if str(s.get("brain_tag") or "stat") == "stat"]
            if len(stat_sets) != 10:
                stat_sets = sets if len(sets) == 10 else []
            if len(stat_sets) != 10:
                continue
            n_cache_stat += 1
            skill = [s for s in stat_sets if str(s.get("role")) == "skill_native"]
            cover = [s for s in stat_sets if str(s.get("role")) == "cover_r3"]
            shape = [s for s in stat_sets if str(s.get("role")) == "shape_r2"]
            if len(skill) == 5 and len(cover) == 3 and len(shape) == 2:
                role_ok += 1
            else:
                role_bad += 1
            for s in cover:
                cover_src[str(s.get("source") or "")] += 1
            su: set[int] = set()
            f4s: set[tuple[int, ...]] = set()
            f5s: set[tuple[int, ...]] = set()
            for s in skill:
                nums = [int(x) for x in (s.get("nums") or [])]
                su |= set(nums)
                f4s |= _fours(nums)
                f5s |= _fives(nums)
            f4c: set[tuple[int, ...]] = set()
            f5c: set[tuple[int, ...]] = set()
            outs = []
            for s in cover:
                nums = [int(x) for x in (s.get("nums") or [])]
                f4c |= _fours(nums)
                f5c |= _fives(nums)
                outs.append(len(set(nums) - su) if su else 0)
            t4_skill.append(len(f4s))
            t4_cover.append(len(f4c))
            t4_union.append(len(f4s | f4c))
            t5_skill.append(len(f5s))
            t5_cover.append(len(f5c))
            if outs:
                outside_mean.append(mean(outs))

        # official 5-cores
        drows = conn.execute(
            "SELECT draw_no, num1,num2,num3,num4,num5,num6, bonus FROM lotto_draws ORDER BY draw_no"
        ).fetchall()
        cores: Counter[tuple[int, ...]] = Counter()
        num_in_core: Counter[int] = Counter()
        num_in_win: Counter[int] = Counter()
        for d in drows:
            win = [int(d[k]) for k in ("num1", "num2", "num3", "num4", "num5", "num6")]
            for n in win:
                num_in_win[n] += 1
            for five in combinations(sorted(win), 5):
                cores[five] += 1
                for n in five:
                    num_in_core[n] += 1
        # proportionality check: core_count[n] == 5 * win_count[n]
        prop_bad = sum(
            1 for n in range(1, 46) if num_in_core[n] != 5 * num_in_win[n]
        )

        hw = conn.execute(
            """
            SELECT as_of_draw, payload_json FROM testlotto_role_homework
            WHERE brain_tag='stat' AND role='cover_r3'
            ORDER BY as_of_draw DESC LIMIT 1
            """
        ).fetchone()
        hw_npos = None
        hw_asof = None
        if hw:
            hw_asof = int(hw["as_of_draw"])
            payload = json.loads(hw["payload_json"] or "{}")
            hw_npos = sum(1 for i in range(1, 46) if float(payload.get(str(i), 0) or 0) > 0)

        prize_3 = None
        try:
            prize_3 = int(
                conn.execute(
                    "SELECT SUM(winner_count) FROM testlotto_draw_prize_tiers WHERE tier_rank=3"
                ).fetchone()[0]
                or 0
            )
        except Exception:
            prize_3 = None
    finally:
        conn.close()

    n_set_200 = 200 * 15
    n_cover_200 = 200 * 3
    bounds = {v: schonheim_c_v65(v) for v in (7, 8, 9, 10, 12, 15, 18, 22, 30, 45)}

    return {
        "id": "K-STAT-TIER3-ENGINE-SPEC",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "read_only": True,
        "db_write": False,
        "draws_max": draws_max,
        "n_draws": n_draws,
        "pred_1237": pred_1237,
        "math": {
            "C45_6": C45_6,
            "n_tier3_tickets": N_T3,
            "n_tier2_tickets": N_T2,
            "n_hits5_tickets": N_H5,
            "P_tier3": round(P_T3, 12),
            "P_hits5": round(P_H5, 12),
            "E_tier3_per_ticket": round(P_T3, 12),
            "E_tier3_3000": round(n_set_200 * P_T3, 6),
            "E_hits5_3000": round(n_set_200 * P_H5, 6),
            "E_tier3_cover600": round(n_cover_200 * P_T3, 6),
            "source": "C(6,5)*38=228 / C(45,6); K-P P5=234/C(45,6)",
        },
        "schonheim_C_v_6_5": bounds,
        "ledger_stat_pool": {
            "n_rows": len(led),
            "hits_hist_by_role": {
                k: {str(h): int(c) for h, c in sorted(v.items())}
                for k, v in by_role_hits.items()
            },
            "hits_ge5_total": h5,
            "hits_ge5_by_role": dict(h5_role),
        },
        "cache_1037_1236": {
            "n_stat10": n_cache_stat,
            "role_5_3_2_ok": role_ok,
            "role_bad": role_bad,
            "cover_source": dict(cover_src),
            "t4_skill_mean": round(mean(t4_skill), 4) if t4_skill else None,
            "t4_cover_mean": round(mean(t4_cover), 4) if t4_cover else None,
            "t4_union_mean": round(mean(t4_union), 4) if t4_union else None,
            "t5_skill_mean": round(mean(t5_skill), 4) if t5_skill else None,
            "t5_cover_mean": round(mean(t5_cover), 4) if t5_cover else None,
            "cover_outside_per_set_mean": round(mean(outside_mean), 4) if outside_mean else None,
        },
        "official_5cores": {
            "n_draws": len(drows),
            "n_core_rows": 6 * len(drows),
            "unique_cores": len(cores),
            "repeat_cores": sum(1 for c, n in cores.items() if n > 1),
            "max_core_repeat": max(cores.values()) if cores else 0,
            "core_freq_equals_5x_win_freq_bad": prop_bad,
            "note": "번호 n의 5코어 등장=5×공식1등등장. 새 신호 아님.",
        },
        "role_hw_cover_stat_latest": {"as_of": hw_asof, "n_pos": hw_npos},
        "prize_tier3_winner_sum": prize_3,
        "live_flags": None,
    }


def _probe_cover_source(sample: list[int]) -> dict[str, Any]:
    """READ-ONLY: 라이브 cover source 라벨. DB 쓰기 없음."""
    import random

    import app.testlotto.signal_pool as sp
    from app.testlotto.data_service import _get_draws_before
    from app.testlotto.learn_state_cutoff import set_learn_as_of
    from app.testlotto.role_slots import build_cover_r3_sets

    src: Counter[str] = Counter()
    peek = 0
    for dno in sample:
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        max_mat = max((int(d["draw_no"]) for d in draws), default=0)
        if max_mat >= dno:
            peek += 1
            continue
        random.seed(42)
        pool = sp.expand_pool(draws, dno, seed=42, brains=["stat"])
        skill = [s for s in pool if str(s.get("role")) == "skill_native"]
        cover = [s for s in pool if str(s.get("role")) == "cover_r3"]
        if not cover:
            cover = build_cover_r3_sets(
                lambda dr, n: sp.expand_pool(dr, dno, seed=42, brains=["stat"])[:5],
                draws,
                brain_tag="stat",
                skill_sets=skill,
                seed=42,
                draw_no=dno,
                n=3,
            )
        for s in cover:
            src[str(s.get("source") or "")] += 1
    return {
        "n_sample": len(sample),
        "peek_fail": peek,
        "source": dict(src),
        "note": "캐시 payload는 pool source 미저장. 라이브 expand만 라벨 확인.",
    }


def _flags() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.role_homework import COVER_MIN_HITS
    from app.testlotto.role_slots import COVER_SELECT_MODE, SHAPE_CORE_MODE
    from app.testlotto.stat_pool_learn import STAT_POOL_LEARN_WIRE
    from app.testlotto.structure_cover import STRUCTURE_COVER_WIRE

    return {
        "ROLE_TIER_LEARN_BRAINS": sorted(sp.ROLE_TIER_LEARN_BRAINS),
        "COVER_SELECT_MODE": COVER_SELECT_MODE,
        "SHAPE_CORE_MODE": SHAPE_CORE_MODE,
        "COVER_MIN_HITS": int(COVER_MIN_HITS),
        "STAT_POOL_LEARN_WIRE": bool(STAT_POOL_LEARN_WIRE),
        "STRUCTURE_COVER_WIRE": bool(STRUCTURE_COVER_WIRE),
        "REPACK_ROLE_QUOTA_WIRE": bool(sp.REPACK_ROLE_QUOTA_WIRE),
        "REPACK_RECOMBINE_MODE": sp.REPACK_RECOMBINE_MODE,
    }


def _md(o: dict[str, Any]) -> str:
    m = o.get("math") or {}
    led = o.get("ledger_stat_pool") or {}
    ca = o.get("cache_1037_1236") or {}
    oc = o.get("official_5cores") or {}
    sh = o.get("schonheim_C_v_6_5") or {}
    hw = o.get("role_hw_cover_stat_latest") or {}
    lines = [
        "# K-STAT-TIER3-ENGINE-SPEC — 3등 엔진 정밀분석 (보조 부품 필요성)",
        "",
        f"시각: {o['as_of']} · **{o.get('verdict')}** · 범위=**stat만** · READ-ONLY · ge3미클레임 · 1237아님",
        "근거: 본턴 DB실측 JSON · `role_slots.build_cover_r3_sets` · `role_homework` · "
        "S0 SPEC · K-P · covering 문헌",
        "",
        "## 0) 한 줄 답",
        "",
        "**지금 6~8번(`cover_r3`)은 3등을 예측·학습하는 엔진이 아니다.** "
        "같은 과거학습 `predict_sets`를 다시 뽑아 1~5 밖 번호를 고르는 **포트폴리오 선택기**다. "
        "3등(본번호 5맞)의 기하학은 오히려 9~10번(`shape_r2`)의 ‘핵심5+가변1’에 가깝다.",
        "",
        "**‘과거 3등 당첨사례를 학습해 3등P를 올리는’ 보조 엔진은 필요 없다(기각).** "
        "우리 원장의 5맞 표본은 사실상 0이고, 공식 1등의 5코어 빈도는 기존 번호빈도와 **완전 비례**라 새 신호가 아니다 (K-P).",
        "",
        "**3등 형태에 맞는 보조는 이미 있다: 9~10 `shape_r2`(핵심5+가변1).** "
        "문헌의 휠(작은 풀을 3장이 겹쳐 덮기)은 지금 S1(밖 번호·겹침↓)과 **반대 기하**라 자동 다음이 아니다. "
        "풀-먼저 greedy t-cover는 후보로만 남긴다. APPLY는 형 GO 후.",
        "",
        "## 1) 3등이 무엇인가 (규칙·수학)",
        "",
        "| 등수 | 조건 | 티켓 수 / C(45,6) |",
        "|------|------|-------------------|",
        f"| 1등 | 본번호 6 | 1 / {m.get('C45_6')} |",
        f"| 2등 | 본번호 5 + 보너스 | {m.get('n_tier2_tickets')} |",
        f"| 3등 | 본번호 5 (보너스 아님) | **{m.get('n_tier3_tickets')}** |",
        f"| 5맞 합 | 2등+3등 | {m.get('n_hits5_tickets')} |",
        "",
        f"P(3등)=228/8,145,060 ≈ **1/{round(1/P_T3) if P_T3 else '미확인'}**. "
        f"200회×15장=3000장의 E[3등]≈**{m.get('E_tier3_3000')}**. "
        f"cover 3장×200=600장의 E[3등]≈**{m.get('E_tier3_cover600')}**.",
        "",
        "원장맞춤 200회 고유 3등 **0** 은 성적 실패가 아니라 이 기대값과 맞다. "
        "K-P: 세트 5적중 학습신호 부재 (P₅≈2.87e-5).",
        "",
        "3등의 **형태** = 당첨 6개 중 5개를 고정(5코어) + 나머지 1개는 틀린 번호. "
        "공식 1등 한 회차에 5코어는 정확히 **6개**.",
        "",
        "## 2) 지금 엔진이 실제로 하는 일 (코드)",
        "",
        "| 칸 | 이름 | 3등과의 관계 | 자체 3등 학습기 |",
        "|----|------|---------------|-----------------|",
        "| 1~5 | skill_native | 과거학습 본류. 3등 목적함수 없음 | 없음 (miss_pattern 등) |",
        "| 6~8 | cover_r3 | **3등 엔진 아님**. 2nd `predict_sets` 5장 중 skill union 밖 번호 최대 3장 | 원장 3맞 번호 가중(숙제)만 |",
        "| 9~10 | shape_r2 | **3등 형태에 가장 가까움**(5고정+1교체). 라벨은 2등용 | 과거 보너스·5맞 표. 타깃 보너스 금지 |",
        "| 몰아주기 | focus_r1 | 복사4+보완1. 5코어 조립 아님 | 없음 |",
        "",
        f"라이브 플래그: `{json.dumps(o.get('live_flags') or {}, ensure_ascii=False)}`",
        "",
        "cover 숙제(`COVER_MIN_HITS=3`)는 **5등(3맞) 근사 복습**이다. 주석 그대로. "
        "hits≥5 가산은 있으나 표본이 비면 항등 0.",
        "",
        "## 3) 본턴 실측 (모니터 · 클레임 금지)",
        "",
        f"- draws MAX **{o.get('draws_max')}** · pred_1237 **{o.get('pred_1237')}** · 쓰기 없음",
        f"- ledger stat pool 행 `{json.dumps(led.get('hits_hist_by_role') or {}, ensure_ascii=False)}`",
        f"- 원장 hits≥5 합 **{led.get('hits_ge5_total')}** · 역할 `{json.dumps(led.get('hits_ge5_by_role') or {}, ensure_ascii=False)}`",
        f"- 캐시 1037~1236 stat10 **{ca.get('n_stat10')}** · 역할5+3+2 일치 **{ca.get('role_5_3_2_ok')}** · 불일치 **{ca.get('role_bad')}**",
        f"- 캐시 cover source(미저장 가능) `{json.dumps(ca.get('cover_source') or {}, ensure_ascii=False)}`",
        f"- 라이브 source probe `{json.dumps(o.get('cover_source_probe') or {}, ensure_ascii=False)}`",
        f"- 4-subset 커버 mean: skill **{ca.get('t4_skill_mean')}** / cover **{ca.get('t4_cover_mean')}** / 합 **{ca.get('t4_union_mean')}**",
        f"- 5-subset 커버 mean: skill **{ca.get('t5_skill_mean')}** / cover **{ca.get('t5_cover_mean')}**",
        f"- cover 장당 skill-union 밖 번호 mean **{ca.get('cover_outside_per_set_mean')}**",
        f"- 공식 5코어: 행 **{oc.get('n_core_rows')}** · 고유 **{oc.get('unique_cores')}** · 반복코어 **{oc.get('repeat_cores')}** · "
        f"빈도=5×1등빈도 불일치 **{oc.get('core_freq_equals_5x_win_freq_bad')}**",
        f"- cover 숙제 최신 as_of **{hw.get('as_of')}** n_pos **{hw.get('n_pos')}**",
        f"- 공식 3등 당첨자 수 합(표) **{o.get('prize_tier3_winner_sum')}** — 당첨**티켓 번호**는 없음",
        "",
        "## 4) ‘과거 3등 사례 학습’ 후보 — 채택/기각",
        "",
        "| 부품 | 재료 | 판정 | 이유 |",
        "|------|------|------|------|",
        "| A. 우리 원장 5맞(3·2등) 복습 | ledger hits≥5 | **기각(표본0)** | 200×15 E≈0.08. 학습기 불가 |",
        "| B. 공식 1등의 5코어 카탈로그 | lotto_draws leave-1 | **기각(중복)** | 번호빈도×5. skill과 동일 축 |",
        "| C. 공식 3등 당첨자 티켓 | 판매점/당첨자 조합 | **불가** | DB에 티켓 번호 없음. 인원수만 있을 수 있음 |",
        "| D. 3등P 손실함수 / 5맞 최적화 | 목적함수 | **기각** | LIST_V3·K-P·초기하. 게이트 금지 |",
        "| E. 보너스 맞춰 2등/3등 분리학습 | bonus 입력 | **기각** | 타깃 보너스 미지 · T-NB1 |",
        "| F. STRUCTURE_COVER / PAIR_COVER | 홀짝·합·희소쌍 | **재탕금지** | 기존 HOLD · ge3↓ 서베이 |",
        "| G. LSTM·유튜브 필터·WIN_1Y | 시계열 | **재탕금지** | 잠금 리스트 |",
        "| **H. 풀-먼저 greedy t-cover 생성기** | skill union(또는 숙제 상위 n) 위 3장 | **채택(후보)** | 문헌 covering. P↑클레임 아님 |",
        "| I. shape를 3등 형태 슬롯으로 재라벨 | 문서/역할 의미 | **DOC채택** | 기하=5+1. 코드 APPLY 아님 |",
        "",
        "## 5) 문헌 · 외부 엔진 아이디어 (복붙 금지 · 프로세스만)",
        "",
        "| 출처 | 요지 | 우리 3장 규모 |",
        "|------|------|----------------|",
        "| Covering design C(v,6,5) · La Jolla / Covering Repository | 풀 v의 모든 5셋을 6장 티켓으로 덮음 | Schönheim 하한 아래. **3장으로 5맞 보장 불가** |",
        "| Lottery wheeling / abbreviated wheel | ‘풀 안에 당첨 k개가 들어오면 t맞 보장’ | 조건부. 풀을 맞추는 문제는 그대로 skill |",
        "| LuckyPicks Smart Coverage | 예산 고정 시 3·4맞 커버리지 greedy 최대화 | **우리 예산=cover 3장**. 유일한 실용 매핑 |",
        "| Nerdland greedy set-cover | 미커버 t-subset 최다 티켓을 반복 선택 | H 구현 스케치 |",
        "| Thaler–Ziemba / Moffitt | P(win) 불변 · 스킬은 몫 | 게이트=prefer/prize 유지 |",
        "| Stern–Cover 1989 | pick marginal | 판매비율 없음 → 흉내 금지 |",
        "| Hai4320 | null·고백 | E[3등] 병기 |",
        "",
        "Schönheim 하한 C(v,6,5) ≥ C(v,5)/6 (3장으로 5커버 가능한 v는 사실상 없음):",
        "",
        f"`{json.dumps(sh, ensure_ascii=False)}`",
        "",
        "예: 번호 10개 풀의 모든 5코어를 덮으려면 ≥**42장**. 우리 cover는 3장. "
        "풀 휠 C(10,6)=210장. 그래서 ‘3등 보장 엔진’은 부품이 아니라 자본 전략이다.",
        "",
        "## 6) 그래서 필요한 보조 부품인가",
        "",
        "**3등P를 올리는 학습 부품 — 아니오.** 재료도 없고 수학도 금지.",
        "",
        "**3등 형태 부품 — 이미 있음.** `shape_r2` = 5코어 고정 + 6번째만 교체. "
        "3장으로 같은 5코어를 더 쓰는 것은 cover를 shape로 옮기는 재배치일 뿐 새 학습기가 아니다.",
        "",
        "**휠 생성 부품 — 후보이나 S1과 충돌.** 문헌 covering은 ‘작은 풀을 겹쳐 덮기’. "
        "지금 cover는 밖 번호 mean **2.94** · 4-subset이 skill과 거의 안 겹침(t4_union≈75+45). "
        "S1을 유지하면 휠을 넣지 않는다. 휠을 넣으면 S1을 되돌리는 셈이다. 자동 진행 금지.",
        "",
        "구현 스케치(APPLY 아님 · 형 GO 시 1건 · S1 롤백 각오):",
        "",
        "```text",
        "풀 V = skill union 상위 n (n≈10~15)  — 밖 번호 최대와 반대",
        "3번 반복: 아직 안 덮인 4-subset을 가장 많이 덮는 6셋 1장",
        "게이트: prefer/prize 비악화 · 모니터= t4 overlap (등수 금지)",
        "롤백: COVER_GEN_MODE='resample' + COVER_SELECT_MODE='outside_union'",
        "```",
        "",
        "S2 consensus는 prefer 실패로 HOLD. 3등용으로 재탕하지 않는다.",
        "",
        "## 7) 하지 말 것",
        "",
        "- 원장 4등12/5등55/3등0 을 엔진 성적로 쓰기",
        "- 5맞 손실함수 · 보너스 입력 · 10장 1등/3등 보장",
        "- STRUCTURE/PAIR_COVER · WIN_1Y · HINT 0.15 · ASSOC · S2 consensus 재탕",
        "- markov/review · 1237 양산 · 동결 3종",
        "",
        "## 8) 다음",
        "",
        "권고 다음 1건(형 선택):",
        "1. **3등 학습 엔진 닫기** + 원래 #2 `K-STAT-PROCESS-AUDIT-S5LIVE` READ 재개",
        "2. shape=3등형태 문서만 고정 (코드 불변)",
        "3. greedy-t4 휠 — S1과 충돌. **별도 GO 없으면 안 함**",
        "",
        "본턴 코드 APPLY 없음. 1237아님.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    flags = _flags()
    out = measure()
    out["live_flags"] = flags
    out["cover_source_probe"] = _probe_cover_source(list(range(1217, 1237)))
    out["verdict"] = "SPEC_OK"
    # HARD: read-only sanity
    hard = bool(
        out["pred_1237"] == 0
        and out["draws_max"] == 1236
        and out["official_5cores"]["core_freq_equals_5x_win_freq_bad"] == 0
        and flags["ROLE_TIER_LEARN_BRAINS"] == ["stat"]
    )
    out["hard_ok"] = hard
    if not hard:
        out["verdict"] = "SPEC_FAIL"
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _md(out)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({
        "verdict": out["verdict"],
        "hard": hard,
        "E_tier3_3000": out["math"]["E_tier3_3000"],
        "hits_ge5": out["ledger_stat_pool"]["hits_ge5_total"],
        "cache": out["cache_1037_1236"],
        "cores": out["official_5cores"],
        "schonheim_10": out["schonheim_C_v_6_5"].get("10"),
        "hw": out["role_hw_cover_stat_latest"],
        "prize3": out["prize_tier3_winner_sum"],
        "src_probe": out.get("cover_source_probe"),
    }, ensure_ascii=False, indent=2))
    return 0 if hard else 1


if __name__ == "__main__":
    raise SystemExit(main())
