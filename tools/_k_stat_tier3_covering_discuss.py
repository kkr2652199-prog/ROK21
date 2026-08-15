# -*- coding: utf-8 -*-
"""K-STAT-TIER3-COVERING-DISCUSS — READ-ONLY 실측. APPLY 없음.

캐시 1037~1236 stat 200회 Jaccard/union + 코드 경로 기록.
DB 쓰기 없음. 1237아님.
"""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KSTAT_TIER3_COVERING_DISCUSS.json"
OUT_MD = ROOT / "reports" / "20260815_KSTAT_TIER3_COVERING_DISCUSS.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def _nums(s: dict) -> list[int]:
    return [int(x) for x in (s.get("nums") or [])]


def schonheim(v: int, k: int, t: int) -> int:
    if t == 0:
        return 1
    if k < t or v < k:
        return 0
    if t == 1:
        return math.ceil(v / k)
    return math.ceil(v / k * schonheim(v - 1, k - 1, t - 1))


def measure() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    draws = {
        int(r["draw_no"]): {int(r[f"num{i}"]) for i in range(1, 7)}
        for r in conn.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws"
        )
    }
    rows = list(
        conn.execute(
            """
            SELECT draw_no, pool_json, repack_json
            FROM testlotto_pool_view_cache
            WHERE brain='stat' AND draw_no BETWEEN ? AND ?
            ORDER BY draw_no
            """,
            (LO, HI),
        )
    )
    conn.close()

    jac_shape_set1: list[float] = []
    jac_cover_skill: list[float] = []
    union_skill: list[int] = []
    union10: list[int] = []
    n_ok = 0
    cond3 = cond3_covered = 0
    cond5 = cond5_hit5 = 0
    for r in rows:
        dno = int(r["draw_no"])
        pool = json.loads(r["pool_json"] or "[]")
        rep = json.loads(r["repack_json"] or "[]")
        if len(pool) != 10:
            continue
        skill = [s for s in pool if str(s.get("role")) == "skill_native"]
        cover = [s for s in pool if str(s.get("role")) == "cover_r3"]
        shape = [s for s in pool if str(s.get("role")) == "shape_r2"]
        if len(skill) != 5 or len(cover) != 3 or len(shape) != 2:
            continue
        n_ok += 1
        skill = sorted(skill, key=lambda s: int(s.get("set_no") or s.get("pred_set_no") or 0))
        set1 = set(_nums(skill[0]))
        su: set[int] = set()
        for s in skill:
            su |= set(_nums(s))
        u10: set[int] = set(su)
        for s in cover + shape:
            u10 |= set(_nums(s))
        union_skill.append(len(su))
        union10.append(len(u10))
        # S0와 동일: cover×skill 전쌍 평균, shape×set1 평균
        jac_cover_skill.append(
            mean(_jaccard(set(_nums(c)), set(_nums(sk))) for c in cover for sk in skill)
        )
        jac_shape_set1.append(mean(_jaccard(set(_nums(sh)), set1) for sh in shape))
        actual = draws.get(dno)
        if not actual:
            continue
        inter = actual & su
        tickets = [_nums(s) for s in pool] + [_nums(s) for s in rep]
        if len(inter) >= 3:
            cond3 += 1
            triples = list(combinations(sorted(inter), 3))
            ok = False
            for tr in triples:
                ts = set(tr)
                if any(ts <= set(t) for t in tickets if len(t) == 6):
                    ok = True
                    break
            if ok:
                cond3_covered += 1
        if len(inter) >= 5:
            cond5 += 1
            if any(len(set(t) & actual) >= 5 for t in tickets if len(t) == 6):
                cond5_hit5 += 1

    def _m(xs: list[float], nd: int = 4) -> float | None:
        return round(mean(xs), nd) if xs else None

    return {
        "n_cache_ok": n_ok,
        "jaccard_shape_vs_set1_mean": _m(jac_shape_set1),
        "jaccard_cover_vs_skill_mean": _m(jac_cover_skill),
        "skill_union_mean": _m([float(x) for x in union_skill]),
        "union10_mean": _m([float(x) for x in union10]),
        "s0_ref": {
            "jaccard_shape_vs_set1_mean": 0.7143,
            "jaccard_cover_vs_skill_mean": 0.1059,
            "source": "docs/benchmarks/20260814_KSTAT_ENGINE_EVOLVE_SPEC.json",
        },
        "cond_3_in_skill_union": {
            "n_draws": cond3,
            "n_some_ticket_has_that_triple": cond3_covered,
            "note": "V=skill union. 3-if-3 모니터(5등 형태). 3등=5맞 아님.",
        },
        "cond_5_in_skill_union": {
            "n_draws": cond5,
            "n_some_ticket_hits5": cond5_hit5,
            "note": "V에 당첨 5개 들어온 회차에서 어느 장이 5맞(3등형태)인가. 표본소.",
        },
    }


