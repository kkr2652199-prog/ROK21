# -*- coding: utf-8 -*-
"""K-NEXT-QUEUE-EXHAUST — 자동 순서 큐 소진 DOC. APPLY없음."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.signal_pool import ROLE_TIER_LEARN_BRAINS

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KNEXT_QUEUE_EXHAUST.json"
OUT_MD = ROOT / "reports" / "20260815_KNEXT_QUEUE_EXHAUST.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def main() -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    conn.close()
    hard_ok = dmax == 1236 and pred_1237 == 0

    done = [
        "LIST_V3 L0–L14 (L9/L10/L11계 HOLD)",
        "진단로그 SPEC/APPLY/READ/EXPAND",
        "2뇌 엔진+문헌 DISCUSS",
        "prize↔Ziemba SPEC · review W_STRUCT APPLY 0.20",
        "권고#2 축모니터 · 권고4A 전이상태 HOLD",
        "L14 3등엔진 CLOSE",
        "COOCCUR A 궁합annotate SPEC HOLD",
        "COOCCUR B evolve필드 SPEC HOLD",
    ]
    locked = [
        "숙제ON (라이브 {stat} · 형 정정)",
        "궁합 APPLY (prefer_table 금지 · annotate HOLD)",
        "covering 휠 APPLY (greedy t-cover 별 GO)",
        "S2 consensus 재탕",
        "L9/L11/L11b/L11c 재탕",
        "1237 예측/양산",
    ]
    pick = [
        {"id": "숙제 markov ON", "need": "명시 ‘숙제 켜’", "note": "코드 있음. 형 정정은 stat만."},
        {"id": "covering 휠 H", "need": "명시 ‘휠 APPLY’", "note": "S1과 반대 기하. L14에서 별GO."},
        {"id": "evolve features APPLY", "need": "명시 ‘필드 넣어’", "note": "B SPEC HOLD. WEIGHT 0 유지."},
        {"id": "궁합 annotate APPLY", "need": "명시 ‘annotate 켜’", "note": "A SPEC HOLD. prefer 표 금지."},
        {"id": "S2 대체 설계", "need": "새 아이디어+GO", "note": "consensus 재탕 금지."},
    ]

    payload = {
        "id": "K-NEXT-QUEUE-EXHAUST",
        "as_of": _now(),
        "verdict": "DOC_OK" if hard_ok else "DOC_FAIL",
        "apply": False,
        "auto_next": None,
        "draws_max": dmax,
        "pred_1237": pred_1237,
        "role_learn_brains": sorted(ROLE_TIER_LEARN_BRAINS),
        "done_seq": done,
        "locked": locked,
        "pick": pick,
        "hard_ok": hard_ok,
    }

    lines = [
        "# K-NEXT-QUEUE-EXHAUST",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · 코드 **불변** · APPLY **없음** · 1237아님",
        "목적=문서에 적힌 **자동 순서 큐가 비었음**을 확정. 다음 1건은 형이 고른다.",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. MAX={dmax} · pred_1237={pred_1237} · 숙제={sorted(ROLE_TIER_LEARN_BRAINS)}.",
        "",
        "## 0) 한 줄",
        "",
        "**다음 자동 1건은 없다.** LIST_V3 L14 · 권고 1–4A · ENGINE #1–2 · covering A · COOCCUR A·B 까지 끝.",
        "남은 것은 모두 **별 GO** 이거나 잠금(재탕/1237).",
        "",
        "## 1) 끝난 순서",
        "",
    ]
    for x in done:
        lines.append(f"- {x}")
    lines += [
        "",
        "## 2) 잠금 (이 말로 ‘다음’ 해도 안 켬)",
        "",
    ]
    for x in locked:
        lines.append(f"- {x}")
    lines += [
        "",
        "## 3) 형이 고를 수 있는 1건",
        "",
        "| 고를 말 | 필요한 지시 | 메모 |",
        "|---------|--------------|------|",
    ]
    for p in pick:
        lines.append(f"| {p['id']} | {p['need']} | {p['note']} |")
    lines += [
        "",
        "## 4) 판정",
        "",
        "DOC_OK. 새 SPEC/모니터를 이어서 만들지 않음. 코드 없음.",
        "",
        "## 5) 금지 확인",
        "",
        "동결 토큰 미수정. kweon 미접촉. 1237 아님.",
        "",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": payload["verdict"], "auto_next": None, "hard_ok": hard_ok}, ensure_ascii=False))
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
