# -*- coding: utf-8 -*-
"""K-PREDICT-RESET — 테스트로또 DB 의 **3뇌 예측 산출물만** 삭제.

형 지시 (20260808): 「로또테스트에 백테스트한 모든 db 에 잇는 3뇌 예측을 삭제」
대상 DB = `data/lotto_testlotto.db` 단독 · 백업 없음.

삭제 대상 판정 기준 (추측 금지)
  · `brain_tag` / `brain` 컬럼을 가진 테이블 = 뇌별 산출물
  · 뇌 태그가 없어도 **예측·백테스트 산출물**로 명시된 테이블
회차·당첨정보처럼 **재수집해야 하는 원천 데이터는 건드리지 않는다.**
회차에서 기계적으로 파생되는 기록(이행로그·rare 적중)도 3뇌 예측이 아니므로 남긴다.

Usage
  python tools/_k_predict_reset.py              # 예정 내역만 출력 (삭제 안 함)
  K_RESET_APPLY=1 python tools/_k_predict_reset.py   # 실제 삭제
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

RESET_ID = "K-PREDICT-RESET"
OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KPREDICT_RESET.json"
OUT_MD = ROOT / "reports" / "20260808_KPREDICT_RESET.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

# 3뇌 예측·백테스트 산출물 → 삭제
DELETE_TABLES: dict[str, str] = {
    "lotto_predictions": "3뇌 예측 세트 (brain_tag)",
    "lotto_analysis": "prediction_feedback 등 예측 채점 결과",
    "testlotto_brain_review": "복기뇌 산출",
    "testlotto_brain_learn_state": "뇌별 누적 학습상태 (3행=3뇌)",
    "testlotto_brain_weights": "뇌별 가중치",
    "testlotto_backtest_runs": "백테스트 실행 헤더",
    "testlotto_backtest_draw_results": "백테스트 회차별 결과",
    "testlotto_pool_view_cache": "10세트 pool·몰아주기 캐시",
    "testlotto_evolve_log": "회차·뇌별 pool/repack 채점 로그",
    "testlotto_evolve_auto_state": "evolve 자동화 상태",
    "testlotto_pool_hit_ledger": "세트별 적중 원장 (K-POOL-HIT-LEDGER)",
    "testlotto_pool_hit_scatter": "회차×뇌 적중 분산 요약",
    "hit_warrant_log": "적중 명분 로그 (예측 대조 산출)",
}

# 원천 데이터 · 회차 파생 → 보존
KEEP_TABLES: dict[str, str] = {
    "lotto_draws": "회차 당첨번호 (원천 · 재수집 필요)",
    "testlotto_draw_features": "회차 자체 특성 (회차 파생)",
    "testlotto_draw_prize_tiers": "등위별 당첨정보 (원천)",
    "testlotto_draw_detail": "회차 상세 (원천)",
    "testlotto_draw_win_stores": "당첨판매점 (원천)",
    "testlotto_rare_bundle_catalog": "희귀묶음 카탈로그 (원천)",
    "testlotto_rare_bundle_hits": "희귀묶음 적중 (회차 파생 · 3뇌 예측 아님)",
    "transition_log": "회차 이행 기록 (회차 파생 · 3뇌 예측 아님)",
    "testlotto_brain_page": "뇌 소개 문구 (UI)",
    "sqlite_sequence": "SQLite 내부",
}


def _tables(conn: Any) -> list[str]:
    return [
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
    ]


def _counts(conn: Any, tabs: list[str]) -> dict[str, int]:
    return {t: conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in tabs}


def _brain_columns(conn: Any, table: str) -> list[str]:
    cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
    return [c for c in cols if c in ("brain_tag", "brain", "brain_name")]


def survey() -> dict[str, Any]:
    from app.testlotto.models import get_lotto_db, init_testlotto_db

    init_testlotto_db()
    conn = get_lotto_db()
    tabs = _tables(conn)
    before = _counts(conn, tabs)
    brain_cols = {t: _brain_columns(conn, t) for t in tabs}
    conn.close()

    unknown = [t for t in tabs if t not in DELETE_TABLES and t not in KEEP_TABLES]
    return {
        "tables": tabs,
        "counts_before": before,
        "brain_columns": {t: c for t, c in brain_cols.items() if c},
        "unknown_tables": unknown,
        "to_delete": {t: before.get(t, 0) for t in DELETE_TABLES if t in tabs},
        "to_keep": {t: before.get(t, 0) for t in KEEP_TABLES if t in tabs},
    }


def apply_reset(targets: list[str]) -> dict[str, int]:
    from app.testlotto.models import get_lotto_db

    conn = get_lotto_db()
    deleted: dict[str, int] = {}
    try:
        for t in targets:
            n = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            conn.execute(f'DELETE FROM "{t}"')
            deleted[t] = int(n)
        conn.commit()
    except Exception:
        conn.rollback()
        conn.close()
        raise
    conn.close()

    # VACUUM 은 트랜잭션 밖에서
    conn2 = get_lotto_db()
    conn2.isolation_level = None
    conn2.execute("VACUUM")
    conn2.close()
    return deleted


def build_md(p: dict[str, Any]) -> str:
    s = p["survey"]
    L = [
        f"# {RESET_ID} — 3뇌 예측 산출물 리셋",
        "",
        f"- 생성 {p['generated_at']} · 대상 `data/lotto_testlotto.db` 단독",
        f"- 실제 적용: **{p['applied']}** · 백업: **{p['backup']}**",
        "",
        "## 0. 형 지시",
        "",
        "> 로또테스트에 백테스트한 모든 db 에 잇는 3뇌 예측을 삭제해줘",
        "",
        "테스트로또 DB 단독 · 백업 없음. 회차·당첨정보 같은 **원천 데이터는 보존**하고,",
        "회차에서 기계적으로 파생되는 기록도 3뇌 예측이 아니므로 남겼다.",
        "",
        "## 1. 삭제 대상",
        "",
        "|테이블|삭제 행수|사유|",
        "|---|---|---|",
    ]
    for t, n in sorted(s["to_delete"].items(), key=lambda kv: -kv[1]):
        L.append(f"|`{t}`|{n}|{DELETE_TABLES[t]}|")
    L.append(f"|**합계**|**{sum(s['to_delete'].values())}**||")

    L += [
        "",
        "## 2. 보존 (건드리지 않음)",
        "",
        "|테이블|행수|사유|",
        "|---|---|---|",
    ]
    for t, n in sorted(s["to_keep"].items(), key=lambda kv: -kv[1]):
        L.append(f"|`{t}`|{n}|{KEEP_TABLES[t]}|")

    L += [
        "",
        "## 3. 뇌 태그를 가진 테이블 (판정 근거)",
        "",
        "추측이 아니라 스키마로 확인한 목록이다.",
        "",
    ]
    for t, c in sorted(s["brain_columns"].items()):
        mark = "삭제" if t in DELETE_TABLES else "보존"
        L.append(f"- `{t}` — 컬럼 {c} · **{mark}**")

    if p["applied"]:
        L += [
            "",
            "## 4. 적용 결과",
            "",
            "|테이블|삭제됨|삭제 후|",
            "|---|---|---|",
        ]
        for t, n in sorted(p["deleted"].items(), key=lambda kv: -kv[1]):
            L.append(f"|`{t}`|{n}|{p['counts_after'].get(t, '?')}|")
        L += [
            "",
            f"- DB 파일 크기 {p['db_mb_before']} MB → **{p['db_mb_after']} MB** (VACUUM 포함)",
        ]

    L += [
        "",
        "## 5. 다음에 해야 할 일",
        "",
        "리셋만으로는 예측이 다시 생기지 않는다. 새 배선(뇌별 성적표 · 신호 상위 세트 ·",
        "뇌 간 RNG 독립)으로 백테스트를 다시 돌려야 기록이 채워진다.",
        "",
        "## 6. 주의",
        "",
        "- 이 DB 는 git 추적 대상(약 51MB)이다. **리셋 결과는 커밋하지 않는다** (레포 위생)",
        "- 미분류 테이블: " + (str(s["unknown_tables"]) if s["unknown_tables"] else "없음"),
        "",
    ]
    return "\n".join(L)


def main() -> None:
    db = ROOT / "data" / "lotto_testlotto.db"
    mb_before = round(db.stat().st_size / 1024 / 1024, 2) if db.exists() else 0.0

    s = survey()
    apply = os.environ.get("K_RESET_APPLY", "").strip() == "1"

    print(f"[{RESET_ID}] 대상 {db.name} · {mb_before} MB · apply={apply}")
    print(f"\n삭제 예정 ({sum(s['to_delete'].values())} 행):")
    for t, n in sorted(s["to_delete"].items(), key=lambda kv: -kv[1]):
        print(f"  {n:>6}  {t}")
    print("\n보존:")
    for t, n in sorted(s["to_keep"].items(), key=lambda kv: -kv[1]):
        print(f"  {n:>6}  {t}")
    if s["unknown_tables"]:
        print(f"\n[경고] 미분류 테이블 {s['unknown_tables']} → 삭제하지 않음")

    deleted: dict[str, int] = {}
    after: dict[str, int] = {}
    if apply:
        deleted = apply_reset(sorted(s["to_delete"]))
        s2 = survey()
        after = s2["counts_before"]
        print(f"\n삭제 완료 {sum(deleted.values())} 행")
    else:
        print("\n※ 예정 내역만 출력했다. 실제 삭제는 K_RESET_APPLY=1")

    mb_after = round(db.stat().st_size / 1024 / 1024, 2) if db.exists() else 0.0
    payload = {
        "id": RESET_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db": db.as_posix(),
        "applied": apply,
        "backup": "없음 (형 지시)",
        "db_mb_before": mb_before,
        "db_mb_after": mb_after,
        "survey": s,
        "deleted": deleted,
        "counts_after": after,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md = build_md(payload)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(f"-> {OUT_JSON.relative_to(ROOT)}\n-> {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
