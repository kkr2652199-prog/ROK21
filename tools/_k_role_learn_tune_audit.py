# -*- coding: utf-8 -*-
"""K-ROLE-LEARN-TUNE-AUDIT — 6~10 역할·학습경로·뇌별튜닝 필요여부.

READ-ONLY. ge3/등수P 성적클레임 금지. 1237 아님.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260814_KROLE_LEARN_TUNE_AUDIT.json"
OUT_MD = ROOT / "reports" / "20260814_KROLE_LEARN_TUNE_AUDIT.md"
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


def _role_of(kind: str, set_no: int, role_col: str | None) -> str:
    if kind == "repack":
        return "focus_r1"
    if role_col:
        return str(role_col)
    return ROLE_BY_SET.get(int(set_no or 0), "?")


def main() -> int:
    from app.testlotto.models import get_lotto_db, init_testlotto_db
    from app.testlotto.signal_pool import (
        ASSEMBLE_MODE,
        HINT_SPEC_BY_BRAIN,
        POOL_SLOTS_BY_BRAIN,
        POOL_UNION_CAP_BY_BRAIN,
        ROLE_SLOTS_WIRE,
        SCORE_WEIGHTS_BY_BRAIN,
    )
    from app.testlotto.skill_homework import SKILL_HOMEWORK_CONSUME, SKILL_KIND_BY_BRAIN
    from app.testlotto.pool_hit_ledger import LEDGER_TABLE

    init_testlotto_db()
    conn = get_lotto_db()
    try:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({LEDGER_TABLE})").fetchall()]
        has_role = "role" in cols
        sel_role = "role" if has_role else "NULL AS role"
        rows = [
            dict(r)
            for r in conn.execute(
                f"""
                SELECT draw_no, brain_tag, kind, set_no, hits, bonus_hit, tier_rank, {sel_role}
                FROM {LEDGER_TABLE}
                WHERE draw_no BETWEEN ? AND ?
                """,
                (LO, HI),
            ).fetchall()
        ]
        hw_n = conn.execute(
            "SELECT COUNT(1) FROM testlotto_skill_homework"
        ).fetchone()[0]
        review_n = conn.execute(
            "SELECT COUNT(1) FROM testlotto_brain_review"
        ).fetchone()[0]
    finally:
        conn.close()

    # stats: brain x role -> n, sum_hits, ge3, ge4, ge5, r2 (5+bonus), r3 (5 no bonus)
    bucket: dict[tuple[str, str], dict[str, float]] = defaultdict(
        lambda: {
            "n": 0,
            "sum_hits": 0,
            "ge3": 0,
            "ge4": 0,
            "ge5": 0,
            "r2": 0,
            "r3": 0,
            "bonus_hit": 0,
        }
    )
    role_filled = 0
    for r in rows:
        kind = str(r["kind"])
        tag = str(r["brain_tag"])
        sn = int(r["set_no"] or 0)
        role_col = r.get("role")
        if role_col:
            role_filled += 1
        role = _role_of(kind, sn, role_col)
        hits = int(r["hits"] or 0)
        bm = int(r.get("bonus_hit") or 0)
        b = bucket[(tag, role)]
        b["n"] += 1
        b["sum_hits"] += hits
        if hits >= 3:
            b["ge3"] += 1
        if hits >= 4:
            b["ge4"] += 1
        if hits >= 5:
            b["ge5"] += 1
        if hits == 5 and bm:
            b["r2"] += 1
        if hits == 5 and not bm:
            b["r3"] += 1
        if bm:
            b["bonus_hit"] += 1

    table: dict[str, dict[str, dict[str, float]]] = {t: {} for t in BRAINS}
    for (tag, role), b in sorted(bucket.items()):
        n = b["n"] or 1
        table.setdefault(tag, {})[role] = {
            "n": int(b["n"]),
            "mean_hits": round(b["sum_hits"] / n, 4),
            "ge3": int(b["ge3"]),
            "ge4": int(b["ge4"]),
            "ge5": int(b["ge5"]),
            "r2_5plus_bonus": int(b["r2"]),
            "r3_5_no_bonus": int(b["r3"]),
            "bonus_hit_sets": int(b["bonus_hit"]),
        }

    # compare cover vs skill mean (monitor)
    delta: dict[str, dict[str, float]] = {}
    for t in BRAINS:
        sk = table.get(t, {}).get("skill_native") or {}
        cv = table.get(t, {}).get("cover_r3") or {}
        sh = table.get(t, {}).get("shape_r2") or {}
        fo = table.get(t, {}).get("focus_r1") or {}
        delta[t] = {
            "cover_minus_skill_mean": round(
                float(cv.get("mean_hits") or 0) - float(sk.get("mean_hits") or 0), 4
            ),
            "shape_minus_skill_mean": round(
                float(sh.get("mean_hits") or 0) - float(sk.get("mean_hits") or 0), 4
            ),
            "focus_minus_skill_mean": round(
                float(fo.get("mean_hits") or 0) - float(sk.get("mean_hits") or 0), 4
            ),
        }

    payload: dict[str, Any] = {
        "id": "K-ROLE-LEARN-TUNE-AUDIT",
        "as_of": _now(),
        "window": [LO, HI],
        "ge3_claim": False,
        "draw_1237": False,
        "verdict_tune_now": "HOLD_NO_PER_BRAIN_ROLE_SWEEP",
        "knobs": {
            "ASSEMBLE_MODE": ASSEMBLE_MODE,
            "ROLE_SLOTS_WIRE": bool(ROLE_SLOTS_WIRE),
            "HINT_SPEC_BY_BRAIN": {k: list(v) for k, v in HINT_SPEC_BY_BRAIN.items()},
            "SCORE_WEIGHTS_BY_BRAIN": {k: list(v) for k, v in SCORE_WEIGHTS_BY_BRAIN.items()},
            "POOL_SLOTS_BY_BRAIN": dict(POOL_SLOTS_BY_BRAIN),
            "POOL_UNION_CAP_BY_BRAIN": dict(POOL_UNION_CAP_BY_BRAIN),
            "SKILL_KIND_BY_BRAIN": {k: list(v) for k, v in SKILL_KIND_BY_BRAIN.items()},
            "SKILL_HOMEWORK_CONSUME": bool(SKILL_HOMEWORK_CONSUME),
        },
        "n_ledger_rows": len(rows),
        "ledger_role_col_filled": role_filled,
        "skill_homework_rows": int(hw_n),
        "brain_review_rows": int(review_n),
        "by_brain_role": table,
        "mean_delta_vs_skill": delta,
        "prior_gates": {
            "L5_defects": [],
            "L6_L8": "skip",
            "L9_slots_cap": "HOLD",
            "L11_review_shape": "HOLD",
            "L11b_markov_bday": "HOLD",
            "L11c_stat_win1y": "HOLD",
        },
        "structural": {
            "cover_shape_have_own_learner": False,
            "cover_uses_brain_predict_sets": True,
            "shape_uses_skill_set1_morph": True,
            "cover_shape_reread_hint": False,
            "repack_role_aware_select": False,
            "repack_selects_by": "pos_ema_set_no + set_score, cap4",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def role_row(tag: str, role: str) -> str:
        d = (table.get(tag) or {}).get(role) or {}
        if not d:
            return f"| {tag} | {role} | — | — | — | — | — | — |"
        return (
            f"| {tag} | {role} | {d['n']} | {d['mean_hits']} | "
            f"{d['ge3']} | {d['ge4']} | {d['ge5']} | "
            f"{d['r3_5_no_bonus']}/{d['r2_5plus_bonus']} |"
        )

    rows_md = "\n".join(
        role_row(t, r)
        for t in BRAINS
        for r in ("skill_native", "cover_r3", "shape_r2", "focus_r1")
    )
    dlt = "\n".join(
        f"| {t} | {delta[t]['cover_minus_skill_mean']} | "
        f"{delta[t]['shape_minus_skill_mean']} | {delta[t]['focus_minus_skill_mean']} |"
        for t in BRAINS
    )

    md = f"""# K-ROLE-LEARN-TUNE-AUDIT — 6~10 학습·뇌별튜닝

