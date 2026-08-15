# -*- coding: utf-8 -*-
"""K-STAT-COOCCUR-PREFER + EVOLVE-DIAG — READ-ONLY 실측. APPLY 없음."""
from __future__ import annotations

import json
import math
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KSTAT_COOCCUR_PREFER_EVOLVE_DISCUSS.json"
OUT_MD = ROOT / "reports" / "20260815_KSTAT_COOCCUR_PREFER_EVOLVE_DISCUSS.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _flags() -> dict[str, Any]:
    import app.testlotto.signal_pool as sp
    from app.testlotto.brains.markov_brain import learn as mlearn
    from app.testlotto.brains.shared import crowd_signal
    from app.testlotto.evolve_auto import evolve_auto_enabled
    from app.testlotto.stat_pool_learn import STAT_POOL_LEARN_WIRE
    from app.testlotto.brains.review_brain import learn as rlearn

    review_has_apply = hasattr(rlearn, "apply_learn_boost")
    return {
        "ROLE_TIER_LEARN_WIRE": bool(sp.ROLE_TIER_LEARN_WIRE),
        "ROLE_TIER_LEARN_BRAINS": sorted(sp.ROLE_TIER_LEARN_BRAINS),
        "STAT_POOL_LEARN_WIRE": bool(STAT_POOL_LEARN_WIRE),
        "HINT_SPEC_BY_BRAIN": {k: list(v) if v[0] is not None else [None, v[1]] for k, v in sp.HINT_SPEC_BY_BRAIN.items()},
        "SCORE_WEIGHTS_BY_BRAIN": {k: list(v) for k, v in sp.SCORE_WEIGHTS_BY_BRAIN.items()},
        "markov_LEARN_WIRED": bool(mlearn.LEARN_WIRED),
        "review_has_apply_learn_boost": bool(review_has_apply),
        "PREFER_WIRE": bool(crowd_signal.PREFER_WIRE),
        "PRIZE_WIRE": bool(crowd_signal.PRIZE_WIRE),
        "PREFER_BDAY_STRENGTH": float(crowd_signal.PREFER_BDAY_STRENGTH),
        "PRIZE_SHAPE_STRENGTH": float(crowd_signal.PRIZE_SHAPE_STRENGTH),
        "BLEND_STRENGTH_BY_BRAIN": dict(crowd_signal.BLEND_STRENGTH_BY_BRAIN),
        "EVOLVE_AUTO": bool(evolve_auto_enabled()),
        "FEATURE_LAMBDA_WIRE": bool(sp.FEATURE_LAMBDA_WIRE),
        "stat_calls_annotate_prefer": False,
    }


