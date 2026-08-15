# -*- coding: utf-8 -*-
"""K-STAT-EVOLVE-DIAG-LOG SPEC — READ-ONLY 스키마·트리거 실측. APPLY 없음."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KSTAT_EVOLVE_DIAG_LOG_SPEC.json"
OUT_MD = ROOT / "reports" / "20260815_KSTAT_EVOLVE_DIAG_LOG_SPEC.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _pragma(conn: sqlite3.Connection, table: str) -> list[str]:
    return [str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})")]


def measure() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    ev_cols = _pragma(conn, "testlotto_evolve_log") if "testlotto_evolve_log" in tables else []
    led_cols = _pragma(conn, "testlotto_pool_hit_ledger") if "testlotto_pool_hit_ledger" in tables else []
    ev_n = int(conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log").fetchone()[0]) if ev_cols else 0
    ev_by = {}
    if ev_cols:
        ev_by = {
            str(r["brain_tag"]): int(r["n"])
            for r in conn.execute(
                "SELECT brain_tag, COUNT(*) n FROM testlotto_evolve_log GROUP BY brain_tag"
            )
        }
    led_n = led_by = led_roles = None
    if led_cols:
        led_n = int(conn.execute("SELECT COUNT(*) FROM testlotto_pool_hit_ledger").fetchone()[0])
        led_by = {
            str(r["brain_tag"]): int(r["n"])
            for r in conn.execute(
                "SELECT brain_tag, COUNT(*) n FROM testlotto_pool_hit_ledger GROUP BY brain_tag"
            )
        }
        led_roles = {
            str(r["role"] or ""): int(r["n"])
            for r in conn.execute(
                "SELECT role, COUNT(*) n FROM testlotto_pool_hit_ledger GROUP BY role"
            )
        }
    cache_by = {}
    if "testlotto_pool_view_cache" in tables:
        cache_by = {
            str(r["brain"]): int(r["n"])
            for r in conn.execute(
                "SELECT brain, COUNT(*) n FROM testlotto_pool_view_cache GROUP BY brain"
            )
        }
    dmax = conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0]
    conn.close()

    from app.testlotto.evolve_auto import evolve_auto_enabled
    from app.testlotto.evolve_log import WEIGHT_APPLIED
    from app.testlotto.signal_pool import FEATURE_LAMBDA_WIRE, ROLE_TIER_LEARN_BRAINS

    return {
        "max_draw": int(dmax) if dmax else None,
        "evolve_log_columns": ev_cols,
        "evolve_has_brain_tag": "brain_tag" in ev_cols,
        "evolve_has_brain": "brain" in ev_cols,
        "evolve_n": ev_n,
        "evolve_by_brain": ev_by,
        "ledger_columns": led_cols,
        "ledger_n": led_n,
        "ledger_by_brain": led_by,
        "ledger_by_role": led_roles,
        "cache_by_brain": cache_by,
        "WEIGHT_APPLIED": float(WEIGHT_APPLIED),
        "EVOLVE_AUTO": bool(evolve_auto_enabled()),
        "FEATURE_LAMBDA_WIRE": bool(FEATURE_LAMBDA_WIRE),
        "ROLE_TIER_LEARN_BRAINS": sorted(ROLE_TIER_LEARN_BRAINS),
        "as_of_current_meaning": "build_evolve_row sets as_of=draw_no (채점회차). 형 HARD as_of<draw_no 와 불일치.",
    }


def _md(o: dict[str, Any]) -> str:
    m = o.get("measure") or {}
    return "\n".join(
        [
            "# K-STAT-EVOLVE-DIAG-LOG — SPEC (APPLY 없음)",
            "",
            f"시각: {o['as_of']} · **{o.get('verdict')}** · READ-ONLY · 1237아님 · hits/tier 클레임 금지",
            "목적=매 회차 예측/적중을 정직하게 기록. 성능↑ 아님. χ²·boost귀속 제외.",
            "",
            "## 0) 한 줄 확정",
            "",
            "**뇌 컬럼은 이미 있다 (`brain_tag`). 새 테이블·PK 변경 불필요.** "
            "세트별 필드는 같은 행의 `pool_hits_json`/`repack_hits_json`에 넣고, "
            "원장 `testlotto_pool_hit_ledger`는 이미 세트×뇌 적중을 갖고 있다(이중 SSOT 주의). "
            "쓰기는 **캐시 채점만 · stat만 · `apply_feedback` 호출 금지**. "
            "지금 `as_of=draw_no`는 형 HARD(`as_of < draw_no`)와 **안 맞다** — APPLY 때 `as_of=draw_no-1`로 고친다.",
            "",
            f"실측: evolve 행 **{m.get('evolve_n')}** · ledger **{m.get('ledger_n')}** "
            f"뇌별 `{json.dumps(m.get('ledger_by_brain'), ensure_ascii=False)}` · "
            f"캐시 `{json.dumps(m.get('cache_by_brain'), ensure_ascii=False)}` · "
            f"MAX draws **{m.get('max_draw')}** · EVOLVE_AUTO **{m.get('EVOLVE_AUTO')}** · "
            f"FEATURE_LAMBDA **{m.get('FEATURE_LAMBDA_WIRE')}** · 소비 `{m.get('ROLE_TIER_LEARN_BRAINS')}`",
            "",
            "## 1) brain 컬럼",
            "",
            f"evolve_log 컬럼: `{m.get('evolve_log_columns')}`",
            "",
            "- `brain` 컬럼: **없음**",
            "- `brain_tag` 컬럼: **있음** · PK=`(draw_no, brain_tag)` · 인덱스 `idx_evolve_log_brain`",
            "- 한 회차×한 뇌 = **1행**. 세트는 JSON 배열.",
            "",
            "독립 유지 최소 변경: 컬럼명 `brain`을 새로 만들지 않는다. 형 문서의 brain = 코드 `brain_tag`. "
            "PK를 세트 단위로 쪼개지 않는다(마이그레이션·중복). "
            "markov/review 행 스키마는 그대로 두되 **이번 APPLY 쓰기는 stat만**.",
            "",
            "세트별 기록(형 목록)은 JSON에 넣는다. `_score_sets`에 지금 없는 것: `role`, `tier`. "
            "있으면 됨: `set_no`, `nums`, `hits`, `kind`.",
            "",
            f"이미 세트×뇌 원장: `testlotto_pool_hit_ledger` 컬럼 `{m.get('ledger_columns')}` "
            f"· 역할 `{json.dumps(m.get('ledger_by_role'), ensure_ascii=False)}`. "
            "여기엔 `as_of`가 없다. **신설 금지**이므로 원장을 대체 테이블로 쓰지 않고, "
            "evolve_log JSON을 캠페인 SSOT로 한다. 원장은 기존 L3 유지(이번 SPEC이 다시 쓰지 않음).",
            "",
            "## 2) 트리거 자리",
            "",
            "| 자리 | 예측 변경 | peek | 뇌 독립 | SPEC |",
            "|------|-----------|------|---------|------|",
            "| `click_feedback.apply_draw_result_feedback` 그대로 | **바꿈** (`apply_feedback`·3뇌) | 발권행 사용 | 3뇌 루프+숙제쓰기 | **금지** |",
            "| `coordinator._auto_feedback` 그대로 | **바꿈** (learn) | 캐시 없으면 skip/compute | 3뇌 | **금지** |",
            "| `evolve_auto.score_draw_from_cache` (S2) | 안 바꿈(재예측 없음) | 캐시+actual만 | **3뇌 필수·불완전 시 실패** | **뼈대만 채택** |",
            "| EVOLVE_AUTO=1 | S3 재예측 가능 | 위험 | 3뇌 | **OFF 유지** |",
            "",
            "**확정 자리 (APPLY 때):** 새 함수 `write_evolve_diag_stat(draw_no)` "
            "= S2의 캐시→로그 경로를 **stat만** 복제. "
            "호출=회차 확정 후(클릭/수집 끝) **별도 한 줄**. `apply_feedback` / `write_skill_homework` / "
            "`write_role_homework` / `get_feedback_summary` **호출 금지**. "
            "`allow_compute=False`. 캐시 없으면 SKIP(재생성 없음).",
            "",
            "S2를 그대로 부르면 markov/review 캐시 없을 때 전체가 실패하고, 있으면 3뇌를 써 "
            "‘소비 ON’처럼 보인다. 그래서 복제·stat 필터가 필요하다.",
            "",
            "## 3) as_of < draw_no HARD",
            "",
            "현코드: `build_evolve_row`가 `as_of: int(draw_no)` — **채점 회차와 같음**. "
            "주석도 ‘as_of=draw_no’.",
            "",
            "형 HARD와 맞추는 설계:",
            "1. `as_of = draw_no - 1` (예측 시점 마지막 확정 회). 쓰기 전 `assert as_of < draw_no`.",
            "2. actual은 `lotto_draws`에서 `draw_no=N`만. 없으면 SKIP.",
            "3. 예측 세트는 `pool_view_cache`의 **target=N** 행만. `predict_sets` / `get_or_build` 금지.",
            "4. `_get_draws_before(N)`은 가드 검증용만(max < N). miss_tags 계산에 쓰지 않음(이번 SPEC 제외).",
            "5. 실패 시 INSERT 하지 않음. peek면 HARD FAIL.",
            "",
            "캐시가 N을 만들 때 이미 `_get_draws_before(N)`을 썼다는 전제. "
            "로그 쓰기는 그 산출물을 채점만 한다.",
            "",
            "## 4) 누수 3건 악화 여부",
            "",
            "| 누수 | 이 로그가 악화? | 대안 |",
            "|------|-----------------|------|",
            "| `get_feedback_summary` 3뇌 공유 | **S2 그대로는 안 부름**. `click_feedback`에 붙이면 **악화**(apply_feedback). | 쓰기 함수를 feedback과 분리 |",
            "| skill_homework 3뇌 스냅샷 | click/auto에 붙이면 **악화**(숙제 write). | 숙제 write 호출 금지 |",
            "| 발권 쿼터 혼합 | `lotto_predictions`를 소스로 쓰면 **악화**(혼합 5장). | 소스=캐시 `pool_by_brain[stat]` + `repack_by_brain[stat]`만 |",
            "",
            "읽기: `WHERE brain_tag='stat'`. 3뇌 SUM/평균 뷰 만들지 않음. "
            "`mean_hits`/`best_hits`는 행 안에 있어도 **그 뇌 5장 모니터**. 뇌간 합산 쿼리 금지. "
            "`FEATURE_LAMBDA_WIRE`는 **False 유지**(evolve mean을 예측에 넣지 않음).",
            "",
            "독립 판정: **이 SPEC대로면 누수 3건을 악화하지 않는다.** "
            "click_feedback/_auto_feedback에 그대로 얹으면 악화한다.",
            "",
            "## 5) 함정 3개",
            "",
            "1. **이중 SSOT.** 원장 3000행(stat)이 이미 세트×hits×role×tier. evolve_log를 세트 JSON으로 채우면 같은 숫자가 두 곳에 있다. "
            "어긋나면 어느 쪽이 맞는지 싸운다. APPLY는 evolve만 쓰고 원장은 손대지 말 것.",
            "2. **회차완료=click_feedback 착각.** 그 함수는 학습을 돌린다. 로그 append와 학습을 한 함수에 넣으면 "
            "‘기록만’이 즉시 다음 예측을 바꾼다.",
            "3. **as_of 의미 충돌 + 3뇌 S2.** 옛 독자는 as_of=채점회. 바꾸면 읽기 코드가 깨질 수 있다. "
            "S2는 3뇌 완결을 요구해 stat-only 캐시 창에서 침묵/실패한다.",
            "",
            "## 6) APPLY 때 할 일 / 안 할 일 (형 GO 후)",
            "",
            "할 일:",
            "- `write_evolve_diag_stat(draw_no)` : 캐시 stat만 · as_of=N-1 HARD · role/tier를 hits JSON에 추가",
            "- 확정 경로에서 그 함수만 호출 (learn/숙제/feedback 없이)",
            "- 읽기 API는 brain_tag 필터 필수",
            "",
            "안 할 일:",
            "- 새 테이블 · EVOLVE_AUTO=1 · FEATURE_LAMBDA ON · 3뇌 쓰기 · χ² · boost 귀속",
            "- `random.choices` / `_get_draws_before` / boost 상한 수정",
            "- hits/tier로 게이트·서열",
            "",
            "## 7) 합의",
            "",
            "| 형 | 커서 |",
            "|----|------|",
            "| evolve_log 재사용 · 신설 금지 | **동의** |",
            "| 뇌 컬럼 분리 | **이미 `brain_tag`** · `brain` 추가 불필요 |",
            "| 세트별 기록 | **동의** · JSON (PK 유지) |",
            "| χ²·boost귀속 제외 | **동의** |",
            "| 트리거=회차완료 | **동의하되 click_feedback 본체 금지** · 별 함수 |",
            "| 누수 악화 금지 | **동의** · 위 표 |",
            "",
        ]
    )


def main() -> int:
    meas = measure()
    out = {
        "id": "K-STAT-EVOLVE-DIAG-LOG-SPEC",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "read_only": True,
        "code_apply": False,
        "verdict": "SPEC_OK",
        "independence_ok_if_spec_followed": True,
        "worsens_leaks_if_hooked_on_click_feedback": True,
        "measure": meas,
        "trigger": "write_evolve_diag_stat after draw confirm; not click_feedback body; not EVOLVE_AUTO",
        "as_of_hard": "as_of = draw_no-1; reject unless as_of < draw_no; cache only; no predict",
        "brain_column": "brain_tag (exists). do not add brain.",
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _md(out)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(json.dumps({
        "verdict": out["verdict"],
        "brain_tag": meas.get("evolve_has_brain_tag"),
        "evolve_n": meas.get("evolve_n"),
        "ledger_n": meas.get("ledger_n"),
        "ledger_by": meas.get("ledger_by_brain"),
        "cache_by": meas.get("cache_by_brain"),
        "as_of_issue": True,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