def _flags() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.role_slots import COVER_SELECT_MODE, SHAPE_CORE_MODE

    return {
        "COVER_SELECT_MODE": COVER_SELECT_MODE,
        "SHAPE_CORE_MODE": SHAPE_CORE_MODE,
        "ROLE_TIER_LEARN_BRAINS": sorted(sp.ROLE_TIER_LEARN_BRAINS),
        "POOL_SLOTS": int(sp.POOL_SLOTS_PER_BRAIN),
        "POOL_UNION_CAP": int(sp.POOL_UNION_CAP),
        "REPACK_SETS": int(sp.REPACK_SETS_PER_BRAIN),
        "REPACK_ROLE_QUOTA_WIRE": bool(sp.REPACK_ROLE_QUOTA_WIRE),
        "REPACK_RECOMBINE_MODE": sp.REPACK_RECOMBINE_MODE,
    }


def _md(o: dict[str, Any]) -> str:
    m = o.get("measure") or {}
    lj = o.get("lajolla_C_v_6_3") or {}
    sh = o.get("schonheim_C_v_6_3") or {}
    sh5 = o.get("schonheim_C_v_6_5") or {}
    f = o.get("flags") or {}
    c3 = m.get("cond_3_in_skill_union") or {}
    c5 = m.get("cond_5_in_skill_union") or {}
    return "\n".join(
        [
            "# K-STAT-TIER3-COVERING-DISCUSS — 3-covering 논의 (APPLY 없음)",
            "",
            f"시각: {o['as_of']} · **{o.get('verdict')}** · READ-ONLY · 1237아님 · ge3/3등P 클레임 금지",
            "범위=stat만. 형 질문서 5항에 코드·캐시·La Jolla로 답함.",
            "",
            "## 0) 한 줄 의견",
            "",
            "**지금 `cover_r3`는 covering이 아니다. 같은 `predict_sets`를 다시 뽑아 고르는 클론/재샘플이다.**",
            "",
            "형 재해석(풀 N + 3-covering wheel)은 문헌과 맞다. 다만 이름부터 고쳐야 한다. "
            "한국 로또 **3등 = 본번호 5맞**. covering의 **t=3은 3개 묶음을 덮는 것**이라, "
            "‘3개 적중 시 3등 보장’은 규칙과 안 맞다. 맞는 문장은 "
            "**‘풀 안에서 당첨 3개가 들어오면, 그 3개를 품은 장이 최소 1장’ = 5등 형태 보장**이다. "
            "진짜 3등(5맞) 보장은 C(v,6,5)라 N=10만 해도 ≥42장이다.",
            "",
            "3장(지금 덮기 칸)으로는 **N≥7에서 완전 3-covering 불가**(La Jolla C(7,6,3)=**4**). "
            "N=12는 **15장**. slots=2·cap=4는 몰아주기 복사 한도이지 덮기 장수가 아니다. "
            "발권은 5장이라, 덮기 휠을 넣어도 발권에 전부 안 실릴 수 있다.",
            "",
            "권고: **지금 APPLY 하지 말 것.** 먼저 보장 문장을 5등(t=3) / 3등(t=5) 중 하나로 고정. "
            "그다음 장수 계약을 정한 뒤 SPEC.",
            "",
            "## 1) cover_r3는 진짜 covering인가",
            "",
            "**클론/재샘플이다.** 풀을 확정한 뒤 블록을 깔지 않는다.",
            "",
            "`expand_pool` (`signal_pool.py` 270행): `build_cover_r3_sets(mod.predict_sets, ...)`",
            "`build_cover_r3_sets` (`role_slots.py` 105행): `cands = predict_sets_fn(draws, 5)` — "
            "**같은 엔진 5장을 다른 시드로 다시 뽑고**, S1이면 skill union **밖** 번호가 많은 3장을 고른다. "
            "부족하면 skill 1칸 교체(`cover_fill_morph`).",
            "",
            "문헌 covering = (1) 번호 풀 V를 정하고 (2) V의 t-subset을 k-블록으로 덮기. "
            "지금 덮기는 (1)도 명시적 V가 없고 (2)도 없다. S1은 오히려 V(skill union) **밖으로** 나간다.",
            "",
            "### 캐시 200회 재실측 (1037~1236 · 쓰기없음)",
            "",
            f"- n_ok **{m.get('n_cache_ok')}**",
            f"- shape vs set1 Jaccard **{m.get('jaccard_shape_vs_set1_mean')}** (S0 참조 0.7143)",
            f"- cover vs skill 전쌍평균 Jaccard **{m.get('jaccard_cover_vs_skill_mean')}** (S0 0.1059 · S1후)",
            f"- skill union mean **{m.get('skill_union_mean')}** · union10 mean **{m.get('union10_mean')}**",
            "",
            "shape≈0.714는 5공유/7합(한 칸 변형)과 같다. S2 HOLD(set1)라 그대로다. "
            "cover Jaccard는 S1 밖번호 때문에 S0(0.1059)과 다를 수 있다. 그래도 covering 블록 배치는 아니다.",
            "",
            "## 2) 파이프라인에 휠을 끼울 자리",
            "",
            "| 지점 | 수정 | 적합 |",
            "|------|------|------|",
            "| **`build_cover_r3_sets` 교체** | 후보=`predict_sets` 대신 V의 covering 블록 3장 | **최소 수정**. 1~5 불변. 플래그로 롤백 |",
            "| `expand_pool` 뒤 별 레이어 | pool10 계약을 깨고 장수 증가 | UI/원장 10+5와 충돌 |",
            "| `assemble_signal_union` (몰아주기) | 복사4+보완1을 휠로 교체 | **S3/S4와 충돌**. 비권고 |",
            "| 발권 quota5 | 휠 15장을 5장으로 자름 | 보장 깨짐 |",
            "",
            "결정론: 고정 표(La Jolla 블록을 V에 번호순으로 사상)는 **seed 무관**. "
            "cover 칸만 그렇게 하면 그 칸은 K-E(시드 비재현)를 우회한다. "
            "1~5 `predict_sets`의 `random.choices`는 동결 그대로. 휠이 1~5를 고치지 않는다.",
            "",
            f"라이브 플래그: `{json.dumps(f, ensure_ascii=False)}`",
            "",
            "## 3) N과 장수 (La Jolla 실측 페이지)",
            "",
            "C(v,6,3) = 풀 v에서 모든 3묶음을 6장 티켓으로 덮는 **최소 장수**. "
            "출처: `ljcr.dmgordon.org/cover/show_cover.php?v=*&k=6&t=3` (2026-08-15 fetch).",
            "",
            "| v=N | C(v,6,3) | Schönheim 하한 | 우리 덮기 3장으로 완전보장? |",
            "|-----|----------|----------------|------------------------------|",
            f"| 7 | **{lj.get('7')}** | {sh.get('7')} | 아니오 (4>3) |",
            f"| 8 | **{lj.get('8')}** | {sh.get('8')} | 아니오 |",
            f"| 9 | **{lj.get('9')}** | {sh.get('9')} | 아니오 |",
            f"| 10 | **{lj.get('10')}** | {sh.get('10')} | 아니오 |",
            f"| 12 | **{lj.get('12')}** | {sh.get('12')} | 아니오 (15>3) |",
            f"| 15 | {lj.get('15')} | {sh.get('15')} | 아니오 (≈31>3) |",
            "",
            "N=12~15 ‘3-win 완전보장’에 필요한 장수 ≈ **15~31**. 덮기 3장·발권 5장 둘 다 부족하다.",
            "",
            "진짜 3등(5맞) 보장 C(v,6,5): La Jolla **C(10,6,5)=50** (Schönheim 하한 42). "
            f"Schönheim 표: `{json.dumps(sh5, ensure_ascii=False)}`. N=12 ≥132. 10세트·발권5로 불가.",
            "",
            "slots=**2** · cap=**4** 는 몰아주기 **복사 한도**다. 덮기 3장을 15장으로 늘리지 않는다. "
            "늘리려면 pool10 계약·캐시·원장·UI를 같이 바꿔야 한다. 발권 경로는 여전히 quota **5장** "
            "(L12b). 휠 15장을 만들어도 사는 장은 5장이다.",
            "",
            "## 4) 검증 축이 타당한가",
            "",
            "**문장을 고치면 타당하다. 지금 문장 그대로는 타당하지 않다.**",
            "",
            "- 틀린 축: ‘3개 맞은 회차에서 3등(5맞) 티켓이 1장’ — t=3 휠의 보장이 아니다. 표본도 거의 0.",
            "- 맞는 축(t=3 휠): **V∩당첨 ≥3인 회차**에서, 그 교집합의 어떤 3묶음이든 **어느 장에 통째로 들어갔는가**.",
            "- 게이트는 그대로 prefer/prize 비악화. 위 축은 **모니터·설계검증**이지 APPLY 성적이 아니다.",
            "",
            "현재 엔진(휠 없음)으로 같은 모니터를 캐시 200회에 얹으면:",
            f"- skill union에 당첨 3개 이상 **{c3.get('n_draws')}**회 · 그중 어느 장이 그 3묶음을 품음 **{c3.get('n_some_ticket_has_that_triple')}**",
            f"- skill union에 당첨 5개 이상 **{c5.get('n_draws')}**회 · 그중 5맞 장 **{c5.get('n_some_ticket_hits5')}**",
            "",
            "이 숫자는 ‘휠이 없어서 실패’가 아니라 **지금 구조의 베이스라인**이다. "
            "V가 넓으면(union≈23) 3개가 들어올 확률은 높고, 그 3개를 한 장에 모을 확률은 별개다.",
            "",
            "## 5) 형이 먼저 알아야 할 함정 3개",
            "",
            "1. **이름.** 3-covering ≠ 3등 엔진. 혼동한 채 APPLY하면 5등 보장을 3등 성공으로 읽게 된다 (K-O·K-P와 충돌).",
            "2. **장수.** 완전 보장에 필요한 장이 칸보다 많다. 3장 greedy는 ‘Smart Coverage’(부분 커버율)이지 보장이 아니다. "
            "보장을 쓰려면 장수를 늘리거나 N을 6~8로 줄여야 한다. N을 줄이면 당첨 3개가 V에 들어올 일 자체가 줄어 보장이 거의 안 발동한다.",
            "3. **S1·S3·S4와 반대 기하.** 휠은 작은 풀을 겹쳐 덮는다. S1은 밖 번호로 넓힌다. "
            "몰아주기는 복사4+보완1이라 휠 15장을 압축해 보장을 깨뜨린다. 덮기에 휠을 넣으면 S1을 사실상 롤백하는 셈이다.",
            "",
            "추가: 풀 V를 고르는 일이 예측이고, 휠은 그 다음 배치일 뿐이다. Wikipedia/Thaler대로 E[value]는 불변. "
            "V가 틀리면 보장은 ‘발동하지 않은 보장’으로 끝난다.",
            "",
            "## 6) 합의/반박",
            "",
            "| 형 문장 | 커서 |",
            "|---------|------|",
            "| 3등 전용 데이터셋 없음 → 풀+휠로 재해석 | **동의** (데이터 공백은 맞음) |",
            "| 3-covering = 3개 적중 시 3등 보장 | **반박** · 3개 적중 시 **5등 형태**. 3등은 5맞 |",
            "| 2등 확장 4-if-5 / 5-if-6 | **조건부로 동의** · 그건 (v,6,t,m) 로또커버. 장수는 더 큼. 보너스 미지라 2등 확정 불가 |",
            "| 지금 파이프에 끼울 수 있나 | **덮기 함수 교체는 가능**. 3장으로는 완전보장 불가. APPLY는 장수·문장 합의 후 |",
            "",
            "## 7) 하지 말 것",
            "",
            "- 본턴 코드 APPLY · 1237 · 등수P↑ 문장 · 동결 3종 · 3뇌 동시",
            "- S2 consensus 재탕 · 캐시 source 미저장을 HARD 버그로 APPLY",
            "",
            "## 8) 다음 (형 선택)",
            "",
            "A. 문장 고정만 (5등 t=3 vs 3등 t=5) — DOC",
            "B. N≤8 · 4장 covering을 덮기+α에 넣는 SPEC (장수 계약 변경) — 별 GO",
            "C. 3장 greedy t=3 커버율 모니터만 (보장 문구 금지) — S1과 충돌 각오",
            "D. 보류 — 지금 구조 유지",
            "",
        ]
    )


