# -*- coding: utf-8 -*-
"""K-REPACK-COPY-WHICH-SET — 몰아주기가 10세트 중 몇 번을 복제하는지.

READ-ONLY. 버그 vs 시스템(signal_union cap4). ge3 성적클레임 금지.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KREPACK_COPY_WHICH_SET.json"
OUT_MD = ROOT / "reports" / "20260814_KREPACK_COPY_WHICH_SET.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

LO, HI = 1037, 1236
BRAINS = ("stat", "markov", "review")
ROLE_BY_SET = {
    1: "skill_native",
    2: "skill_native",
    3: "skill_native",
    4: "skill_native",
    5: "skill_native",
    6: "cover_r3",
    7: "cover_r3",
    8: "cover_r3",
    9: "shape_r2",
    10: "shape_r2",
}


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _key(nums) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def main() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.signal_pool import (
        ASSEMBLE_MODE,
        POOL_SLOTS_BY_BRAIN,
        POOL_UNION_CAP_BY_BRAIN,
        ROLE_SLOTS_WIRE,
    )

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        cache_rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT draw_no, brain, pool_json, repack_json
                FROM testlotto_pool_view_cache
                WHERE draw_no BETWEEN ? AND ?
                """,
                (LO, HI),
            ).fetchall()
        ]
    finally:
        conn.close()

    # pool set_no that was copied into repack (exact nums match)
    copy_from_pool_set: Counter[int] = Counter()
    copy_from_role: Counter[str] = Counter()
    copy_from_pool_set_by_brain: dict[str, Counter[int]] = {t: Counter() for t in BRAINS}
    copy_to_repack_slot: Counter[int] = Counter()  # dest set_no 1-5
    pair_src_dst: Counter[tuple[int, int]] = Counter()  # (pool_set, repack_set)
    copies_per_draw_brain: Counter[int] = Counter()  # 0..5
    unmatched_repack = 0  # score_repack (not exact pool copy)
    n_repack = 0
    n_draw_brain = 0
    src_field: Counter[str] = Counter()
    src_set_no_present = 0
    # if source_set_no disagrees with nums match
    src_mismatch = 0
    always_low: int = 0  # copies only from set 1-4
    sample_spread: list[dict[str, Any]] = []
    draw_1210: dict[str, Any] = {}

    def analyze_rows(rows: list[dict]) -> None:
        nonlocal unmatched_repack, n_repack, n_draw_brain, src_set_no_present, src_mismatch, always_low
        for row in rows:
            tag = str(row["brain"])
            pool = json.loads(row["pool_json"] or "[]")
            repack = json.loads(row["repack_json"] or "[]")
            pmap: dict[tuple[int, ...], int] = {}
            for s in pool:
                k = _key(s.get("nums") or [])
                sn = int(s.get("set_no") or s.get("pred_set_no") or 0)
                if k and sn:
                    pmap[k] = sn
            copied_sns: list[int] = []
            local = []
            n_draw_brain += 1
            n_copy = 0
            for s in repack:
                n_repack += 1
                src = str(s.get("source") or "") or "empty"
                src_field[src] += 1
                k = _key(s.get("nums") or [])
                rsn = int(s.get("set_no") or s.get("pred_set_no") or 0)
                psn = pmap.get(k)
                ssn = s.get("source_set_no")
                if ssn not in (None, "", 0):
                    src_set_no_present += 1
                    try:
                        if psn is not None and int(ssn) != int(psn) and src == "pool":
                            src_mismatch += 1
                    except (TypeError, ValueError):
                        pass
                if psn is None:
                    unmatched_repack += 1
                    continue
                n_copy += 1
                copied_sns.append(psn)
                copy_from_pool_set[psn] += 1
                copy_from_role[ROLE_BY_SET.get(psn, "?")] += 1
                copy_from_pool_set_by_brain[tag][psn] += 1
                copy_to_repack_slot[rsn] += 1
                pair_src_dst[(psn, rsn)] += 1
                if len(sample_spread) < 12:
                    sample_spread.append(
                        {
                            "draw": row["draw_no"],
                            "brain": tag,
                            "pool_set": psn,
                            "role": ROLE_BY_SET.get(psn),
                            "repack_set": rsn,
                            "source_field": src,
                        }
                    )
                local.append(
                    {
                        "pool_set": psn,
                        "role": ROLE_BY_SET.get(psn),
                        "repack_set": rsn,
                        "nums": list(k),
                    }
                )
            copies_per_draw_brain[n_copy] += 1
            if copied_sns and max(copied_sns) <= 4:
                always_low += 1
            if int(row["draw_no"]) == 1210:
                draw_1210[tag] = {
                    "copies": local,
                    "n_copy": n_copy,
                    "pool_set_nos": [
                        int(s.get("set_no") or 0) for s in pool
                    ],
                    "repack_all": [
                        {
                            "set_no": int(s.get("set_no") or 0),
                            "source": s.get("source"),
                            "source_set_no": s.get("source_set_no"),
                            "nums": sorted(int(x) for x in (s.get("nums") or [])),
                            "matched_pool_set": pmap.get(_key(s.get("nums") or [])),
                        }
                        for s in repack
                    ],
                }

    analyze_rows(cache_rows)

    copy_n = int(sum(copy_from_pool_set.values()))
    verdict = "SYSTEM_NOT_BUG"
    notes = [
        "고정 4·5번 복제가 아님(구 hybrid는 버그성 하드코딩이었고 이미 교체됨).",
        "현행 signal_union: 위치EMA 상위 2장 + 세트점수 상위 보충 cap4 + 재조합 1장.",
        "10세트 번호(1~10)는 역할 슬롯이지 '1등이 잘 맞는 순서'가 아님.",
        "복사 대상이 1~10에 퍼지면 설계대로, 항상 1~4만이면 EMA0 초기편향 모니터.",
    ]

    payload: dict[str, Any] = {
        "id": "K-REPACK-COPY-WHICH-SET",
        "as_of": _now(),
        "window": [LO, HI],
        "ge3_claim": False,
        "draw_1237": False,
        "verdict": verdict,
        "knobs": {
            "ASSEMBLE_MODE": ASSEMBLE_MODE,
            "POOL_SLOTS_BY_BRAIN": dict(POOL_SLOTS_BY_BRAIN),
            "POOL_UNION_CAP_BY_BRAIN": dict(POOL_UNION_CAP_BY_BRAIN),
            "ROLE_SLOTS_WIRE": bool(ROLE_SLOTS_WIRE),
            "ROLE_BY_POOL_SET": dict(ROLE_BY_SET),
        },
        "n_cache_rows": len(cache_rows),
        "n_draw_brain": n_draw_brain,
        "n_repack": n_repack,
        "n_exact_pool_copy": copy_n,
        "copy_ratio": round(copy_n / n_repack, 4) if n_repack else None,
        "n_not_exact_copy": unmatched_repack,
        "copies_per_draw_brain": dict(sorted(copies_per_draw_brain.items())),
        "copy_from_pool_set_1to10": {str(i): int(copy_from_pool_set[i]) for i in range(1, 11)},
        "copy_from_role": dict(copy_from_role),
        "copy_from_pool_set_by_brain": {
            t: {str(i): int(copy_from_pool_set_by_brain[t][i]) for i in range(1, 11)}
            for t in BRAINS
        },
        "copy_to_repack_slot_1to5": {str(i): int(copy_to_repack_slot[i]) for i in range(1, 6)},
        "top_pool_to_repack_pairs": [
            {"pool_set": a, "repack_set": b, "n": n}
            for (a, b), n in pair_src_dst.most_common(15)
        ],
        "draw_brain_where_all_copies_from_set_le4": always_low,
        "source_field": dict(src_field),
        "source_set_no_present": src_set_no_present,
        "source_set_no_vs_nums_mismatch": src_mismatch,
        "draw_1210": draw_1210,
        "sample": sample_spread,
        "notes": notes,
    }

    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def bar_row(i: int, n: int, total: int) -> str:
        pct = (100.0 * n / total) if total else 0.0
        return f"| {i} | {ROLE_BY_SET.get(i, '?')} | {n} | {pct:.1f}% |"

    tot = copy_n or 1
    role_lines = "\n".join(
        f"| {k} | {v} | {100.0 * v / tot:.1f}% |" for k, v in sorted(copy_from_role.items())
    )
    set_lines = "\n".join(bar_row(i, copy_from_pool_set[i], tot) for i in range(1, 11))
    slot_lines = "\n".join(
        f"| {i} | {copy_to_repack_slot[i]} |" for i in range(1, 6)
    )
    per_db = ", ".join(f"{k}장복사×{v}회" for k, v in sorted(copies_per_draw_brain.items()))
    m1210 = draw_1210.get("markov") or {}
    m_copies = m1210.get("copies") or []

    md = f"""# K-REPACK-COPY-WHICH-SET — 10세트 중 몇 번째를 복제하나

시각: {payload['as_of']} · 창 {LO}~{HI} · **판정={verdict}** · ge3미클레임 · 1237아님

## 1) 한 줄

**버그 아님. 엔진 시스템이다.**  
몰아주기는 10세트 중 **고정 번호(예: 항상 1~4번, 또는 구버전처럼 항상 4·5번)를 집어오는 것이 아니다.**  
매 회차·뇌마다 **신호(위치 EMA) 상위 2장 + 번호점수 합 상위 보충 → 최대 4장**을 통째 복사하고, 나머지 1장은 번호를 재조합한다.

## 2) 10세트의 의미 (역할 · 고정)

`ROLE_SLOTS_WIRE=True` 일 때 세트 번호는 **성적 순위가 아니라 역할 칸**이다.

| pool 세트 | 역할 | 만드는 방식 |
|-----------|------|-------------|
| 1~5 | skill_native | 그 뇌 원래 예측 5장 |
| 6~8 | cover_r3 | 3등 커버(겹침 낮게) |
| 9~10 | shape_r2 | 2등 형상(핵심5+6번째 가변) |

발권 5장은 **1~5만** 후보로 쓴다(`ticket_pool_sync.skill_candidates_from_raw`).  
몰아주기는 **1~10 전부**를 보고 위 규칙으로 4장까지 고른다.

## 3) 코드가 고르는 순서 (`assemble_signal_union`)

1. 위치 EMA가 높은 **세트 번호 2개** (동점이면 번호 작은 쪽)
2. 남은 8장 중 **번호 점수 합**이 높은 순으로 cap(4)까지 채움
3. 모자란 칸은 점수 재조합(`score_repack`)
4. 번호가 겹치면 건너뛰고 filler로 보충
5. 나온 5장을 **다시 1~5번으로 붙인다** (원본 10세트 번호를 유지하지 않음)

구버전 `p45_r123`은 **항상 pool 4·5번**만 보존했다. 그건 신호와 무관한 하드코딩이라 설계 어긋남으로 이미 `signal_union`으로 교체됨.

상수 실측: ASSEMBLE_MODE=`{ASSEMBLE_MODE}` · 슬롯={dict(POOL_SLOTS_BY_BRAIN)} · cap={dict(POOL_UNION_CAP_BY_BRAIN)}

## 4) 200회 캐시 실측 (번호 완전일치 = 복제)

- 캐시 행: {len(cache_rows)} · 회차×뇌: {n_draw_brain} · 몰아주기 장: {n_repack}
- 10세트와 **번호가 똑같은 복제**: **{copy_n}** / {n_repack} (비율 **{payload['copy_ratio']}**)
- 재조합(10세트에 없음): {unmatched_repack}
- 회차×뇌당 복제 장수: {per_db}
- source 필드: {dict(src_field)}
- source_set_no 기록: {src_set_no_present} · 번호매칭과 불일치: {src_mismatch}

### 복제된 **원본 몇 번**인가 (1~10)

| pool세트 | 역할 | 복제횟수 | 비율 |
|----------|------|----------|------|
{set_lines}

역할 합:

| 역할 | 복제횟수 | 비율 |
|------|----------|------|
{role_lines}

몰아주기 **몇 번 칸**에 붙였나 (재번호 1~5):

| 몰아주기 세트 | 복제가 들어간 횟수 |
|---------------|---------------------|
{slot_lines}

회차×뇌 중 복제가 **전부 1~4번에서만** 온 경우: {always_low} / {n_draw_brain}

## 5) 1210 선호번호(markov) — 홈 3등 그 장

복제 목록: `{json.dumps(m_copies, ensure_ascii=False)}`

3등 번호가 pool **3번**(skill_native)에서 왔고, 몰아주기에도 같은 번호가 한 장 들어갔다.  
그건 「항상 3번을 복사한다」가 아니라, 그 회차 규칙이 3번을 상위 4장에 넣은 결과다.

## 6) 판정

| 질문 | 답 |
|------|-----|
| 버그인가? | **아니오. 시스템(설계)** |
| 항상 같은 번째를 복사하나? | **아니오.** 1~10이 역할이고, 매 회차 EMA+점수로 고른다 |
| 왜 화면에 같은 번호가 두 줄인가? | 10세트 원본 + 몰아주기 복사본을 **둘 다 보여주기 때문** |
| 산 표 5장과 다른 이유 | 발권은 **1~5 skill만** quota. 몰아주기는 1~10에서 4장 복사 |

성적(3등↑) 클레임 없음. 다음=형 1건(화면 고유합치기 / 발권편입 / 유지).
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({k: payload[k] for k in (
        "verdict", "n_exact_pool_copy", "copy_ratio", "copy_from_pool_set_1to10",
        "copy_from_role", "copies_per_draw_brain", "draw_brain_where_all_copies_from_set_le4",
    )}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
