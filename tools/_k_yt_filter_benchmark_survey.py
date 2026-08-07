# -*- coding: utf-8 -*-
"""K-YT-FILTER-BENCH — 유튜브 다중필터 주장 vs lotto_testlotto.db 실측 (READ-ONLY · wire 없음).

Sources:
  https://youtu.be/T7I3hEfQBlc  (Gemini 지능형 생성기 · 합/홀짝/고저/연번/이월/끝수)
  https://youtu.be/3G3zExNItj0  (조코딩 LSTM · 예측 무효 · train/val 붕괴)

Usage:
  python tools/_k_yt_filter_benchmark_survey.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260808_KYT_FILTER_BENCH.json"
OUT_MD = ROOT / "reports" / "20260808_KYT_FILTER_BENCH.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name

C45_6 = math.comb(45, 6)
NULL_MC = 200_000
NULL_SEED = 42


def _nums(d: dict) -> list[int]:
    return [int(d["num1"]), int(d["num2"]), int(d["num3"]), int(d["num4"]), int(d["num5"]), int(d["num6"])]


def _has_consec(ns: list[int]) -> bool:
    s = sorted(ns)
    return any(s[i + 1] == s[i] + 1 for i in range(5))


def _odd_even_key(ns: list[int]) -> str:
    odd = sum(1 for n in ns if n % 2 == 1)
    return f"{odd}:{6 - odd}"


def _high_low_key(ns: list[int]) -> str:
    """영상 정의: 저=1~22 · 고=23~45."""
    low = sum(1 for n in ns if n <= 22)
    return f"{low}:{6 - low}"


def _has_same_ending(ns: list[int]) -> bool:
    ends = [n % 10 for n in ns]
    return len(ends) != len(set(ends))


def _sum_in(ns: list[int], lo: int, hi: int) -> bool:
    return lo <= sum(ns) <= hi


def _profile_ok(ns: list[int], *, sum_band: tuple[int, int]) -> bool:
    oe = _odd_even_key(ns)
    hl = _high_low_key(ns)
    return (
        _sum_in(ns, *sum_band)
        and oe in {"3:3", "4:2", "2:4"}
        and hl in {"3:3", "4:2", "2:4"}
        and _has_consec(ns)
        and _has_same_ending(ns)
    )


def _rate(n: int, total: int) -> float:
    return round(n / max(total, 1), 6)


def analyze_window(draws: list[dict], label: str) -> dict[str, Any]:
    n = len(draws)
    if n == 0:
        return {"label": label, "n": 0}

    sum_110_170 = 0
    sum_100_180 = 0
    oe_bal = 0
    hl_bal = 0
    consec = 0
    same_end = 0
    profile_110 = 0
    profile_100 = 0
    oe_dist: Counter[str] = Counter()
    hl_dist: Counter[str] = Counter()
    sums: list[int] = []

    for d in draws:
        ns = _nums(d)
        s = sum(ns)
        sums.append(s)
        oe = _odd_even_key(ns)
        hl = _high_low_key(ns)
        oe_dist[oe] += 1
        hl_dist[hl] += 1
        if _sum_in(ns, 110, 170):
            sum_110_170 += 1
        if _sum_in(ns, 100, 180):
            sum_100_180 += 1
        if oe in {"3:3", "4:2", "2:4"}:
            oe_bal += 1
        if hl in {"3:3", "4:2", "2:4"}:
            hl_bal += 1
        if _has_consec(ns):
            consec += 1
        if _has_same_ending(ns):
            same_end += 1
        if _profile_ok(ns, sum_band=(110, 170)):
            profile_110 += 1
        if _profile_ok(ns, sum_band=(100, 180)):
            profile_100 += 1

    carry_main_ge1 = 0
    carry_bonus_ge1 = 0
    carry_pairs = 0
    for i in range(len(draws) - 1):
        a = set(_nums(draws[i]))
        b_main = set(_nums(draws[i + 1]))
        b_bonus = set(b_main)
        b_bonus.add(int(draws[i + 1]["bonus"]))
        carry_pairs += 1
        if a & b_main:
            carry_main_ge1 += 1
        if a & b_bonus:
            carry_bonus_ge1 += 1

    return {
        "label": label,
        "n": n,
        "draw_range": [int(draws[0]["draw_no"]), int(draws[-1]["draw_no"])],
        "sum": {
            "mean": round(sum(sums) / n, 3),
            "min": min(sums),
            "max": max(sums),
            "in_110_170": {"count": sum_110_170, "rate": _rate(sum_110_170, n)},
            "in_100_180": {"count": sum_100_180, "rate": _rate(sum_100_180, n)},
        },
        "odd_even_balanced_3_4_2": {"count": oe_bal, "rate": _rate(oe_bal, n)},
        "odd_even_top": dict(oe_dist.most_common(7)),
        "high_low_balanced_3_4_2": {"count": hl_bal, "rate": _rate(hl_bal, n)},
        "high_low_top": dict(hl_dist.most_common(7)),
        "has_consecutive_pair": {"count": consec, "rate": _rate(consec, n)},
        "same_ending_digit_ge1": {"count": same_end, "rate": _rate(same_end, n)},
        "carry_over": {
            "pairs": carry_pairs,
            "main6_ge1": {
                "count": carry_main_ge1,
                "rate": _rate(carry_main_ge1, carry_pairs),
            },
            "prev_main_in_next_main_or_bonus_ge1": {
                "count": carry_bonus_ge1,
                "rate": _rate(carry_bonus_ge1, carry_pairs),
                "note": "영상 '보너스포함 7개 중 1개'에 가까운 정의",
            },
        },
        "yt_profile_and": {
            "sum110_170_oe_hl_consec_ending": {
                "count": profile_110,
                "rate": _rate(profile_110, n),
            },
            "sum100_180_oe_hl_consec_ending": {
                "count": profile_100,
                "rate": _rate(profile_100, n),
            },
            "note": "이월은 시계열쌍이라 AND 프로파일에서 제외(단건 필터만)",
        },
    }


def null_mc(n_samples: int = NULL_MC, seed: int = NULL_SEED) -> dict[str, Any]:
    rng = random.Random(seed)
    pool = list(range(1, 46))
    sum_110 = sum_100 = oe = hl = consec = ending = p110 = p100 = 0
    for _ in range(n_samples):
        ns = rng.sample(pool, 6)
        if _sum_in(ns, 110, 170):
            sum_110 += 1
        if _sum_in(ns, 100, 180):
            sum_100 += 1
        if _odd_even_key(ns) in {"3:3", "4:2", "2:4"}:
            oe += 1
        if _high_low_key(ns) in {"3:3", "4:2", "2:4"}:
            hl += 1
        if _has_consec(ns):
            consec += 1
        if _has_same_ending(ns):
            ending += 1
        if _profile_ok(ns, sum_band=(110, 170)):
            p110 += 1
        if _profile_ok(ns, sum_band=(100, 180)):
            p100 += 1

    carry_ge1 = 0
    for _ in range(n_samples):
        a = set(rng.sample(pool, 6))
        b = set(rng.sample(pool, 6))
        if a & b:
            carry_ge1 += 1

    consec_theory = 1.0 - math.comb(40, 6) / C45_6

    return {
        "method": "MC_uniform_C45_6",
        "n_samples": n_samples,
        "seed": seed,
        "rates": {
            "sum_110_170": _rate(sum_110, n_samples),
            "sum_100_180": _rate(sum_100, n_samples),
            "odd_even_balanced": _rate(oe, n_samples),
            "high_low_balanced": _rate(hl, n_samples),
            "has_consecutive_pair": _rate(consec, n_samples),
            "has_consecutive_pair_theory": round(consec_theory, 6),
            "same_ending_digit_ge1": _rate(ending, n_samples),
            "carry_main6_ge1": _rate(carry_ge1, n_samples),
            "yt_profile_sum110": _rate(p110, n_samples),
            "yt_profile_sum100": _rate(p100, n_samples),
        },
    }


def delta(emp: float, null: float) -> float:
    return round(emp - null, 6)


def attach_deltas(win: dict[str, Any], null: dict[str, Any]) -> dict[str, Any]:
    nr = null["rates"]
    return {
        "sum_110_170": delta(win["sum"]["in_110_170"]["rate"], nr["sum_110_170"]),
        "sum_100_180": delta(win["sum"]["in_100_180"]["rate"], nr["sum_100_180"]),
        "odd_even_balanced": delta(win["odd_even_balanced_3_4_2"]["rate"], nr["odd_even_balanced"]),
        "high_low_balanced": delta(win["high_low_balanced_3_4_2"]["rate"], nr["high_low_balanced"]),
        "has_consecutive_pair": delta(
            win["has_consecutive_pair"]["rate"], nr["has_consecutive_pair"]
        ),
        "same_ending_digit_ge1": delta(
            win["same_ending_digit_ge1"]["rate"], nr["same_ending_digit_ge1"]
        ),
        "carry_main6_ge1": delta(
            win["carry_over"]["main6_ge1"]["rate"], nr["carry_main6_ge1"]
        ),
        "yt_profile_sum110": delta(
            win["yt_profile_and"]["sum110_170_oe_hl_consec_ending"]["rate"],
            nr["yt_profile_sum110"],
        ),
    }


def build_report(payload: dict[str, Any]) -> str:
    full = payload["windows"]["full"]
    tail = payload["windows"]["tail100"]
    null = payload["null_mc"]["rates"]
    d_full = payload["delta_vs_null"]["full"]
    yt = payload["sources"]

    lines = [
        "# K-YT-FILTER-BENCH — 유튜브 필터/LSTM vs 테스트로또 실측",
        "",
        f"📅 2026-08-08 KST · **DOC_SURVEY** · wire=**False** · 수치 SSOT=`{OUT_JSON.name}`",
        "",
        "---",
        "",
        "## 0) 한 줄",
        "",
        "과거 유튜브(Gemini 다중필터 생성기 · LSTM 예측)를 ROK21 `lotto_testlotto.db`로 재실측했다. "
        "필터는 **당첨P↑가 아니라 조합 프로파일(=null 근처 질량)** 이며, LSTM 시퀀스 예측은 기각 유지. "
        "2026-08 벤치 포인트는 바이브 생성기 복제가 아니라 **annotate/warrant/structure 진단축**이다.",
        "",
        "---",
        "",
        "## 1) 앱 구조 (testlotto SSOT)",
        "",
        "| 역할 | 경로 |",
        "|------|------|",
        "| 엔트리 | `app/main_v13.py` · 포트 **7021** |",
        "| API | `app/testlotto/routes.py` `/api/testlotto` |",
        "| 예측 | `brains/coordinator.py` — **3예측+4보조** |",
        "| DB | `data/lotto_testlotto.db` |",
        "| 컨닝방지 | `data_service._get_draws_before(T)` = draw_no < T |",
        "| 벤치 | `tools/_k_*` → `docs/benchmarks/*.json` |",
        "",
        "흐름: draws → coordinator → aux/quota → predictions → walkforward/bench.",
        "",
        "---",
        "",
        "## 2) 영상 소스",
        "",
        "| ID | URL | 요지 |",
        "|----|-----|------|",
        f"| YT1 | {yt['gemini_generator']['url']} | {yt['gemini_generator']['claim']} |",
        f"| YT2 | {yt['lstm_critique']['url']} | {yt['lstm_critique']['claim']} |",
        "",
        "---",
        "",
        "## 3) DB 실측 (전구간 / 최근100)",
        "",
        f"- MAX draw = **{payload['meta']['max_draw']}** · n_full=**{full['n']}** · n_tail=**{tail['n']}**",
        f"- null = MC n={payload['null_mc']['n_samples']} seed={payload['null_mc']['seed']} (균등 C(45,6))",
        "",
        "### 3.1 단건 필터 rate",
        "",
        "| 필터 | full rate | Δnull | tail100 | null |",
        "|------|-----------|-------|---------|------|",
        f"| sum 110–170 | {full['sum']['in_110_170']['rate']} | {d_full['sum_110_170']:+} | {tail['sum']['in_110_170']['rate']} | {null['sum_110_170']} |",
        f"| sum 100–180 | {full['sum']['in_100_180']['rate']} | {d_full['sum_100_180']:+} | {tail['sum']['in_100_180']['rate']} | {null['sum_100_180']} |",
        f"| 홀짝 3:3/4:2/2:4 | {full['odd_even_balanced_3_4_2']['rate']} | {d_full['odd_even_balanced']:+} | {tail['odd_even_balanced_3_4_2']['rate']} | {null['odd_even_balanced']} |",
        f"| 고저(≤22:>22) 동일군 | {full['high_low_balanced_3_4_2']['rate']} | {d_full['high_low_balanced']:+} | {tail['high_low_balanced_3_4_2']['rate']} | {null['high_low_balanced']} |",
        f"| 연번≥1쌍 | {full['has_consecutive_pair']['rate']} | {d_full['has_consecutive_pair']:+} | {tail['has_consecutive_pair']['rate']} | {null['has_consecutive_pair']} (이론 {null['has_consecutive_pair_theory']}) |",
        f"| 동일끝수≥1 | {full['same_ending_digit_ge1']['rate']} | {d_full['same_ending_digit_ge1']:+} | {tail['same_ending_digit_ge1']['rate']} | {null['same_ending_digit_ge1']} |",
        f"| 이월 main6≥1 | {full['carry_over']['main6_ge1']['rate']} | {d_full['carry_main6_ge1']:+} | {tail['carry_over']['main6_ge1']['rate']} | {null['carry_main6_ge1']} |",
        f"| 이월(+next bonus) | {full['carry_over']['prev_main_in_next_main_or_bonus_ge1']['rate']} | — | {tail['carry_over']['prev_main_in_next_main_or_bonus_ge1']['rate']} | — |",
        f"| YT AND 프로파일(sum110…) | {full['yt_profile_and']['sum110_170_oe_hl_consec_ending']['rate']} | {d_full['yt_profile_sum110']:+} | {tail['yt_profile_and']['sum110_170_oe_hl_consec_ending']['rate']} | {null['yt_profile_sum110']} |",
        "",
        f"- sum mean full=**{full['sum']['mean']}** (min {full['sum']['min']} / max {full['sum']['max']})",
        "",
        "### 3.2 영상 주장 vs 실측 (교정)",
        "",
        "| 영상 주장(요지) | ROK21 실측(full) | 판정 |",
        "|-----------------|------------------|------|",
        "| 합 110–170이 흔함 / 101–180≈80%+ | "
        f"110–170={full['sum']['in_110_170']['rate']} · 100–180={full['sum']['in_100_180']['rate']} | "
        f"{'질량대역 OK·null근접' if abs(d_full['sum_100_180']) < 0.05 else '편차확인'} |",
        "| 홀짝 3:3/4:2/2:4가 대다수 | "
        f"{full['odd_even_balanced_3_4_2']['rate']} (Δ{d_full['odd_even_balanced']:+}) | "
        "프로파일 필터(예측력≠) |",
        "| 연번 포함≈55% | "
        f"{full['has_consecutive_pair']['rate']} vs null≈{null['has_consecutive_pair']} | "
        "≈null · '의외로 흔함'은 조합기하 |",
        "| 이월≈42%(보너스포함) | "
        f"main={full['carry_over']['main6_ge1']['rate']} · +bonus={full['carry_over']['prev_main_in_next_main_or_bonus_ge1']['rate']} | "
        "정의 민감 · Δnull 작음 |",
        "| 동일끝수≈77% | "
        f"{full['same_ending_digit_ge1']['rate']} (Δ{d_full['same_ending_digit_ge1']:+}) | "
        "≈null · 필터≠엣지 |",
        "",
        "---",
        "",
        "## 4) ROK21 매핑 (이미 있는 것)",
        "",
        "| 영상 축 | ROK21 | 상태 |",
        "|---------|-------|------|",
        "| 합·홀짝·존·연속 | `structure_cover.py` | WIRE **OFF** · HOLD |",
        "| carry / consec 라벨 | `hit_warrant.py` · TRANSITION HIT-WARRANT | 로그전용 · weight=0 |",
        "| carry/ending boost | `stat_brain/predict.py` | 동결 상한 유지 |",
        "| 합/홀짝/연번 analyze | `data_service.analyze_*` | API 통계 |",
        "| 인기(합·연속·생일) | KSIGNAL L4 스펙 | w*=0 진단 |",
        "| LSTM/시퀀스 DL | 레거시 미배선 | **부활 금지**(조코딩과 동일 결론) |",
        "",
        "---",
        "",
        "## 5) 2026-08 벤치마킹 — 채택 / 기각",
        "",
        "### 채택 (분석·진단만 · wire 금지)",
        "",
        "1. 다중필터 체크리스트 → **세트 annotate / warrant / structure mass** 진단축으로 재사용",
        "2. Gemini 딥리서치 숫자 → **우리 DB+null**로 교정하는 워크플로(이미 `_k_*` 우위)",
        "3. 균형/핫/콜드 모드 → brain·quota **성향 라벨 문서화**만 (발권 강제 아님)",
        "4. 조코딩 교훈 → train 과적합·독립시행 → BENCH_PROTOCOL null/WF 유지",
        "",
        "### 기각",
        "",
        "1. 바이브코딩으로 새 '지능형 생성기' 재작성",
        "2. LSTM/시퀀스 DL 예측 경로 부활",
        "3. 필터 AND를 live 5장 강제 (발권가중·WIRE)",
        "4. '당첨 확률↑' 마케팅 문구 차용",
        "",
        "### 2026 AI 업그레이드 각도",
        "",
        "- 모델이 좋아져도 **독립시행+등확률** 전제는 안 바뀜 → LLM은 예측기가 아니라 "
        "**postmortem·warrant 설명·taxonomy 스키마**에 쓰는 편이 ROK21과 맞음.",
        "- 영상1 프로파일은 KSIGNAL L1/L4 · STRUCTURE_COVER와 겹침 → **신규 wire 후보 아님**, "
        "기존 HOLD/DOC 트랙의 외부 근거 보강용.",
        "",
        "---",
        "",
        "## 6) 판정",
        "",
        f"- verdict: **{payload['verdict']}**",
        f"- pass: **{payload['pass']}**",
        "- wire: **False** · engine/quota/coordinator 미변경",
        "- 다음: 형 GO 없으면 트랙 정지 유지 · 라벨확장만 별도 지시",
        "",
        "---",
        "",
        f"생성: `tools/_k_yt_filter_benchmark_survey.py`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    from app.testlotto.data_service import get_all_draws

    draws = get_all_draws()
    draws = sorted(draws, key=lambda d: int(d["draw_no"]))
    if not draws:
        print("NO_DRAWS")
        return 1

    full = analyze_window(draws, "full")
    tail = analyze_window(draws[-100:], "tail100")
    null = null_mc()

    payload: dict[str, Any] = {
        "id": "K-YT-FILTER-BENCH",
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verdict": "DOC_SURVEY",
        "pass": True,
        "wire": False,
        "meta": {
            "max_draw": int(draws[-1]["draw_no"]),
            "n_draws": len(draws),
            "db": "data/lotto_testlotto.db",
            "note": "당첨P↑ 비약속 · 필터=조합 프로파일 질량",
        },
        "sources": {
            "gemini_generator": {
                "url": "https://youtu.be/T7I3hEfQBlc",
                "claim": "다중필터(합·홀짝·고저·연번·이월·끝수)+균형/핫/콜드 · Gemini 2.5 Pro 딥리서치",
            },
            "lstm_critique": {
                "url": "https://youtu.be/3G3zExNItj0",
                "claim": "LSTM 로또예측 무효 · train만 당첨·val/test≈일상 · 독립시행",
            },
        },
        "windows": {"full": full, "tail100": tail},
        "null_mc": null,
        "delta_vs_null": {
            "full": attach_deltas(full, null),
            "tail100": attach_deltas(tail, null),
        },
        "rok21_map": {
            "structure_cover": "HOLD_WIRE_OFF",
            "hit_warrant_carry_consec": "LOG_ONLY",
            "stat_carry_ending_boost": "FROZEN_CAPS",
            "ksignal_l4_popularity": "SPEC_W0",
            "lstm_path": "NOT_WIRED_KEEP_DEAD",
        },
        "adopt": [
            "filters_as_annotate_warrant_structure_diag",
            "recalibrate_yt_claims_on_our_db_null",
            "mode_labels_doc_only",
        ],
        "reject": [
            "vibe_rewrite_generator",
            "revive_lstm",
            "force_and_filters_on_live_quota",
            "claim_higher_win_probability",
        ],
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = build_report(payload)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "json": str(OUT_JSON),
                "md": str(OUT_MD),
                "drive": str(DRIVE),
                "max_draw": payload["meta"]["max_draw"],
                "full_profile": full["yt_profile_and"]["sum110_170_oe_hl_consec_ending"]["rate"],
                "consec": full["has_consecutive_pair"]["rate"],
                "carry_main": full["carry_over"]["main6_ge1"]["rate"],
                "ending": full["same_ending_digit_ge1"]["rate"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