def main() -> int:
    flags = _flags()
    meas = measure()
    lajolla = {
        "7": 4,
        "8": 4,
        "9": 7,
        "10": 10,
        "12": 15,
        "15": "30~31",
        "source": "https://ljcr.dmgordon.org/cover/show_cover.php?v={7,8,10,12,15}&k=6&t=3",
        "C12_proof": "Gordon: C(12,6,3)=15",
    }
    sh3 = {str(v): schonheim(v, 6, 3) for v in (7, 8, 9, 10, 12, 15)}
    sh5 = {str(v): schonheim(v, 6, 5) for v in (7, 8, 10, 12, 15, 18)}
    out = {
        "id": "K-STAT-TIER3-COVERING-DISCUSS",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "read_only": True,
        "code_apply": False,
        "verdict": "DISCUSS_OK",
        "flags": flags,
        "measure": meas,
        "lajolla_C_v_6_3": lajolla,
        "schonheim_C_v_6_3": sh3,
        "schonheim_C_v_6_5": sh5,
        "lajolla_C_v_6_5": {
            "10": 50,
            "source": "https://ljcr.dmgordon.org/cover/show_cover.php?v=10&k=6&t=5",
        },
        "name_collision": {
            "kr_tier3": "5 hits (no bonus)",
            "covering_t3": "every 3-subset in some 6-ticket = 5등 form if those 3 are in draw",
            "user_phrase_3hit_implies_tier3": False,
        },
        "insert_point": "build_cover_r3_sets replace predict_sets resample",
        "deterministic_wheel_bypasses_KE_for_cover_only": True,
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _md(out)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({
        "verdict": out["verdict"],
        "j_shape": meas.get("jaccard_shape_vs_set1_mean"),
        "j_cover": meas.get("jaccard_cover_vs_skill_mean"),
        "union_skill": meas.get("skill_union_mean"),
        "cond3": meas.get("cond_3_in_skill_union"),
        "cond5": meas.get("cond_5_in_skill_union"),
        "C12": 15,
        "C8": 4,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
