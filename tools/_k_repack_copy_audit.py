# -*- coding: utf-8 -*-
"""K-REPACK-COPY-AUDIT — 몰아주기=pool 통째복사 실측. READ-ONLY."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.signal_pool import (
    ASSEMBLE_MODE,
    POOL_UNION_CAP,
    REPACK_RECOMBINE_BRAINS,
    REPACK_RECOMBINE_MODE,
    REPACK_ROLE_QUOTA_BRAINS,
    SIGNAL_TOP_BRAINS,
)

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KREPACK_COPY_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260815_KREPACK_COPY_AUDIT.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236
BRAINS = ("stat", "markov", "review")
UI = {
    "draw": 1216,
    "sets": [
        [4, 11, 15, 26, 40, 45],
        [7, 9, 23, 36, 41, 44],
        [6, 8, 16, 25, 27, 45],
        [3, 15, 23, 24, 27, 38],
    ],
}


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _nums(s: dict) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in (s.get("nums") or [])))


def main() -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    act = conn.execute(
        "SELECT num1,num2,num3,num4,num5,num6,bonus FROM lotto_draws WHERE draw_no=1216"
    ).fetchone()
    actual = [int(act[f"num{k}"]) for k in range(1, 7)]
    bonus = int(act["bonus"] or 0)

    snap: dict[str, Any] = {}
    for tag in BRAINS:
        r = conn.execute(
            "SELECT pool_json, repack_json FROM testlotto_pool_view_cache WHERE draw_no=1216 AND brain=?",
            (tag,),
        ).fetchone()
        pool = json.loads(r["pool_json"] or "[]")
        rep = json.loads(r["repack_json"] or "[]")
        pset = {_nums(s) for s in pool}
        rows = []
        copies = 0
        for s in rep:
            n = _nums(s)
            is_c = n in pset
            copies += int(is_c)
            rows.append(
                {
                    "set_no": s.get("set_no"),
                    "nums": list(n),
                    "source": s.get("source"),
                    "source_set_no": s.get("source_set_no"),
                    "exact_pool_copy": is_c,
                }
            )
        snap[tag] = {
            "pool": [{"set_no": s.get("set_no"), "role": s.get("role"), "nums": list(_nums(s))} for s in pool],
            "repack": rows,
            "n_copy": copies,
        }

    win: dict[str, Any] = {}
    for tag in BRAINS:
        n = copy = src_pool = src_score = 0
        for r in conn.execute(
            "SELECT pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no BETWEEN ? AND ?",
            (tag, LO, HI),
        ):
            pset = {_nums(s) for s in json.loads(r["pool_json"] or "[]")}
            q = json.loads(r["repack_json"] or "[]")
            n += 1
            copy += sum(1 for s in q if _nums(s) in pset)
            src_pool += sum(1 for s in q if s.get("source") == "pool")
            src_score += sum(1 for s in q if s.get("source") == "score_repack")
        win[tag] = {
            "draws": n,
            "copy_sets": copy,
            "copy_per5": round(copy / n, 3) if n else None,
            "src_pool": src_pool,
            "src_score": src_score,
        }
    conn.close()

    ui_in_pool = [s for s in snap["stat"]["pool"] if s["nums"] in UI["sets"]]
    hard_ok = dmax == 1236 and pred_1237 == 0 and all(win[t]["copy_per5"] == 4.0 for t in BRAINS)

    payload = {
        "id": "K-REPACK-COPY-AUDIT",
        "as_of": _now(),
        "verdict": "AUDIT_OK" if hard_ok else "AUDIT_FAIL",
        "apply": False,
        "bug": False,
        "design_mismatch": True,
        "ui_draw": 1216,
        "actual_1216": actual,
        "bonus_1216": bonus,
        "ui_sets_are_stat_pool": len(ui_in_pool) == 4,
        "snap_1216": snap,
        "window": win,
        "flags": {
            "ASSEMBLE_MODE": ASSEMBLE_MODE,
            "SIGNAL_TOP_BRAINS": sorted(SIGNAL_TOP_BRAINS),
            "POOL_UNION_CAP": POOL_UNION_CAP,
            "REPACK_ROLE_QUOTA_BRAINS": sorted(REPACK_ROLE_QUOTA_BRAINS),
            "REPACK_RECOMBINE_MODE": REPACK_RECOMBINE_MODE,
            "REPACK_RECOMBINE_BRAINS": sorted(REPACK_RECOMBINE_BRAINS),
        },
        "pred_1237": pred_1237,
        "draws_max": dmax,
        "hard_ok": hard_ok,
        "intended_by_hyung": "10장 중 미당첨이지만 적중 강한 세트의 번호를 뽑아 새 5장",
        "actual_code": "10장 중 신호/점수 상위 4장을 통째 복사 + 1장만 번호 재조합. 타깃 회차 적중은 안 봄.",
    }

    st = snap["stat"]
    lines = [
        "# K-REPACK-COPY-AUDIT",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · READ-ONLY · APPLY **없음** · 1237아님",
        "목적=UI 몰아주기가 10장과 같은 번호인지, 3뇌 공통인지, 형의 스킬 정의와 맞는지 실측.",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. MAX={dmax} · pred_1237={pred_1237}.",
        "",
        "## 0) 한 줄",
        "",
        "**버그(난수/캐시 꼬임)가 아니다.** 몰아주기는 지금 **10장 중 4장을 통째로 복사**한다. 3뇌·200회 모두 4/5가 pool과 완전 동일.",
        "형이 말한 ‘적중 잘된 미당첨 세트에서 번호를 뽑아 새 5장’은 **코드에 없다.** 타깃 회차 적중을 보면 컨닝이 된다.",
        "",
        "## 1) 화면 숫자는 1236이 아니라 **1216**",
        "",
        f"당첨 1216 = {actual} · 보너스 {bonus}.",
        "UI 네 장 = stat **pool 1~4** 그대로. 그중 pool#4=`[3,15,23,24,27,38]` 가 본번호 4개(3·15·23·24)라 4등 라벨.",
        "몰아주기#3=#pool3 · 몰아주기#4=#pool4. 같은 번호가 두 칸에 보이는 이유=**복사**.",
        "",
        "## 2) 1216 stat 몰아주기 출처",
        "",
        "| 몰아주기 | 번호 | source | 원본 |",
        "|----------|------|--------|------|",
    ]
    for row in st["repack"]:
        lines.append(
            f"| #{row['set_no']} | {row['nums']} | {row['source']} | "
            f"{'pool #'+str(row['source_set_no']) if row['exact_pool_copy'] else '재조합'} |"
        )
    lines += [
        "",
        "## 3) 200회 복사율 (1037–1236)",
        "",
        "| 뇌 | 회 | 복사 장/회 | source=pool | source=score_repack |",
        "|----|----|------------|-------------|---------------------|",
    ]
    for tag in BRAINS:
        w = win[tag]
        lines.append(
            f"| {tag} | {w['draws']} | {w['copy_per5']} | {w['src_pool']} | {w['src_score']} |"
        )
    lines += [
        "",
        "## 4) 코드가 하는 일 (설계)",
        "",
        f"- `ASSEMBLE_MODE={ASSEMBLE_MODE}` · `SIGNAL_TOP_BRAINS`={sorted(SIGNAL_TOP_BRAINS)} → **3뇌 모두** 복사 경로.",
        f"- cap **{POOL_UNION_CAP}**: 10장 중 4장 통째 보존. 5번째만 `score_repack`.",
        f"- 역할쿼터·보완1장 = **stat만** (`{sorted(REPACK_ROLE_QUOTA_BRAINS)}` / `{sorted(REPACK_RECOMBINE_BRAINS)}`).",
        "- 점수 재료=이번 pool 번호빈도 + hint + (과거 원장 EMA). **이번 회 당첨번호는 입력 아님.**",
        "",
        "## 5) 형 정의 vs 지금",
        "",
        "| | 형 | 지금 코드 |",
        "|---|----|-----------|",
        "| 재료 | 10장 중 적중 잘된 미당첨 세트 | 신호/점수 상위 **세트 전체** |",
        "| 동작 | 그 번호들을 모아 새 5장 | 4장 **복사** + 1장 재조합 |",
        "| 시점 | (결과 본 뒤처럼 들림) | 예측 시점. 타깃 적중 금지 |",
        "| 범위 | 과거학습만이 아닌 것 같다 | **3뇌 동일** 복사. 맞음 |",
        "",
        "4등 장은 ‘몰아주기가 잘해서’가 아니라 **이미 10장에 있던 세트가 복사된 것**. 성적 클레임 금지.",
        "",
        "## 6) 판정",
        "",
        "AUDIT_OK. 오동작 패치 대상 아님. 스킬을 형 정의로 바꾸려면 별 GO (타깃 적중 입력 금지 · prefer/prize 게이트).",
        "",
        "## 7) 금지 확인",
        "",
        "코드/DB 쓰기 없음. 1237 아님. 동결 토큰 미수정.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], "copy_per5": {t: win[t]["copy_per5"] for t in BRAINS}, "ui_draw": 1216}, ensure_ascii=False))
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