시각: {payload['as_of']} · 창 {LO}~{HI} · **판정={payload['verdict_tune_now']}** · ge3미클레임 · 1237아님

## 0) 한 줄 (형 질문에 대한 답)

**6~10번은 ‘3등 엔진 / 2등 엔진’이 따로 학습하는 세트가 아니다.**  
각 뇌의 **1~5번 예측을 재료로** 만든 포트폴리오 역할이다.  
몰아주기는 **1등 지향 압축기**이지, 6~10을 등수별로 다시 학습하지 않는다.

**지금 뇌별 세부 튜닝 스윕은 필요 없다 (HOLD).**  
스킬축 잔여 노브는 이미 L11~L11c HOLD, 몰아주기 slots/cap은 L9 HOLD, L5 결함 0으로 L6~L8 스킵된 상태다.

등수 횟수(아래 표 ge3/ge4/ge5)는 **모니터만**. 3등·2등이 더 잘된다고 쓰지 않는다.

## 1) 10세트 + 몰아주기 — 실제로 무엇이 도나

| 칸 | 역할 | 만드는 법 | 자체 학습기 |
|----|------|-----------|-------------|
| 1~5 | skill_native | 그 뇌 `predict_sets` 그대로 | **있음** (뇌 스킬+learn_boost+숙제) |
| 6~8 | cover_r3 | 같은 뇌 `predict_sets`를 **다른 시드**로 한 번 더 돌리고, 1~5와 겹침(Jaccard) **낮은** 3장 | **없음** |
| 9~10 | shape_r2 | 그 뇌 **1번 세트**에서 번호 1개 빼고 다른 1개 넣음 (보너스 입력 금지) | **없음** |
| 몰아주기 1~5 | focus_r1 | 10장 중 신호·점수 상위 **4장 통째 복사** + 1장 재조합 | 원장(ledger) 위치/번호 신호 · EMA는 보조 |