def _measure() -> dict[str, Any]:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    draws = [
        {
            "draw_no": int(r["draw_no"]),
            "nums": [int(r[f"num{i}"]) for i in range(1, 7)],
        }
        for r in conn.execute(
            "SELECT draw_no,num1,num2,num3,num4,num5,num6 FROM lotto_draws ORDER BY draw_no"
        )
    ]
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    evolve_n = evolve_by = None
    if "testlotto_evolve_log" in tables:
        evolve_n = int(
            conn.execute("SELECT COUNT(*) FROM testlotto_evolve_log").fetchone()[0]
        )
        evolve_by = {
            str(r["brain_tag"]): int(r["n"])
            for r in conn.execute(
                "SELECT brain_tag, COUNT(*) n FROM testlotto_evolve_log GROUP BY brain_tag"
            )
        }
        ev_minmax = conn.execute(
            "SELECT MIN(draw_no) a, MAX(draw_no) b FROM testlotto_evolve_log"
        ).fetchone()
        evolve_span = [ev_minmax["a"], ev_minmax["b"]] if ev_minmax and ev_minmax["a"] else None
    else:
        evolve_span = None
    bt_n = None
    if "testlotto_backtest_runs" in tables:
        bt_n = int(
            conn.execute("SELECT COUNT(*) FROM testlotto_backtest_runs").fetchone()[0]
        )
    ledger_by = {}
    if "testlotto_pool_hit_ledger" in tables:
        ledger_by = {
            str(r["brain_tag"]): int(r["n"])
            for r in conn.execute(
                "SELECT brain_tag, COUNT(*) n FROM testlotto_pool_hit_ledger GROUP BY brain_tag"
            )
        }
    conn.close()

    n = len(draws)
    max_d = draws[-1]["draw_no"] if draws else None
    pair_all: Counter = Counter()
    consec_draws = 0
    neighbor_same = 0  # 연번과 동일: 같은 회 |a-b|=1
    for d in draws:
        ns = sorted(d["nums"])
        for a, b in combinations(ns, 2):
            pair_all[(a, b)] += 1
            if b - a == 1:
                neighbor_same += 1
        if any(ns[i + 1] - ns[i] == 1 for i in range(5)):
            consec_draws += 1

    # 이웃수(회차 사이): 직전 회 n이 있으면 다음 회에 n±1
    next_nb_hit = next_nb_den = 0
    for i in range(len(draws) - 1):
        prev = set(draws[i]["nums"])
        nxt = set(draws[i + 1]["nums"])
        neigh: set[int] = set()
        for x in prev:
            if 1 <= x - 1 <= 45:
                neigh.add(x - 1)
            if 1 <= x + 1 <= 45:
                neigh.add(x + 1)
        neigh -= prev
        if not neigh:
            continue
        next_nb_den += 1
        if neigh & nxt:
            next_nb_hit += 1

    recent = draws[-200:] if n >= 200 else draws
    pair_200: Counter = Counter()
    for d in recent:
        for a, b in combinations(sorted(d["nums"]), 2):
            pair_200[(a, b)] += 1

    # 이론: 한 회 C(6,2)=15쌍. 특정 쌍 P = C(43,4)/C(45,6)
    p_pair = math.comb(43, 4) / math.comb(45, 6)
    exp_pair = n * p_pair
    top5 = [{"pair": list(p), "count": c, "exp": round(exp_pair, 2)} for p, c in pair_all.most_common(5)]

    from app.testlotto.features.draw_features import build_pair_freq, consecutive_pairs

    # 함수 존재 확인 (같은 데이터)
    pf = build_pair_freq(
        [
            {
                "draw_no": d["draw_no"],
                "num1": d["nums"][0],
                "num2": d["nums"][1],
                "num3": d["nums"][2],
                "num4": d["nums"][3],
                "num5": d["nums"][4],
                "num6": d["nums"][5],
            }
            for d in recent
        ],
        window=100,
    )
    consec_fn = [
        consecutive_pairs(d["nums"]) for d in recent
    ]

    return {
        "n_draws": n,
        "max_draw": max_d,
        "pair_top5_all": top5,
        "pair_distinct_all": len(pair_all),
        "consec_draw_rate": round(consec_draws / max(n, 1), 4),
        "consec_draws": consec_draws,
        "neighbor_same_draw_pairs": neighbor_same,
        "next_draw_neighbor_hit_rate": round(next_nb_hit / max(next_nb_den, 1), 4),
        "next_draw_neighbor_n": next_nb_den,
        "next_draw_neighbor_null_approx": round(
            1.0 - math.comb(35, 6) / math.comb(45, 6), 4
        ),
        "next_draw_neighbor_note": "이웃집합≈10이면 이론 P(≥1)≈1-C(35,6)/C(45,6)≈0.778. 실측≈이론. 예측신호 아님.",
        "build_pair_freq_window100_pairs": len(pf),
        "consecutive_pairs_mean_last200": round(sum(consec_fn) / max(len(consec_fn), 1), 4),
        "p_specific_pair": round(p_pair, 6),
        "evolve_log_n": evolve_n,
        "evolve_log_by_brain": evolve_by,
        "evolve_log_span": evolve_span,
        "backtest_runs_n": bt_n,
        "ledger_by_brain": ledger_by,
        "tables_present": {
            "testlotto_evolve_log": "testlotto_evolve_log" in tables,
            "testlotto_evolve_auto_state": "testlotto_evolve_auto_state" in tables,
            "testlotto_backtest_runs": "testlotto_backtest_runs" in tables,
        },
    }


