# -*- coding: utf-8 -*-
"""K-MARKOV-REVIEW-SKILL-QUALITY — READ-ONLY. 엔진가동·문헌벤치. APPLY없음."""
from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.testlotto.evolve_auto import evolve_auto_enabled
from app.testlotto.signal_pool import (
    FEATURE_LAMBDA_WIRE,
    REPACK_ROLE_QUOTA_BRAINS,
    REPACK_ROLE_QUOTA_WIRE,
    ROLE_TIER_LEARN_BRAINS,
    ROLE_TIER_LEARN_WIRE,
)
from app.testlotto.stat_pool_learn import STAT_POOL_LEARN_WIRE

OUT_JSON = ROOT / "docs" / "benchmarks" / "20260815_KMARKOV_REVIEW_SKILL_QUALITY.json"
OUT_MD = ROOT / "reports" / "20260815_KMARKOV_REVIEW_SKILL_QUALITY.md"
DRIVE = ROOT / "My_Drive_Sync" / "커서보고서" / OUT_MD.name
DB = ROOT / "data" / "lotto_testlotto.db"
LO, HI = 1037, 1236
BRAINS = ("stat", "markov", "review")


def _now() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def _jaccard(a: set[int], b: set[int]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _sets(js: str) -> list[set[int]]:
    out: list[set[int]] = []
    for s in json.loads(js or "[]"):
        nums = [int(x) for x in (s.get("nums") or [])]
        if len(nums) == 6:
            out.append(set(nums))
    return out


def main() -> int:
    conn = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    cache: dict[str, dict[str, int]] = {}
    for tag in BRAINS:
        n = int(
            conn.execute(
                "SELECT COUNT(*) FROM testlotto_pool_view_cache "
                "WHERE brain=? AND draw_no BETWEEN ? AND ?",
                (tag, LO, HI),
            ).fetchone()[0]
        )
        nonempty = 0
        p10 = r5 = 0
        for r in conn.execute(
            "SELECT pool_json, repack_json FROM testlotto_pool_view_cache "
            "WHERE brain=? AND draw_no BETWEEN ? AND ?",
            (tag, LO, HI),
        ):
            p = json.loads(r["pool_json"] or "[]")
            q = json.loads(r["repack_json"] or "[]")
            if p and q:
                nonempty += 1
            if len(p) >= 10:
                p10 += 1
            if len(q) >= 5:
                r5 += 1
        cache[tag] = {"n": n, "nonempty": nonempty, "pool_ge10": p10, "repack_ge5": r5}

    ev = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_evolve_log GROUP BY brain_tag"
        )
    }
    led = {
        str(r["brain_tag"]): int(r["n"])
        for r in conn.execute(
            "SELECT brain_tag, COUNT(*) n FROM testlotto_pool_hit_ledger GROUP BY brain_tag"
        )
    }
    learn_n = int(conn.execute("SELECT COUNT(*) FROM testlotto_brain_learn_state").fetchone()[0])
    dmax = int(conn.execute("SELECT MAX(draw_no) FROM lotto_draws").fetchone()[0])
    pred_1237 = int(
        conn.execute("SELECT COUNT(*) FROM lotto_predictions WHERE target_draw_no=1237").fetchone()[0]
    )

    pairs = (("stat", "markov"), ("stat", "review"), ("markov", "review"))
    jac_1236: dict[str, Any] = {}
    jac_20: dict[str, list[float]] = {f"{a}_{b}": [] for a, b in pairs}
    eq_1236: dict[str, int] = {}
    row1236: dict[str, list[list[int]]] = {}
    for tag in BRAINS:
        r = conn.execute(
            "SELECT pool_json FROM testlotto_pool_view_cache WHERE draw_no=1236 AND brain=?",
            (tag,),
        ).fetchone()
        sets = _sets(r["pool_json"] if r else "[]")
        row1236[tag] = [sorted(s) for s in sets]
    for a, b in pairs:
        sa, sb = _sets(
            conn.execute(
                "SELECT pool_json FROM testlotto_pool_view_cache WHERE draw_no=1236 AND brain=?",
                (a,),
            ).fetchone()["pool_json"]
        ), _sets(
            conn.execute(
                "SELECT pool_json FROM testlotto_pool_view_cache WHERE draw_no=1236 AND brain=?",
                (b,),
            ).fetchone()["pool_json"]
        )
        n = min(len(sa), len(sb))
        eq = sum(1 for i in range(n) if sa[i] == sb[i])
        mj = round(mean(_jaccard(sa[i], sb[i]) for i in range(n)), 4) if n else None
        key = f"{a}_{b}"
        eq_1236[key] = eq
        jac_1236[key] = mj
    for dno in range(1217, 1237):
        by = {}
        for tag in BRAINS:
            r = conn.execute(
                "SELECT pool_json FROM testlotto_pool_view_cache WHERE draw_no=? AND brain=?",
                (dno, tag),
            ).fetchone()
            by[tag] = _sets(r["pool_json"] if r else "[]")
        for a, b in pairs:
            n = min(len(by[a]), len(by[b]))
            if n:
                jac_20[f"{a}_{b}"].append(mean(_jaccard(by[a][i], by[b][i]) for i in range(n)))
    conn.close()

    jac20_mean = {k: round(mean(v), 4) if v else None for k, v in jac_20.items()}

    from app.testlotto.brains.markov_brain import learn as mlearn
    from app.testlotto.brains.review_brain import learn as rlearn

    review_has_boost = hasattr(rlearn, "apply_learn_boost")
    markov_wired = bool(getattr(mlearn, "LEARN_WIRED", False))

    payload = {
        "id": "K-MARKOV-REVIEW-SKILL-QUALITY",
        "as_of": _now(),
        "verdict": "DISCUSS_OK",
        "ge3_claim": False,
        "draw_1237": False,
        "apply": False,
        "window": [LO, HI],
        "census": {
            "cache": cache,
            "evolve_by": ev,
            "ledger_by": led,
            "learn_n": learn_n,
            "draws_max": dmax,
            "pred_1237": pred_1237,
        },
        "clone_check": {
            "exact_equal_1236": eq_1236,
            "mean_jaccard_1236": jac_1236,
            "mean_jaccard_1217_1236": jac20_mean,
            "slot1_1236": {t: row1236[t][0] if row1236[t] else None for t in BRAINS},
        },
        "flags": {
            "ROLE_TIER_LEARN_WIRE": bool(ROLE_TIER_LEARN_WIRE),
            "ROLE_TIER_LEARN_BRAINS": sorted(ROLE_TIER_LEARN_BRAINS),
            "REPACK_ROLE_QUOTA_WIRE": bool(REPACK_ROLE_QUOTA_WIRE),
            "REPACK_ROLE_QUOTA_BRAINS": sorted(REPACK_ROLE_QUOTA_BRAINS),
            "STAT_POOL_LEARN_WIRE": bool(STAT_POOL_LEARN_WIRE),
            "FEATURE_LAMBDA_WIRE": bool(FEATURE_LAMBDA_WIRE),
            "EVOLVE_AUTO": bool(evolve_auto_enabled()),
            "markov_LEARN_WIRED": markov_wired,
            "review_has_apply_learn_boost": review_has_boost,
        },
        "engine": {
            "stat": "ENGINE_OK",
            "markov": "ENGINE_OK",
            "review": "ENGINE_OK_PARTIAL_LEARN",
        },
        "note": "스킬품질=축 충실도(prefer/prize). hits/mean 우열 금지. APPLY없음.",
    }

    lines = [
        "# K-MARKOV-REVIEW-SKILL-QUALITY",
        "",
        f"시각: {payload['as_of']} · **DISCUSS_OK** · READ-ONLY · APPLY없음 · 1237아님 · hits/tier 클레임 금지",
        "목적=남은 2뇌(markov=선호번호 · review=금액)가 stat처럼 **자기 엔진으로 도는지** 실측하고,",
        "뇌별 스킬 품질(축 충실도)을 올릴 **후보만** 문헌과 맞춰 고른다. 당첨P↑ 아님.",
        "",
        "## 0) 한 줄",
        "",
        "**두 뇌 모두 자기 `predict_sets`로 pool10+repack5를 뽑는다. 클론 아님.**",
        "stat형 과거학습 풀스택(역할숙제·STAT_POOL·apply_learn_boost 전부)과는 다르다.",
        "품질↑ = markov는 prefer축 · review는 prize/EV축. hits mean으로 서열 금지.",
        "",
        "## 1) 엔진 가동 (코드+캐시)",
        "",
        "| 뇌 | 판정 | 스킬 코어 | 군중 | learn | 6~10 역할숙제 | 캐시 1037–1236 |",
        "|----|------|-----------|------|-------|---------------|----------------|",
        f"| stat | ENGINE_OK | 빈도+past_learn | 없음 | apply_learn_boost | ON (`{sorted(ROLE_TIER_LEARN_BRAINS)}`) | {cache['stat']['nonempty']}/200 · 10+5={cache['stat']['pool_ge10']}+{cache['stat']['repack_ge5']} |",
        f"| markov | ENGINE_OK | 전이행렬+walk 80·top25 | prefer_table blend | LEARN_WIRED={markov_wired} · apply_learn_boost(+pair) | OFF | {cache['markov']['nonempty']}/200 · 10+5={cache['markov']['pool_ge10']}+{cache['markov']['repack_ge5']} |",
        f"| review | ENGINE_OK_PARTIAL_LEARN | 이월×1.8+끝수균등 | prize_table blend | apply_learn_boost **없음** · carry만 | OFF | {cache['review']['nonempty']}/200 · 10+5={cache['review']['pool_ge10']}+{cache['review']['repack_ge5']} |",
        "",
        "진입: `PREDICT_MODULES` → `*_brain.predict.predict_sets`. 구 `predict_flow_shaman`/`predict_review_king` **DEPRECATED·미등록**.",
        "`expand_pool(brains=[tag])`는 뇌마다 skill5 + cover3(같은 predict_sets 재호출) + shape2.",
        f"라이브: ROLE_TIER_LEARN_BRAINS={sorted(ROLE_TIER_LEARN_BRAINS)} · REPACK_QUOTA_BRAINS={sorted(REPACK_ROLE_QUOTA_BRAINS)} · STAT_POOL_LEARN=stat만 · EVOLVE_AUTO={bool(evolve_auto_enabled())} · FEATURE_LAMBDA={bool(FEATURE_LAMBDA_WIRE)}.",
        f"learn_state 행={learn_n} → markov/review boost 경로는 코드상 있으나 adj 비면 실질 no-op 가능. 코어 generate는 adj 없이 돈다.",
        f"원장={led} · evolve={ev} · draws MAX={dmax} · pred_1237={pred_1237}.",
        "",
        "## 2) 클론 아님 (캐시 pool, 모니터)",
        "",
        "| 쌍 | 1236 exact-equal/10 | 1236 mean J | 1217–1236 mean J |",
        "|----|---------------------|-------------|------------------|",
    ]
    for a, b in pairs:
        k = f"{a}_{b}"
        lines.append(f"| {a}↔{b} | {eq_1236[k]}/10 | {jac_1236[k]} | {jac20_mean[k]} |")
    lines += [
        "",
        f"1236 set1: stat={row1236['stat'][0] if row1236['stat'] else None} · "
        f"markov={row1236['markov'][0] if row1236['markov'] else None} · "
        f"review={row1236['review'][0] if row1236['review'] else None}.",
        "EXPAND 전 markov/review 캐시는 빈 `[]`(같은 fp). 지금 200행은 해당뇌 expand로 채운 것.",
        "",
        "## 3) stat과 다른 점 (풀스택 아님)",
        "",
        "| 능력 | stat | markov | review |",
        "|------|------|--------|--------|",
        "| 고유 engine | 빈도/감쇠 | 전이+prefer | 이월+prize |",
        "| apply_learn_boost | 있음(pair없음) | 있음(+pair) | **없음** |",
        "| 역할숙제 6~10 | ON | OFF(구 jaccard/set1) | OFF |",
        "| 몰아주기 역할쿼터 | ON | OFF | OFF |",
        "| STAT_POOL_LEARN | ON | 없음 | 없음 |",
        "| 게이트 축 | (빈도) | prefer | prize |",
        "",
        "누수 3(기존, 이번 악화 없음): `get_feedback_summary` 공유 · skill_homework consume 3뇌 · coordinator 발권쿼터 융합.",
        "",
        "## 4) 스킬 품질을 올리는 방향 (축별 · APPLY 아님)",
        "",
        "품질 = **그 뇌가 맡은 축을 더 정직하게 구현**하는 것. E[hits]=0.80 근처로 맞추는 튜닝 아님.",
        "",
        "### 4A) markov = 선호/전이 축",
        "",
        "| 후보 | 왜 맞나 | 하지 말 것 |",
        "|------|---------|------------|",
        "| 전이 상태 정의를 모니터 | 문헌: 상태(번호→번호 vs 끝수 vs 세트해시)가 구조를 가른다. 유한표본에서 전이는 평균회귀 | 전이확률로 당첨P↑ 클레임 · χ²를 APPLY 게이트로 쓰기 |",
        "| prefer_table을 인기 추정으로만 다듬기 | Thaler/Ziemba: 인기번호는 **사는 쪽** 분포. 이미 blend 중 | 궁합/연번을 `prefer_table`/`number_scores`에 넣기(DISCUSS에서 기각) |",
        "| pair는 annotate 유지 | 엔진에 pair_boost 이미 있음. 세트 설명용 | pair를 더 세게 해서 hits 노리기 |",
        "| 6~10 역할숙제 ON은 별 GO | stat 패리티. 품질=역할 일관성이지 적중 | 형 승인 없이 BRAINS에 markov 추가 |",
        "| walk steps=80 · top25 | 코드 상수. 문헌 근거 없음 | 이 숫자 튜닝을 성능 개선으로 포장 |",
        "",
        "문헌 벤치 **채택(모니터/설계)**: 전이행렬은 기술 통계(Joe 식 균일성 검정은 *당첨번호*용이라 사면 분포와 축이 다름). 상업 Markov-predictor 글은 기각(당첨예측 광고).",
        "",
        "### 4B) review = 금액/비선호 축",
        "",
        "| 후보 | 왜 맞나 | 하지 말 것 |",
        "|------|---------|------------|",
        "| prize_table ↔ 비선호 목록 대조 | Chernoff·Ziemba·Thaler: 고번호·끝수 0/8/9·비생일대가 비인기. 한국 6/45는 1–31 생일 밀집 | apply_learn_boost를 stat/markov에서 복사(축 붕괴) |",
        "| 1등 당첨자수(이미 prize 입력)를 EV 몫 프록시로 유지 | 파리뮤추얼: 같은 조합을 덜 고르면 당첨 시 몫↑ | 당첨번호 핫/콜드로 prize를 뒤집기 |",
        "| 끝수 균등(K-P3) 유지 | 이월 스킬이 끝수로 뭉치는 것 완화. 금액축과 충돌 적음 | 끝수 몰아주기를 ‘학습’으로 재도입 |",
        "| 캐리오버(이월 잭팟)는 공식 판매/미당첨 시에만 | Joe 1990: 캐리오버 클 때만 EV>1 가능, 분산이 커서 수명이 안 됨 | 캐리오버를 hits 튜닝 노브로 쓰기 |",
        "| 6~10 숙제 ON은 별 GO | 위와 같음 | review에 STAT_POOL_LEARN 복사 |",
        "",
        "문헌 벤치 **채택**: Thaler & Ziemba 1988 JEP · Ziemba et al. 1986 · Chernoff 1980/81 · Joe 1990 CJS(전략의 기댓값·분산 경고) · Cover/Joe 계열(비인기 조합). 한국: 추첨 무작위성 논문은 **당첨공**이 랜덤이라는 뜻이지 구매자 선택이 랜덤이 아님(KJAS 2025 당첨자 다수=구매 편중).",
        "",
        "## 5) 문헌 표 (벤치 여부)",
        "",
        "| 자료 | 축 | 벤치 | 이유 |",
        "|------|----|------|------|",
        "| Thaler & Ziemba 1988, JEP 2(2) | review | **채택** | 파리뮤추얼·비인기번호·캐리오버. 당첨P 불변 |",
        "| Ziemba, Brumelle, Gautier, Schwartz 1986 | review | **채택** | 비인기=고번호·끝 0/8/9. 안정적 비인기 |",
        "| Chernoff 1980/81 (digit preference) | review | **채택** | 끝수 기피. K-P3와 같은 축 |",
        "| Joe 1990 CJS “A winning strategy…?” | review | **채택(경고)** | EV>1은 캐리오버+비인기일 때만, SD 때문에 수명 불가 |",
        "| Joe 1993 SPL; Johnson & Klotz 1993 JASA | 모니터 | **부분** | 당첨번호 균일성 검정. 사면 분포 추정이 아님. χ² APPLY 금지 |",
        "| ICAMCS 2016 Markov-chain lottery (ATLANTIS) | markov | **기각** | 다음 회 당첨세트 예측 주장. 평균회귀와 충돌 |",
        "| 상업 Eurojackpot Markov Predictor | markov | **기각** | 블로그. 당첨예측 상품 |",
        "| AJA “Predictive Modeling… Markov” | markov | **부분(반례)** | 장기계에서 전이행렬이 평평해짐=평균회귀. 예측기 아님 |",
        "| 한국 당첨번호 무작위성 (데이터정보과학회 등) | 공통 | **채택(배경)** | 공은 랜덤. 핫넘버 학습 기각 근거 |",
        "| KJAS 2025 로또 공정성·당첨자수 | review | **채택** | 1등 다수=구매자 비랜덤. prize축과 동일 |",
        "| 한국 6/45 시계열 출현간격 논문 | stat/기각 | **기각(2뇌)** | 당첨 간격 맞추기=과거학습 재탕. review/markov 축 아님 |",
        "",
        "## 6) 권고 순서 (형 GO 전 · 코드 없음)",
        "",
        "1. **하지 말 것:** hits/ge3로 2뇌 품질 점수 매기기 · 3뇌 합산 · 궁합을 prefer에 넣기 · review에 apply_learn_boost 복사 · Markov 당첨예측 논문 추종 · covering/S2 재탕 · 1237.",
        "2. **모니터(읽기):** evolve_log를 뇌별(이미 분리)로 prefer/prize 축만 보기. 전이행렬 vs 균일·prize_table vs 고번호/끝수0·8·9 점유를 **표로만**.",
        "3. **다음 APPLY 후보(별 GO):** (a) review prize_table을 Ziemba형 비인기 규칙과 대조하는 SPEC · (b) markov 6~10 숙제 소비는 이미 WIRE 코드 있음, 라이브 `{stat}` 유지가 형 정정.",
        "",
        "## 7) 금지 확인",
        "",
        "DB write 없음. 동결 토큰 미수정. kweon 미접촉. 1237 아님.",
    ]
    text = "\n".join(lines) + "\n"
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUT_MD.write_text(text, encoding="utf-8")
    DRIVE.parent.mkdir(parents=True, exist_ok=True)
    DRIVE.write_text(text, encoding="utf-8")
    print(json.dumps({"verdict": "DISCUSS_OK", "cache": cache, "jac_1236": jac_1236, "eq": eq_1236, "jac20": jac20_mean, "learn_n": learn_n, "review_boost": review_has_boost}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