코드: `role_slots.py` · `signal_pool.assemble_signal_union` · `ledger_signal_tables`.

## 2) 각 뇌 엔진이 배우는 것 (1~5번에만 직접 들어감)

| 뇌 | 아이디어(스킬축) | 숙제 저장 | 예측 때 쓰는 법 | 공통 learn_boost |
|----|------------------|-----------|-----------------|------------------|
| 과거학습 stat | 안 나온 패턴 `miss_pattern` 창 52주 | `testlotto_skill_homework` | hint 가중 **0.15** · SCORE (freq/learn 쪽) | overdue/ending/carry (상한 동결) |
| 선호번호 markov | 사람들이 많이 고르는 쪽 `crowd_prefer` | 동 테이블 | hint **0.65** · BLEND **0.55** · W_CROWD **0.90** | 동 + pair |
| 복습·몫 review | 덜 인기·당첨자 적은 쪽 `crowd_prize` | 동 테이블 | hint **0.65** · BLEND **0.85** · W_CROWD **0.90** | learn_state 로드(가중 재탕 아님) |

실측 행 수(본 DB): 숙제 **{int(hw_n)}** · 복습미러 **{int(review_n)}**.  
숙제 읽기: `as_of < target` only (컨닝 아님).  
몰아주기도 뇌별 hint를 다시 보지만, **고르는 대상은 이미 만들어진 10장**이다.

**6~8, 9~10은 hint를 다시 읽지 않는다.**  
뇌 특성은 “그 뇌가 만든 1~5장(과 cover용 재호출 5장)” 안에만 들어 있다.  
커버 고르는 기준은 세 뇌 모두 **같은 Jaccard 최저**, 형상은 세 뇌 모두 **1번 세트 변형**.

L5 실측 커버 vs 스킬 최소 Jaccard: stat **0.0** / markov **0.0014** / review **0.0219** (역할이 겹침을 낮춘다는 구조 확인 · 등수 아님).

## 3) 3등·2등 ‘학습’은 어디에 있나