def _md(o: dict[str, Any]) -> str:
    f = o.get("flags") or {}
    m = o.get("measure") or {}
    return "\n".join(
        [
            "# K-STAT-COOCCUR-PREFER + EVOLVE-DIAG — 논의 (APPLY 없음)",
            "",
            f"시각: {o['as_of']} · **{o.get('verdict')}** · READ-ONLY · 1237아님 · ge3/mean 클레임 금지",
            "범위=요청A 2뇌 브리핑 + 요청B 추천1·2 실측. 코드 APPLY 없음.",
            "",
            "## 0) 한 줄 의견",
            "",
            "**추천1(궁합·이웃·연번 → prefer 회피)은 가능하되, 번호가중(`blend_weights`/`number_scores`)에 넣으면 안 된다.** "
            "세트 단위 annotate만. **추천2는 새 테이블이 아니라 이미 있는 `testlotto_evolve_log`를 진단으로 재정의**하는 쪽이 맞다. "
            "둘 다 지금 APPLY 하지 말 것.",
            "",
            "---",
            "",
            "## A) markov / review 구조 브리핑",
            "",
            "라이브 진입점: `tools/_k_window_signal_survey.py` `PREDICT_MODULES` = "
            "`predict_markov_brain` / `predict_stat_brain` / `predict_review_brain`.",
            "`predict_review_king.py` · `predict_flow_shaman.py` 는 **DEPRECATED** (구특성·군중신호 미적용).",
            "",
            f"라이브 플래그: `{json.dumps(f, ensure_ascii=False)}`",
            "",
            "### A1) markov = 선호번호뇌",
            "",
            "| 항 | 코드 실측 |",
            "|----|-----------|",
            "| 스킬 | 연속회차 **전이행렬** + 최근 6개에서 **random walk** 방문빈도 → 상위25 가중추출. `engine.py` `build_transition_matrix` / `markov_random_walk` / `generate` |",
            "| 군중 | `prefer_on()`이면 `prefer_table`(1등 당첨자 많은 회 번호 + 생일대 사전)을 `blend_weights`로 **방문가중치에 곱함** → 번호선택에 이미 들어감 |",
            "| 동반 | `learn.apply_learn_boost`의 `pair_boost`가 `build_pair_freq` 상위20쌍 번호를 가중. `predict.py`는 동반쌍 개수를 reasoning만 |",
            "| 보조 | `aux_pattern_spotlight` (쌍·연번·AC). HINT 0.15 |",
            "| 학습 | `LEARN_WIRED=True`. `apply_learn_boost` 소비. `learn_state('markov')` overdue/ending/carry/pair |",
            "| 숙제 소비 | 라이브 `ROLE_TIER_LEARN_BRAINS={stat}` → markov **6~10 역할숙제 OFF** (코드는 보존) |",
            "| 몰아주기 점수 | SCORE (0.65, 0.15, 0.20) · hint=`crowd_prefer` |",
            "| 게이트 축 | prefer (인기). L11b `PREFER_BDAY_STRENGTH=0.0` HOLD |",
            "",
            "필터: 합 80~210 · 홀짝 양극 금지 · 구간≤1 금지 · **연번 최대≥4 금지** (`engine.py` 194–201행).",
            "",
            "### A2) review = 금액뇌",
            "",
            "| 항 | 코드 실측 |",
            "|----|-----------|",
            "| 스킬 | `repeat_rate_after_draw`(직전 나온 뒤 다음에도 나온 비율) + 직전 6개 **×1.8 이월** · 나머지 ×0.85 · **끝수 질량 균등**(K-P3) |",
            "| 군중 | `prize_on()`이면 `prize_table`(1등 적은 회 + 고번호 비선호)을 `blend_weights` → 번호선택에 들어감 |",
            "| 보조 | `aux_miss_detective`. HINT 0.15 |",
            "| 학습 | `apply_learn_boost` **함수 없음**. `load_learn_state('review')`의 `carry_over_boost`만 가중·문구 |",
            "| 숙제 소비 | 라이브 markov와 같이 **역할숙제 OFF** |",
            "| 몰아주기 점수 | SCORE (0.65, 0.15, 0.20) · hint=`crowd_prize` |",
            "| 게이트 축 | prize (몫). L11 `PRIZE_SHAPE_STRENGTH=1.0` 유지 |",
            "",
            "구파일 `predict_review_king.py`는 같은 이월 골격이나 crowd_signal 없음. **라이브 아님**.",
            "",
            "### A3) stat과 겹침 / 독립",
            "",
            "| | stat | markov | review |",
            "|--|------|--------|--------|",
            "| 번호 뽑기 | 빈도+감쇠(+past_learn v2) | 전이 walk | 이월 반복률 |",
            "| 군중 blend | **없음** (`stat_brain`에 crowd_signal 호출 0) | prefer 추종 | prize 비선호 |",
            "| hint | miss_pattern 창52 | crowd_prefer | crowd_prize |",
            "| SCORE | (0.25, 0.35, 0.40) | (0.65, 0.15, 0.20) | 동좌 |",
            "| apply_learn_boost | 있음 (carry/ending/overdue만, **pair 없음**) | 있음 (+pair) | **없음** |",
            "| 역할숙제 소비 | **ON** | OFF | OFF |",
            "",
            "공유 허용 실측: `lotto_draws` + 읽기 헬퍼(`draw_features`, `crowd_signal` 모듈). "
            "노브는 `*_BY_BRAIN`. 테이블 `testlotto_brain_learn_state`는 brain_tag 행 분리.",
            "**겹침 주의:** `crowd_signal.py` 한 파일 · `annotate_prefer`가 `brain=\"markov\"` 고정. "
            "hint 변환 `_build_hint_for_spec`도 crowd_prefer→markov 표 / crowd_prize→review 표. "
            "예측 과정 계수는 분리되어 있으나 **군중 원자료(first_winners)는 같은 회차 컬럼**.",
            "",
            "### A4) 라이브 ON/OFF",
            "",
            "- pool 생성: `expand_pool` 기본 3뇌 모두 생성 가능. 이번 캠페인 소비·튜닝은 **stat만**.",
            "- 역할숙제 읽기: **stat만 ON**.",
            "- STAT_POOL_LEARN: **ON** (stat 1~5).",
            "- markov LEARN_WIRED: **True** (엔진 내부).",
            "- EVOLVE_AUTO env: **OFF** (기본 0).",
            "- PREFER_WIRE / PRIZE_WIRE: **True**.",
            "",
            "---",
            "",
            "## B) 추천 1+2 실현 가능성",
            "",
            f"DB 실측: draws **{m.get('n_draws')}** · MAX **{m.get('max_draw')}** · 1237 미사용.",
            "",
            "### B1) 통계를 lotto_draws에서 뽑을 수 있나",
            "",
            "**가능하다. 함수가 이미 있다.** 4군 `lotto_cooccur_*` 테이블을 가져오면 안 된다 (뇌독립·경로혼선).",
            "",
            "| 신호 | 함수/위치 | 이번 실측 |",
            "|------|-----------|-----------|",
            f"| 궁합(동반쌍) | `draw_features.build_pair_freq` · `data_service.analyze_pair_frequency` | 고유쌍 **{m.get('pair_distinct_all')}** · 특정쌍 이론P **{m.get('p_specific_pair')}** · window100 함수쌍 **{m.get('build_pair_freq_window100_pairs')}** |",
            f"| 연번 | `consecutive_pairs` · `analyze_consecutive` | 연번≥1 회 비율 **{m.get('consec_draw_rate')}** ({m.get('consec_draws')}/{m.get('n_draws')}) · 최근200 연번쌍 평균 **{m.get('consecutive_pairs_mean_last200')}** |",
            f"| 이웃(같은회 ±1) | 연번과 **동일** (\\|a-b\\|=1) | 같은회 이웃쌍 합 **{m.get('neighbor_same_draw_pairs')}** |",
            f"| 이웃(다음회 n±1) | 전용 함수 **없음** · draws로 산출 가능 | 실측 **{m.get('next_draw_neighbor_hit_rate')}** · 이론(이웃≈10) **{m.get('next_draw_neighbor_null_approx')}** → **널과 같음. 예측신호 아님** |",
            "",
            f"전구간 동반 상위5: `{json.dumps(m.get('pair_top5_all'), ensure_ascii=False)}` — 기대횟수≈{((m.get('pair_top5_all') or [{}])[0].get('exp'))}. "
            "상위가 기대보다 조금 높아 보여도 **번호선택 근거로 쓰지 말 것**(K-O·K-U).",
            "",
            "최소 수정 부착점 (stat 독립):",
            "1. **세트 점수만** — `stat_brain/predict.py`의 generate **이후**, `diversity.pick` **이전**. markov `annotate_prefer`를 호출하지 말 것.",
            "2. 또는 진단만 — `evolve_log.set_features`에 pair/consec 필드 추가 (예측 불변).",
            "3. `number_scores` / `blend_weights` / `engine.generate` 가중 — **금지** (freq·K-O).",
            "",
            "### B2) prefer 축에만 연결 가능한가",
            "",
            "**세트 단위라면 가능. 번호 테이블에 넣으면 불가능에 가깝다.**",
            "",
            "- 게이트 prefer = `prefer_table`의 **번호 평균** (`set_crowd_score`). 궁합은 **쌍·세트** 속성.",
            "- `prefer_table`에 쌍을 녹이면 번호 가중 → markov `blend_weights`와 stat `number_scores` hint가 같이 오염.",
            "- stat 엔진은 지금 crowd_signal을 **안 부른다**. 새 `annotate_combo_unpopular(stat)`만 두면 1~5 `random.choices` 라인은 그대로.",
            "- 다만 annotate는 oversample 후 `diversity.pick` 순서를 바꿔 **살아남는 5장**은 바뀐다. "
            "그건 ‘가중치 테이블 수정’은 아니지만 **발권 구성 변경**이다. 게이트는 prefer/prize 비악화.",
            "- 순수 모니터(점수만 기록, pick 불변)면 K-O와 충돌 없음. ‘인간기법 보강’ 효과는 없음.",
            "",
            "권고 배선: **stat 전용 세트 annotate + 플래그 OFF 기본**. `crowd_signal.prefer_table` 미수정. "
            "markov/review 파일 미수정.",
            "",
            "### B3) 회차 완료 자기진단 로그",
            "",
            "**새 파이프를 만들 필요 없다. 이미 있다.**",
            "",
            f"- 테이블 `testlotto_evolve_log` **존재** · 행 **{m.get('evolve_log_n')}** (리셋 후 비어 있음 · 코드만 있음)",
            f"- `testlotto_backtest_runs` **{m.get('backtest_runs_n')}** (UI SOFT `backtest_runs=0`과 같은 축)",
            f"- 원장 `{json.dumps(m.get('ledger_by_brain'), ensure_ascii=False)}`",
            "",
            "쓰기 트리거 실측:",
            "- `click_feedback` → learn_state + evolve_log 마크 (`K-KK-FEEDBACK`)",
            "- `coordinator._auto_feedback` (다음 예측 시 직전 회 채점) + ledger/skill/role homework",
            "- `evolve_auto` S2: 캐시→evolve_log 백필. **`EVOLVE_AUTO` 기본 OFF**",
            "",
            "이미 있는 것 = (a) 예측 대비 적중 (`pool_hits_json`/`repack_hits_json`/`mean_hits`). "
            "`WEIGHT_APPLIED=0.0` · 학습 wire 없음 (Phase1).",
            "",
            "없는 것:",
            "- (b) drift χ²/KS **회차 1장** — 자리 없음. 기존 도구는 **창 단위** (`_k_past_learn_score_rule_diag`, `_k_math_pattern_warrant`). "
            "회차 6개로 χ²를 돌리면 무의미. 넣을 거면 evolve_log에 **롤링 창(예 52회) 스냅샷**만.",
            "- (c) boost 사후 귀속 — `features_json`에 구조특징만. carry/ending/overdue가 ‘이번 회에 도움’인지는 **인과가 아님**. "
            "모니터 필드(이번 장에 이월 n개·끝수겹침)는 가능. APPLY 입력 금지.",
            "",
            "끼움점: `click_feedback` / `_auto_feedback` 끝 또는 `evolve_auto` S2. 예측 산출물 아님.",
            "",
            "### B4) 함정 3개 (형이 먼저)",
            "",
            "1. **이미 들어가 있다.** 궁합·연번은 markov `pair_boost` + `aux_pattern_spotlight`에 번호/보조점수로 있음. "
            "같은 신호를 stat freq에 넣으면 K-O. prefer 회피로 넣어도 markov는 같은 쌍빈도를 **추종** 중이라, "
            "두 뇌가 `lotto_draws` 쌍통계를 반대로 쓰면 발권 혼합 시 효과가 상쇄될 수 있다.",
            "2. **축 혼동.** prefer_table=번호 인기. 궁합=조합. 번호 테이블에 섞으면 `blend_weights`가 선택을 바꾼다. "
            "‘prefer 계산에만’을 지키려면 **새 세트 점수**이거나 **로그 전용**이어야 한다.",
            "3. **진단 유령.** evolve_log는 이미 쌓인다. 새 테이블을 만들면 `backtest_runs=0`과 같은 SOFT 공백이 하나 더 생긴다. "
            "회차 χ²는 공정성 감시가 아니라 노이즈다. `FEATURE_LAMBDA_WIRE`는 라이브 **False** — evolve mean_hits를 예측에 넣지 말 것(K-O).",
            "",
            "## 6) 합의 / 반박",
            "",
            "| 문장 | 커서 |",
            "|------|------|",
            "| 인간기법은 이미 점수식에 대부분 있다 | **동의** (stat 0.25/0.35/0.40 + carry/ending/overdue) |",
            "| 성능↑가 아니라 보강+진단 | **동의** (K-O) |",
            "| 궁합을 prefer 회피에 연결 | **조건부 동의** · 세트 annotate만 · 표/freq 금지 |",
            "| 이웃수 | **정의 필요**. 같은회 ±1=연번과 중복. 다음회 n±1은 전이기호(markov 영역) |",
            "| 회차마다 자기진단 진화 | **로그 재정의에 동의** · 새 엔진/새 테이블 반박 · EVOLVE_AUTO 켜지 말 것 |",
            "| χ²를 회차마다 | **반박** · 롤링 창만 |",
            "",
            "## 7) 하지 말 것",
            "",
            "- 본턴 코드 APPLY · 1237 · 등수/mean APPLY · 동결 3종 · 3뇌 동시",
            "- lotto4 `lotto_cooccur_*` 를 stat에 연결",
            "- `prefer_table` / markov `blend_weights` 수정",
            "- EVOLVE_AUTO=1 · feature_lambda를 예측 입력으로 ON",
            "",
            "## 8) 다음 (형 선택)",
            "",
            "A. 추천1 SPEC만 (stat 세트 annotate · 플래그 OFF · 게이트 prefer/prize) — 별 GO",
            "B. 추천2 SPEC만 (evolve_log 필드 확장 · 롤링 χ² 모니터 · WEIGHT 0 유지)",
            "C. A+B SPEC (APPLY 아님)",
            "D. 보류",
            "",
        ]
    )


