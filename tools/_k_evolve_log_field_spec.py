# -*- coding: utf-8 -*-
"""K-EVOLVE-LOG-FIELD-SPEC — COOCCUR B. features_json 확장 SPEC. APPLY없음."""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.evolve_auto import evolve_auto_enabled
from app.testlotto.evolve_log import WEIGHT_APPLIED
from app.testlotto.signal_pool import FEATURE_LAMBDA_WIRE, ROLE_TIER_LEARN_BRAINS

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KEVOLVE_LOG_FIELD_SPEC.json"
OUT_MD = ROOT / "reports" / "20260815_KEVOLVE_LOG_FIELD_SPEC.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
ROLL = 52


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def main() -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )
    peek = int(conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log WHERE as_of >= draw_no").fetchone()[0])
    evolve = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_evolve_log GROUP BY brain_tag"
        )
    }
    w_n = int(conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log").fetchone()[0])
    w_nz = int(
        conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log WHERE weight_applied != 0").fetchone()[0]
    )
    w_asof = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_evolve_log "
            "WHERE as_of != draw_no - 1 GROUP BY brain_tag"
        )
    }
    keys = Counter()
    sample_feat: dict[str, Any] | None = None
    for r in conn.execute(
        "SELECT features_json FROM testlotto_evolve_log WHERE brain_tag='stat' LIMIT 20"
    ):
        feat = json.loads(r["features_json"] or "{}")
        if sample_feat is None:
            sample_feat = feat
        for k in feat:
            keys[k] += 1
    cols = [str(r[1]) for r in conn.execute("PRAGMA table_info(testlotto_evolve_log)")]
    conn.close()

    proposed = {
        "roll52_chi2": "직전 52회 당첨번호 빈도 vs 균일 χ². 모니터만. APPLY 게이트 금지.",
        "roll52_n": "창 길이(기본 52). 부족하면 그 길이.",
        "repack_mean_consec": "repack5 연번쌍 평균. 세트 속성.",
        "repack_mean_hi32": "repack5 고번호(≥32) 평균. prize 축 모니터.",
        "repack_mean_prefer": "repack5 set_crowd_score(prefer_table). markov 축 모니터.",
        "repack_mean_prize": "repack5 set_crowd_score(prize_table). review 축 모니터.",
    }
    hard_ok = (
        dmax == 1236
        and pred_1237 == 0
        and peek == 0
        and w_nz == 0
        and evolve.get("stat") == 200
        and evolve.get("markov") == 200
        and evolve.get("review") == 200
        and not w_asof
        and FEATURE_LAMBDA_WIRE is False
        and evolve_auto_enabled() is False
        and abs(float(WEIGHT_APPLIED)) < 1e-12
    )

    payload = {
        "id": "K-EVOLVE-LOG-FIELD-SPEC",
        "as_of": _now(),
        "verdict": "SPEC_OK" if hard_ok else "SPEC_FAIL",
        "apply": False,
        "recommend": "HOLD",
        "ge3_claim": False,
        "draw_1237": False,
        "hard_ok": hard_ok,
        "census": {
            "draws_max": dmax,
            "pred_1237": pred_1237,
            "peek": peek,
            "evolve": evolve,
            "weight_n": w_n,
            "weight_nonzero": w_nz,
            "as_of_not_n_minus_1": w_asof,
            "columns": cols,
            "features_keys_now": dict(keys),
            "sample_features": sample_feat,
        },
        "live": {
            "WEIGHT_APPLIED": WEIGHT_APPLIED,
            "FEATURE_LAMBDA_WIRE": FEATURE_LAMBDA_WIRE,
            "EVOLVE_AUTO": evolve_auto_enabled(),
            "ROLE_TIER_LEARN_BRAINS": sorted(ROLE_TIER_LEARN_BRAINS),
        },
        "spec": {
            "new_table": False,
            "alter_table": False,
            "pk": "(draw_no, brain_tag)",
            "write_into": "features_json only",
            "writer": "write_evolve_diag(brain) only · click_feedback 본체 금지",
            "as_of": "N-1",
            "weight_applied": 0.0,
            "roll_window": ROLL,
            "proposed_keys": proposed,
            "chi2_is": "모니터. APPLY 게이트 아님. FEATURE_LAMBDA 입력 아님.",
            "forbid": [
                "새 테이블",
                "회차 6개 χ²",
                "EVOLVE_AUTO=1",
                "FEATURE_LAMBDA_WIRE=True",
                "weight_applied≠0",
                "mean_hits를 예측 입력",
                "궁합 prefer_table 반영",
            ],
        },
        "reason": (
            "이미 있는 features_json에 롤링 모니터 키만 추가하면 된다. 새 파이프 불필요. "
            "이번 턴은 SPEC만. 키를 넣으면 쓰기 경로가 바뀌므로 APPLY는 별 GO."
        ),
    }

    lines = [
        "# K-EVOLVE-LOG-FIELD-SPEC",
        "",
        f"시각: {payload['as_of']} · **{payload['verdict']}** · READ-ONLY · APPLY **없음** · 1237아님",
        "목적=COOCCUR 다음 B. evolve_log **필드 확장 SPEC**. 롤링 χ² 모니터. WEIGHT 0 유지. 새 테이블 없음.",
        "",
        f"권고=**HOLD**. {payload['reason']}",
        "",
        f"HARD={'통과' if hard_ok else '실패'}. peek={peek} · weight≠0={w_nz} · pred_1237={pred_1237} · MAX={dmax}.",
        "",
        "## 0) 지금 있는 것 (실측)",
        "",
        f"| 항 | 값 |",
        f"|----|-----|",
        f"| PK | (draw_no, brain_tag) |",
        f"| 행 | {evolve} |",
        f"| as_of | 전부 N-1 (어긋남 {w_asof or 0}) |",
        f"| weight_applied≠0 | {w_nz} / {w_n} |",
        f"| WEIGHT_APPLIED 코드 | {WEIGHT_APPLIED} |",
        f"| FEATURE_LAMBDA_WIRE | {FEATURE_LAMBDA_WIRE} |",
        f"| EVOLVE_AUTO | {evolve_auto_enabled()} |",
        f"| 지금 features 키 | {sorted(keys)} |",
        f"| 컬럼 수 | {len(cols)} (ALTER 없음) |",
        "",
        "지금 `write_evolve_diag` features = `weight_applied, n_repack, n_pool, has_apply_learn_boost`.",
        "구 `evolve_log` 경로의 repack_avg_* 는 진단 일반화 경로에 **안 들어감**.",
        "",
        "## 1) SPEC (코드에 아직 없음)",
        "",
        "- 새 테이블 **금지**. ALTER **금지**. `features_json` 키만 추가.",
        "- 쓰기=`write_evolve_diag(brain)` 만. `click_feedback` 본체 금지.",
        "- `weight_applied` **0.0** 유지. `FEATURE_LAMBDA_WIRE` **False**. `EVOLVE_AUTO` **OFF**.",
        f"- 롤링 창 **{ROLL}회** 당첨번호 빈도 vs 균일 χ² → `roll52_chi2` (당첨공 모니터. 사면분포 아님).",
        "- 세트 모니터: `repack_mean_consec` · `repack_mean_hi32` · `repack_mean_prefer` · `repack_mean_prize`.",
        "- prefer/prize 점수는 **기록만**. `prefer_table` 수정·궁합 APPLY 아님.",
        "- χ²를 APPLY 게이트로 쓰지 않음. mean_hits를 예측 입력으로 쓰지 않음.",
        "",
        "| 키 | 의미 |",
        "|----|------|",
    ]
    for k, v in proposed.items():
        lines.append(f"| `{k}` | {v} |")
    lines += [
        "",
        "## 2) 왜 APPLY 안 하나",
        "",
        "- 키를 넣는 순간 쓰기 경로가 바뀐다. 이번은 SPEC.",
        "- 회차 6개 χ²는 무의미(DISCUSS 반박). 롤링도 공정성 감시이지 예측 입력이 아님.",
        "- 새 테이블을 만들면 `backtest_runs=0` 같은 SOFT 공백이 하나 더 생긴다.",
        "",
        "## 3) 판정",
        "",
        "SPEC_OK · HOLD. 코드/DB 쓰기 없음. 숙제ON·궁합 APPLY·covering휠·S2·1237 없음.",
        "다음 APPLY는 형 1건.",
        "",
        "## 4) 금지 확인",
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
    print(
        json.dumps(
            {
                "verdict": payload["verdict"],
                "hard_ok": hard_ok,
                "keys": sorted(keys),
                "weight_nz": w_nz,
                "lambda": FEATURE_LAMBDA_WIRE,
                "auto": evolve_auto_enabled(),
            },
            ensure_ascii=False,
        )
    )
    return 0 if hard_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