| 기대(형 표현) | 코드 실측 |
|---------------|-----------|
| 6~8이 3등을 학습 | **안 함.** 겹침↓ 포트폴리오. P(3등)↑ 게이트 **금지**(LIST_V3 PASS) |
| 9~10이 2등을 학습 | **안 함.** ‘5개+빈칸1’ 형태만. 보너스 번호 입력 **금지** |
| 몰아주기가 1등을 학습 | **압축만.** 원장에서 맞은 번호·칸 신호를 다음 회차 **고를 때** 씀. 6맞 목적함수 없음 |
| 칸 번호 6~10 성적 | `ledger` → 위치 EMA. **역할 이름이 아니라 칸 번호**를 기억함 |

그래서 홈에서 3등이 6~8번이 아니라 **3번(skill)** 에서 나온 것(1210)과 모순이 아니다. 3등 칸이 3등을 맞히도록 학습하지 않는다.

## 4) 200회 원장 모니터 (성적 클레임 아님)

ledger 행 {len(rows)} · role컬럼 채워진 행 {role_filled} · 빈 칸은 set_no로 역할 매핑.

| 뇌 | 역할 | 장수 | 장당 mean hits | hits≥3 | ≥4 | ≥5 | 3등/2등(5맞) |
|----|------|------|----------------|--------|----|----|--------------|
{rows_md}

skill 대비 mean 차이 (양수=그 역할이 skill보다 장당 적중 많음 · **게이트 아님**):

| 뇌 | cover−skill | shape−skill | 몰아주기−skill |
|----|-------------|-------------|----------------|
{dlt}

이론 장당 적중 ≈ **0.80**. 이 표가 0.80 근처면 역할이 ‘상위등수 엔진’이 아니라는 뜻과 맞다.

## 5) 몰아주기(1등 지향)와 6~10의 충돌

이미 측정됨 (`20260814_KREPACK_COPY_WHICH_SET`):
- 매 회차 정확히 **4장 복사 + 1장 재조합**
- 복사 많은 칸: **1 · 9 · 10** (skill 첫장 + 그 변형)
- 복사 적은 칸: **6~8 커버**

이유: 몰아주기는 역할을 안 보고 **칸 신호 + 번호 점수**만 본다. 커버는 일부러 안 겹치게 만들어서 점수가 낮다.

이건 버그가 아니라, 「몰아주기=1등 압축」과 「커버=분산」이 **한 선택기에서 동시에 이기기 어려운** 구조다.  
L9 slots/cap 스윕은 신호 없어 **HOLD**(2/4 유지).

## 6) 뇌별 세부 튜닝이 필요한가

| 층 | 지금 | 이유 |
|----|------|------|
| 1~5 스킬 노브 | **추가 스윕 불필요** | L11 review shape HOLD · L11b 생일대 HOLD · L11c WIN_1Y HOLD · L5 결함 0 |
| 6~10을 뇌마다 다른 세기로 | **지금 스윕 금지에 가깝다** | 등수P 게이트 PASS · 자체 학습기 없음 · 레시피가 3뇌 동일 |
| 몰아주기 slots/cap | **불변 유지** | L9 HOLD |
| 구조 선택(튜닝 아님) | 형 결정 1건 | 예: 몰아주기가 역할을 보고 커버 1장을 남길지 / 화면 중복합치기 / 유지 |

**권고:** 세부 숫자 튜닝보다, 형이 원하는 그림이 아래 중 무엇인지 한 줄로 정하는 쪽이 먼저다.

1. **유지** — 6~10은 재료 변형, 몰아주기는 점수 압축 (현재)
2. **역할 보존 몰아주기** — 1등 압축이어도 커버 1장은 남김 (새 설계 · L9와 별건 · 게이트=prefer/prize)
3. **6~10을 진짜 등수 엔진으로** — **비권고** (문헌·K-P·no_bonus_peek와 충돌)

## 7) 하지 않은 것

- 6~10 뇌별 노브 APPLY
- ge3/prize-P 클레임
- 1237 양산
"""
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({
        "verdict": payload["verdict_tune_now"],
        "mean_delta_vs_skill": delta,
        "n_ledger": len(rows),
        "role_filled": role_filled,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