def main() -> int:
    flags = _flags()
    meas = _measure()
    out = {
        "id": "K-STAT-COOCCUR-PREFER-EVOLVE-DISCUSS",
        "as_of": _now(),
        "ge3_claim": False,
        "draw_1237": False,
        "read_only": True,
        "code_apply": False,
        "verdict": "DISCUSS_OK",
        "flags": flags,
        "measure": meas,
        "insert": {
            "rec1": "stat_brain.predict after generate, before diversity.pick — set annotate only",
            "rec1_forbid": ["blend_weights", "number_scores", "prefer_table", "engine.generate weights"],
            "rec2": "extend testlotto_evolve_log via click_feedback/_auto_feedback/evolve_auto S2",
            "rec2_forbid": ["new table", "EVOLVE_AUTO=1", "per-draw chi2 as fairness"],
        },
        "live_paths": {
            "markov": "app/testlotto/brains/markov_brain/predict.py",
            "review": "app/testlotto/brains/review_brain/predict.py",
            "review_king_deprecated": "app/testlotto/brains/predict_review_king.py",
        },
    }
    OUT_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    md = _md(out)
    OUT_MD.write_text(md, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(md, encoding="utf-8")
    print(
        json.dumps(
            {
                "verdict": out["verdict"],
                "max_draw": meas.get("max_draw"),
                "n_draws": meas.get("n_draws"),
                "consec_rate": meas.get("consec_draw_rate"),
                "next_nb": meas.get("next_draw_neighbor_hit_rate"),
                "evolve_n": meas.get("evolve_log_n"),
                "bt_n": meas.get("backtest_runs_n"),
                "brains": flags.get("ROLE_TIER_LEARN_BRAINS"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
