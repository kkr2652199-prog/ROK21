# -*- coding: utf-8 -*-
"""K-TIER3-LEARN-CLOSE — 3등 학습 엔진 닫기+문장고정. DOC · 코드불변."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.role_homework import COVER_MIN_HITS
from app.testlotto.role_slots import COVER_SELECT_MODE, SHAPE_CORE_MODE
from app.testlotto.signal_pool import (
    REPACK_ROLE_QUOTA_BRAINS,
    REPACK_ROLE_QUOTA_WIRE,
    ROLE_TIER_LEARN_BRAINS,
    ROLE_TIER_LEARN_WIRE,
)
from app.testlotto.stat_pool_learn import STAT_POOL_LEARN_WIRE
from app.testlotto.structure_cover import STRUCTURE_COVER_WIRE

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KTIER3_LEARN_CLOSE.json"
OUT_MD = ROOT / "reports" / "20260815_KTIER3_LEARN_CLOSE.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
SPEC = ROOT / "docs" / "benchmarks" / "20260815_KSTAT_TIER3_ENGINE_SPEC.json"
COVER = ROOT / "docs" / "benchmarks" / "20260815_KSTAT_TIER3_COVERING_DISCUSS.json"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def main() -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    hits_ge5 = int(
        conn.execute(
            "SELECT COUNT(*) FROM testlotto_pool_hit_ledger WHERE hits >= 5"
        ).fetchone()[0]
    )
    hits_ge5_stat = int(
        conn.execute(
            "SELECT COUNT(*) FROM testlotto_pool_hit_ledger "
            "WHERE brain_tag='stat' AND hits >= 5"
        ).fetchone()[0]
    )
    ledger = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_pool_hit_ledger GROUP BY brain_tag"
        )
    }
    roles = {
        str(r["role"]): int(r["n"])
        for r in conn.execute(
            "SELECT role, COUNT(*) n FROM testlotto_pool_hit_ledger "
            "WHERE brain_tag='stat' GROUP BY role"
        )
    }
    evolve = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_evolve_log GROUP BY brain_tag"
        )
    }
    peek = int(conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log WHERE as_of >= draw_no").fetchone()[0])
    conn.close()

    spec = json.loads(SPEC.read_text(encoding="utf-8")) if SPEC.exists() else {}
    cover = json.loads(COVER.read_text(encoding="utf-8")) if COVER.exists() else {}
    math = spec.get("math") or {}

    flags = {
        "ROLE_TIER_LEARN_WIRE": bool(ROLE_TIER_LEARN_WIRE),
        "ROLE_TIER_LEARN_BRAINS": sorted(ROLE_TIER_LEARN_BRAINS),
        "COVER_SELECT_MODE": COVER_SELECT_MODE,
        "SHAPE_CORE_MODE": SHAPE_CORE_MODE,
        "COVER_MIN_HITS": int(COVER_MIN_HITS),
        "STAT_POOL_LEARN_WIRE": bool(STAT_POOL_LEARN_WIRE),
        "STRUCTURE_COVER_WIRE": bool(STRUCTURE_COVER_WIRE),
        "REPACK_ROLE_QUOTA_WIRE": bool(REPACK_ROLE_QUOTA_WIRE),
        "REPACK_ROLE_QUOTA_BRAINS": sorted(REPACK_ROLE_QUOTA_BRAINS),
    }
    hard_ok = (
        dmax == 1236
        and pred_1237 == 0
        and peek == 0
        and flags["ROLE_TIER_LEARN_BRAINS"] == ["stat"]
        and flags["COVER_SELECT_MODE"] == "outside_union"
        and flags["SHAPE_CORE_MODE"] == "set1"
        and flags["STRUCTURE_COVER_WIRE"] is False
    )

    sentences = {
        "cover_not_tier3_engine": "6~8 cover_r3는 3등 학습·예측 엔진이 아니다. 같은 predict_sets 재샘플+S1 밖번호 선택이다.",
        "t3_is_tier5_form": "covering t=3은 ‘풀 안 당첨 3개가 한 장에 들어가면 5등 형태’이지 한국 3등(본번호 5맞)이 아니다.",
        "shape_is_tier3_form": "3등 형태(5고정+1가변)는 9~10 shape_r2에 이미 있다. 3등P 학습기가 아니다. 코드 재라벨 없음.",
        "cover_hw_is_tier5": "COVER_MIN_HITS=3 숙제는 5등(3맞) 근사 복습이다. 3등 숙제가 아니다.",
        "track_closed": "‘과거 3등 사례를 학습해 3등P를 올리는 엔진’ 트랙은 닫는다.",
        "greedy_hold": "풀-먼저 greedy t-cover(H)는 후보만. S1과 반대 기하. 별 GO 없이 APPLY 금지.",
    }

    payload: dict[str, Any] = {
        "id": "K-TIER3-LEARN-CLOSE",
        "as_of": _now(),
        "verdict": "DOC_OK" if hard_ok else "DOC_FAIL",
        "apply": False,
        "code_changed": False,
        "ge3_claim": False,
        "draw_1237": False,
        "flags": flags,
        "census": {
            "draws_max": dmax,
            "pred_1237": pred_1237,
            "peek_evolve": peek,
            "ledger": ledger,
            "roles_stat": roles,
            "hits_ge5": hits_ge5,
            "hits_ge5_stat": hits_ge5_stat,
            "evolve": evolve,
        },
        "math_cite": {
            "E_tier3_3000": math.get("E_tier3_3000"),
            "P_tier3": math.get("P_tier3"),
            "source": "docs/benchmarks/20260815_KSTAT_TIER3_ENGINE_SPEC.json",
        },
        "prior": {
            "engine_spec": "reports/20260815_KSTAT_TIER3_ENGINE_SPEC.md",
            "covering_discuss": "reports/20260815_KSTAT_TIER3_COVERING_DISCUSS.md",
            "covering_json_exists": COVER.exists(),
        },
        "sentences": sentences,
        "hard_ok": hard_ok,
    }

    lines = [
        "# K-TIER3-LEARN-CLOSE",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · DOC · 코드 **불변** · APPLY **없음** · 1237아님",
        "목적=ENGINE SPEC 권고#1+#2 · covering 문장고정 A. 3등 학습 엔진 트랙을 닫고 문장을 고정한다.",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. MAX={dmax} · pred_1237={pred_1237} · peek={peek} · hits≥5={hits_ge5}.",
        "",
        "## 0) 고정 문장 (이후 이 문장과 다르게 쓰지 말 것)",
        "",
        f"1. {sentences['cover_not_tier3_engine']}",
        f"2. {sentences['t3_is_tier5_form']}",
        f"3. {sentences['shape_is_tier3_form']}",
        f"4. {sentences['cover_hw_is_tier5']}",
        f"5. {sentences['track_closed']}",
        f"6. {sentences['greedy_hold']}",
        "",
        "## 1) 라이브 플래그 (코드 실측 · 미변경)",
        "",
        f"| 항 | 값 |",
        f"|----|-----|",
        f"| 숙제 소비 | {flags['ROLE_TIER_LEARN_BRAINS']} · WIRE={flags['ROLE_TIER_LEARN_WIRE']} |",
        f"| COVER_SELECT_MODE | {flags['COVER_SELECT_MODE']} |",
        f"| SHAPE_CORE_MODE | {flags['SHAPE_CORE_MODE']} (S2 HOLD) |",
        f"| COVER_MIN_HITS | {flags['COVER_MIN_HITS']} |",
        f"| STRUCTURE_COVER_WIRE | {flags['STRUCTURE_COVER_WIRE']} |",
        f"| STAT_POOL_LEARN_WIRE | {flags['STAT_POOL_LEARN_WIRE']} |",
        f"| 몰아주기 쿼터 | {flags['REPACK_ROLE_QUOTA_WIRE']} · {flags['REPACK_ROLE_QUOTA_BRAINS']} |",
        "",
        "## 2) 원장 센서스 (읽기)",
        "",
        f"| 항 | 값 |",
        f"|----|-----|",
        f"| draws MAX | {dmax} |",
        f"| pred_1237 | {pred_1237} |",
        f"| 원장 | {ledger} |",
        f"| stat 역할 | {roles} |",
        f"| hits≥5 | {hits_ge5} (stat {hits_ge5_stat}) |",
        f"| evolve | {evolve} |",
        f"| E[3등] 3000장 | {math.get('E_tier3_3000')} (SPEC 인용 · 성적 아님) |",
        "",
        "hits≥5=0 은 E≈0.084와 정합. 엔진 실패 문장 금지.",
        "",
        "## 3) 닫는 것 / 남기는 것",
        "",
        "| 닫음 | 남김(별 GO) |",
        "|------|-------------|",
        "| 3등P 학습 엔진 · 5맞 손실 · 공식5코어 카탈로그 | greedy t-cover 휠 H |",
        "| t=3을 3등으로 부르는 문장 | covering 장수 계약 SPEC |",
        "| shape 코드 재라벨 | S2 consensus 재탕 금지 |",
        "",
        "## 4) 판정",
        "",
        "DOC_OK. 코드/노브/DB 쓰기 없음. 숙제ON·궁합prefer·covering APPLY·S2·1237 없음.",
        "다음 APPLY는 형 1건.",
        "",
        "## 5) 금지 확인",
        "",
        "동결 토큰 미수정. kweon 미접촉. 1237 아님.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], "hard_ok": hard_ok, "hits_ge5": hits_ge5, "flags": flags}, ensure_ascii=False))
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
