"""10세트 pool + 신호 몰아주기(repack) — survey 도구와 UI 공용 (coordinator 미수정)."""

from __future__ import annotations

import random
from collections import Counter, defaultdict
from typing import Any

from app.testlotto.brains.registry import SETS_PER_PREDICT_BRAIN
from app.testlotto.data_service import _get_draws_before
from app.testlotto.learn_state_cutoff import set_learn_as_of

# bench_quick_gate / survey 와 동일 상수
MC_SEED = 42
POOL_SETS_PER_BRAIN = 10
REPACK_SETS_PER_BRAIN = 5
WINDOW_WEEKS = 4
WINDOW_SIGNAL = "zone_mix"
BRAIN_TAGS = ["markov", "stat", "review"]
LEARN_EMA = 0.15
W_HINT = 0.40
W_FREQ = 0.25
W_LEARN = 0.35

# K-REPACK-HYBRID-WIRE — ablation 20260804: stat/review hy_p45_r123 · markov baseline
# pool set 4+5 + score-몰아주기 rank1~3 → 발권 5장 (중복 시 rank4/5·다른 pool로 보충)
HYBRID_P45_R123_BRAINS: frozenset[str] = frozenset({"stat", "review"})
HYBRID_ASSEMBLE_MODE: str = "p45_r123"  # "" 이면 전원 baseline 몰아주기

# K-REPACK-SIGNAL-WIRE (20260808) — 설계 의도와 코드가 어긋난 배선 3건 수정.
# 성적 판정이 아니라 「설계대로 동작하게」 만드는 수정이므로 R38 게이트 대상이 아니다.
#   ① 성적표를 뇌별로 분리 — 이전에는 3뇌가 pos/num EMA 한 장을 공유해서
#      stat 의 3번 세트 성적에 markov·review 3번 세트 성적이 겹쳐 기록됐다.
#   ② pool 슬롯을 **신호 상위**로 선택 — 이전에는 set_no 4·5 하드코딩이라
#      신호가 0인 세트도 항상 뽑고 신호가 최고인 세트는 버렸다.
#   ③ 3뇌 동일 배선 — 이전에는 markov 만 pool 슬롯 0개여서 세트가 전부
#      번호로 녹았다. 제외 근거는 백테스트 ablation 뿐이었다.
# 통째 보존 슬롯 수(2)는 구 4·5 와 동수로 유지한다. 「몇 장을 보존할지」는
# 성적 주장이 필요한 튜닝이므로 이번 수정 범위에서 제외.
ASSEMBLE_MODE: str = "signal_top"  # "p45_r123"=구버전 · ""=전원 baseline
POOL_SLOTS_PER_BRAIN: int = 2
SIGNAL_TOP_BRAINS: frozenset[str] = frozenset(BRAIN_TAGS)

# K-BRAIN-INDEPENDENT (20260808) — 뇌별로 따로 정할 수 있게 구조만 열어둔다.
# K-BRAIN-INDEPENDENT-TUNE — 뇌별 점수축 분리 (축전용 지표 게이트 통과 후).
# ge3 미사용 · markov prefer↑ / review prize↓ / stat hit 비악화.
POOL_SLOTS_BY_BRAIN: dict[str, int] = dict.fromkeys(BRAIN_TAGS, POOL_SLOTS_PER_BRAIN)
SCORE_WEIGHTS_BY_BRAIN: dict[str, tuple[float, float, float]] = {
    "stat": (0.25, 0.35, 0.40),    # hint↓ freq/learn↑ — 과거패턴
    "markov": (0.55, 0.20, 0.25),  # hint↑ — 선호번호
    "review": (0.55, 0.20, 0.25),  # hint↑ — 금액뇌
}
LEARN_EMA_BY_BRAIN: dict[str, float] = dict.fromkeys(BRAIN_TAGS, LEARN_EMA)

# K-BRAIN-INDEPENDENT-WIRE (20260808) — hint 를 뇌 특성축으로 분리.
# 공유 허용 = lotto_draws(원본) + 읽기 헬퍼만. hint 테이블 공유 금지.
#   stat   → 과거 당첨 패턴(miss_pattern · 창26)
#   markov → 선호번호(crowd_prefer · first_winners 인기회차)
#   review → 금액뇌(crowd_prize · 비선호·저당첨자수)
# 기존 (WINDOW_WEEKS, WINDOW_SIGNAL) 단일 hint 는 `_build_hint` fallback 으로만 유지.
HINT_SPEC_BY_BRAIN: dict[str, tuple[int | None, str]] = {
    # K-STAT-PATTERN-TUNE APPLY: miss_pattern 창 26→52 (1137~1236·hit↑·iso OK)
    "stat": (52, "miss_pattern"),
    "markov": (None, "crowd_prefer"),
    "review": (None, "crowd_prize"),
}


def hint_shared_across_brains() -> bool:
    """3뇌가 같은 (창, 신호) 를 쓰고 있으면 True. 값을 다르게 두면 자동으로 False."""
    return len(set(HINT_SPEC_BY_BRAIN.values())) <= 1

# K-EVOLVE-FEAT-LAM-REVAL — full history에서 review λ0.3 기각 → OFF
FEATURE_LAMBDA_WIRE: bool = False


SignalTable = dict[str, dict[int, float]]


class RollingSignalLearner:
    """Walk-forward: target draw 이전 회차만으로 번호·세트위치 기여도 EMA.

    성적표는 **뇌별로 따로** 쌓는다 (K-REPACK-SIGNAL-WIRE ①). 한 장을 공유하면
    stat 3번 세트의 성적에 markov·review 3번 세트 성적이 겹쳐 기록되어,
    어느 뇌가 잘한 것인지 구별할 수 없다. 그러면 뇌를 개선해도 그 신호가
    몰아주기까지 전달되지 않는다.
    """

    def __init__(self) -> None:
        self.num_hit_ema: SignalTable = {t: self._new_num() for t in BRAIN_TAGS}
        self.pos_hit_ema: SignalTable = {t: self._new_pos() for t in BRAIN_TAGS}

    @staticmethod
    def _new_num() -> dict[int, float]:
        return dict.fromkeys(range(1, 46), 0.0)

    @staticmethod
    def _new_pos() -> dict[int, float]:
        return dict.fromkeys(range(1, POOL_SETS_PER_BRAIN + 1), 0.0)

    def snapshot(self) -> tuple[SignalTable, SignalTable]:
        """뇌 태그로 키를 잡은 중첩 표를 돌려준다."""
        return (
            {t: dict(v) for t, v in self.num_hit_ema.items()},
            {t: dict(v) for t, v in self.pos_hit_ema.items()},
        )

    def update_from_pool(
        self,
        pool_by_brain: dict[str, list[dict]],
        actual: set[int],
    ) -> None:
        for tag, pool in pool_by_brain.items():
            num_t = self.num_hit_ema.setdefault(tag, self._new_num())
            pos_t = self.pos_hit_ema.setdefault(tag, self._new_pos())
            a = LEARN_EMA_BY_BRAIN.get(tag, LEARN_EMA)
            for c in pool:
                sn = int(c.get("pred_set_no") or c.get("set_no") or 1)
                nums = [int(x) for x in c["nums"]]
                # 1개든 2개든 맞은 개수가 곧 신호 세기 (당첨 여부와 무관)
                mc = len(set(nums) & actual)
                if mc <= 0:
                    continue
                credit = mc / 6.0
                pos_t[sn] = (1 - a) * pos_t.get(sn, 0.0) + a * credit
                for n in nums:
                    if n in actual:
                        num_t[n] = (1 - a) * num_t.get(n, 0.0) + a * credit


def brain_signal(table: dict, brain_tag: str | None) -> dict[int, float]:
    """뇌별 중첩 성적표에서 한 뇌의 표를 꺼낸다. 구형 단일 표는 그대로 통과.

    `brain_tag=None` 으로 중첩 표를 넘기면 뇌를 합산한다 — 옛 도구 호환 경로이며
    **뇌 구분이 없다**. 새 코드는 반드시 brain_tag 를 넘길 것.
    """
    if not table:
        return {}
    if not isinstance(next(iter(table)), str):
        return table
    if brain_tag is not None:
        return dict(table.get(brain_tag) or {})
    merged: dict[int, float] = {}
    for per in table.values():
        for k, v in per.items():
            merged[k] = max(merged.get(k, 0.0), float(v))
    return merged


def _live_candidates(draws: list[dict], draw_no: int) -> list[dict]:
    """구버전 — 3뇌를 **한 난수 흐름으로** 순차 호출 (뇌 간 RNG 오염). 대조용."""
    from tools._k_window_signal_survey import _live_candidates as _lc

    return _lc(draws, draw_no)


def _pass_seed(seed: int, draw_no: int, pass_idx: int) -> int:
    """pass 별 시드. pass0 은 `coordinator._seed_independent_brain` 과 같은 규칙이라
    pool 1~5 세트가 실제 발권 경로가 만드는 5세트와 일치한다.
    """
    return int(seed) + int(draw_no) + pass_idx * 10000


def expand_pool(draws: list[dict], draw_no: int, *, seed: int = MC_SEED) -> list[dict]:
    """뇌별 10세트 pool = 뇌마다 2× predict_sets.

    K-BRAIN-RNG-INDEPENDENT (20260808) — **뇌마다 시드를 리셋한다.** 이전에는
    3뇌를 한 난수 흐름으로 순차 호출해서, 앞 뇌가 뽑기를 몇 번 하느냐에 따라
    뒤 뇌의 결과가 바뀌었다(stat → markov 오염). 발권 경로(`coordinator`)는
    이미 뇌마다 시드를 리셋하고 있었고 pool 경로만 빠져 있었다.
    """
    from tools._k_window_signal_survey import PREDICT_MODULES

    pool: list[dict] = []
    for pass_idx in range(2):
        s = _pass_seed(seed, draw_no, pass_idx)
        for tag in BRAIN_TAGS:
            mod = PREDICT_MODULES.get(tag)
            if mod is None:
                continue
            random.seed(s)  # 뇌마다 같은 시작점 → 서로 오염되지 않음
            for i, c in enumerate(mod.predict_sets(draws, SETS_PER_PREDICT_BRAIN)):
                base_sn = int(
                    c.get("rank") or c.get("set_no") or c.get("pred_set_no") or (i + 1)
                )
                sn = base_sn + pass_idx * SETS_PER_PREDICT_BRAIN
                pool.append({**c, "brain_tag": tag, "pred_set_no": sn, "set_no": sn})
    return pool


def _pool_by_brain(pool: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {t: [] for t in BRAIN_TAGS}
    for c in pool:
        tag = c.get("brain_tag", "")
        if tag in out:
            out[tag].append(c)
    return out


def _pool_freq(pool: list[dict]) -> dict[int, float]:
    cnt: Counter[int] = Counter()
    for c in pool:
        for n in c["nums"]:
            cnt[int(n)] += 1
    mx = max(cnt.values()) if cnt else 1
    return {n: cnt.get(n, 0) / mx for n in range(1, 46)}


def number_scores(
    pool: list[dict],
    hint: dict[int, float],
    num_ema: dict[int, float],
    pos_ema: dict[int, float],
    *,
    hint_only: bool = False,
    random_scores: bool = False,
    brain_tag: str | None = None,
) -> dict[int, float]:
    num_t = brain_signal(num_ema, brain_tag)
    pos_t = brain_signal(pos_ema, brain_tag)
    w_hint, w_freq, w_learn = SCORE_WEIGHTS_BY_BRAIN.get(
        brain_tag or "", (W_HINT, W_FREQ, W_LEARN)
    )
    freq = _pool_freq(pool)
    pos_boost: dict[int, float] = defaultdict(float)
    for c in pool:
        sn = int(c.get("pred_set_no") or 1)
        pw = pos_t.get(sn, 0.0)
        for n in c["nums"]:
            pos_boost[int(n)] = max(pos_boost[int(n)], pw)

    scores: dict[int, float] = {}
    for n in range(1, 46):
        if random_scores:
            scores[n] = random.random()
        elif hint_only:
            scores[n] = max(0.0, hint.get(n, 0.0))
        else:
            scores[n] = (
                w_hint * max(0.0, hint.get(n, 0.0))
                + w_freq * freq.get(n, 0.0)
                + w_learn * (num_t.get(n, 0.0) + 0.5 * pos_boost.get(n, 0.0))
            )
    return scores


def repack_sets(scores: dict[int, float], n_sets: int = REPACK_SETS_PER_BRAIN) -> list[list[int]]:
    ranked = sorted(range(1, 46), key=lambda x: (-scores[x], x))
    sets: list[list[int]] = []
    idx = 0
    for _ in range(n_sets):
        chunk = ranked[idx : idx + 6]
        idx += 6
        sets.append(sorted(chunk))
    return sets


def _nums_key(nums: list[int]) -> tuple[int, ...]:
    return tuple(sorted(int(x) for x in nums))


def _assemble(
    pool: list[dict],
    classic_repack: list[list[int]],
    primary_set_nos: tuple[int, ...],
    *,
    n_sets: int = REPACK_SETS_PER_BRAIN,
) -> list[dict]:
    """지정한 pool 세트를 통째로 보존 + 나머지는 점수몰아주기 rank 로 채움.

    Returns list of {nums, source, source_set_no} length ≤ n_sets.
    """
    p_by = {
        int(c.get("pred_set_no") or c.get("set_no") or 0): [int(x) for x in c["nums"]]
        for c in pool
    }
    n_rank = max(0, n_sets - len(primary_set_nos))
    primary: list[tuple[list[int], str, int]] = [
        (p_by[sn], "pool", sn) for sn in primary_set_nos if sn in p_by
    ]
    primary += [
        (list(nums), "score_repack", i + 1)
        for i, nums in enumerate(classic_repack[:n_rank])
    ]
    fillers: list[tuple[list[int], str, int]] = [
        (list(nums), "score_repack", i)
        for i, nums in enumerate(classic_repack[n_rank:], start=n_rank + 1)
    ]
    fillers += [
        (p_by[sn], "pool", sn) for sn in sorted(p_by) if sn not in primary_set_nos
    ]

    out: list[dict] = []
    seen: set[tuple[int, ...]] = set()
    for nums, src, ssn in primary + fillers:
        key = _nums_key(nums)
        if key in seen or len(nums) != 6:
            continue
        seen.add(key)
        out.append({"nums": sorted(nums), "source": src, "source_set_no": ssn})
        if len(out) >= n_sets:
            break
    return out


def assemble_hybrid_p45_r123(
    pool: list[dict],
    classic_repack: list[list[int]],
    *,
    n_sets: int = REPACK_SETS_PER_BRAIN,
) -> list[dict]:
    """구버전 — pool set_no **4·5 고정** + 점수몰아주기 rank1~3 (K-REPACK-HYBRID).

    4·5 는 백테스트 ablation 에서 나온 숫자이며 신호와 무관하다. 대조군으로만 유지.
    """
    return _assemble(pool, classic_repack, (4, 5), n_sets=n_sets)


def signal_top_set_nos(
    pool: list[dict],
    pos_ema: dict[int, float],
    *,
    n_slots: int = POOL_SLOTS_PER_BRAIN,
) -> tuple[int, ...]:
    """pool 세트를 신호(위치 EMA) 세기 순으로 세워 상위 n_slots 개 set_no.

    동점은 set_no 작은 쪽 (결정적). 신호가 전부 0 인 초기 회차에서는
    set_no 순서와 같아진다.
    """
    sns = {int(c.get("pred_set_no") or c.get("set_no") or 0) for c in pool}
    ranked = sorted(sns, key=lambda sn: (-float(pos_ema.get(sn, 0.0)), sn))
    return tuple(ranked[:n_slots])


def assemble_signal_top(
    pool: list[dict],
    classic_repack: list[list[int]],
    pos_ema: dict[int, float],
    *,
    n_slots: int = POOL_SLOTS_PER_BRAIN,
    n_sets: int = REPACK_SETS_PER_BRAIN,
) -> list[dict]:
    """K-REPACK-SIGNAL-WIRE ②③ — **신호 상위** pool 세트를 통째로 보존.

    구 `assemble_hybrid_p45_r123` 은 set_no 4·5 를 고정으로 집었으므로 신호가
    0 인 세트도 항상 발권하고 신호가 최고인 세트는 버렸다. 여기서는 위치 EMA
    상위 세트를 고른다 — 이것이 「신호가 강한 세트로 몰아준다」의 실제 구현이다.
    """
    tops = signal_top_set_nos(pool, pos_ema, n_slots=n_slots)
    return _assemble(pool, classic_repack, tops, n_sets=n_sets)


def _assembled_for_brain(
    tag: str,
    pool: list[dict],
    classic: list[list[int]],
    pos_t: dict[int, float],
) -> tuple[list[dict] | None, str]:
    """뇌별 조립 방식 선택. (조립결과, 라벨) — None 이면 baseline 점수몰아주기."""
    if ASSEMBLE_MODE == "signal_top" and tag in SIGNAL_TOP_BRAINS:
        n_slots = POOL_SLOTS_BY_BRAIN.get(tag, POOL_SLOTS_PER_BRAIN)
        return assemble_signal_top(pool, classic, pos_t, n_slots=n_slots), "signal_top"
    if ASSEMBLE_MODE == "p45_r123" and tag in HYBRID_P45_R123_BRAINS:
        return assemble_hybrid_p45_r123(pool, classic), "hy_p45_r123"
    return None, "baseline_repack"


def _rows_for_brain(
    tag: str,
    pool: list[dict],
    classic: list[list[int]],
    pos_t: dict[int, float],
) -> list[dict]:
    assembled, label = _assembled_for_brain(tag, pool, classic, pos_t)
    rows: list[dict] = []
    items: list[dict] = (
        assembled
        if assembled is not None
        else [{"nums": nums, "source": "score_repack", "source_set_no": i + 1}
              for i, nums in enumerate(classic)]
    )
    for i, item in enumerate(items):
        row = {
            "nums": item["nums"],
            "brain_tag": tag,
            "pred_set_no": i + 1,
            "set_no": i + 1,
            "repack_rank": i + 1,
            "kind": "repack",
            "assemble": label,
        }
        if assembled is not None:
            row["source"] = item["source"]
            row["source_set_no"] = item["source_set_no"]
        rows.append(row)
    return rows


def repack_by_brain(
    pool_by_brain: dict[str, list[dict]],
    hint: dict[int, float],
    num_ema: dict[int, float],
    pos_ema: dict[int, float],
    *,
    hint_only: bool = False,
    random_repack: bool = False,
    target_draw_no: int | None = None,
    hint_by_brain: dict[str, dict[int, float]] | None = None,
) -> list[dict]:
    """뇌별 몰아주기.

    `hint_by_brain` 을 안 주더라도 `HINT_SPEC_BY_BRAIN` 이 뇌마다 다르면 여기서 직접
    만든다. 호출자가 넘기는 걸 잊어도 뇌별 hint 가 조용히 무시되지 않게 하려는 것이다
    (`brain_tag` 를 빠뜨려 뇌별 가중치가 죽었던 K-REPACK-BRAINTAG-DEAD-WIRE 와 같은 함정).
    """
    from app.testlotto.feature_lambda import FEATURE_LAMBDA_BY_BRAIN, apply_feature_lambda

    if hint_by_brain is None and target_draw_no is not None and not hint_shared_across_brains():
        hint_by_brain = build_hint_by_brain(_get_draws_before(target_draw_no), target_draw_no)

    out: list[dict] = []
    for tag in BRAIN_TAGS:
        pool = pool_by_brain.get(tag, [])
        if not pool:
            continue
        h = (hint_by_brain or {}).get(tag, hint)
        pos_t = brain_signal(pos_ema, tag)
        # brain_tag 필수 — 빠뜨리면 SCORE_WEIGHTS_BY_BRAIN 이 조회되지 않아
        # 뇌별 가중치가 조용히 무시된다 (K-REPACK-BRAINTAG-DEAD-WIRE)
        scores = number_scores(
            pool,
            h,
            num_ema,
            pos_ema,
            hint_only=hint_only,
            random_scores=random_repack,
            brain_tag=tag,
        )
        classic = repack_sets(scores)
        assembled_rows = _rows_for_brain(tag, pool, classic, pos_t)

        if (
            FEATURE_LAMBDA_WIRE
            and target_draw_no is not None
            and tag in FEATURE_LAMBDA_BY_BRAIN
        ):
            lam_rows = apply_feature_lambda(
                tag, pool, assembled_rows, int(target_draw_no)
            )
            if lam_rows:
                out.extend(lam_rows)
                continue
        out.extend(assembled_rows)
    return out


def _weights_to_hint(table: dict[int, float]) -> dict[int, float]:
    """군중 가중(평균≈1) → number_scores용 hint(-1..1, 양수만 점수 반영)."""
    from tools._k_window_signal_survey import _normalize_hint

    raw = {n: float(table.get(n, 1.0)) - 1.0 for n in range(1, 46)}
    return _normalize_hint(raw)


def _build_hint_for_spec(
    draws: list[dict], weeks: int | None, signal: str, draw_no: int
) -> dict[int, float]:
    """단일 (창, 신호) hint. crowd_* 는 lotto_draws 기반 군중표 → hint 변환."""
    if signal == "crowd_prefer":
        from app.testlotto.brains.shared import crowd_signal

        return _weights_to_hint(crowd_signal.prefer_table(draws, brain="markov"))
    if signal == "crowd_prize":
        from app.testlotto.brains.shared import crowd_signal

        return _weights_to_hint(crowd_signal.prize_table(draws, brain="review"))
    from tools._k_window_signal_survey import _build_hint as _bh

    return _bh(draws, weeks, signal, draw_no)


def _build_hint(draws: list[dict], draw_no: int) -> dict[int, float]:
    """공유 fallback (구경로 호환). 뇌별 분리는 `build_hint_by_brain`."""
    return _build_hint_for_spec(draws, WINDOW_WEEKS, WINDOW_SIGNAL, draw_no)


def build_hint_by_brain(draws: list[dict], draw_no: int) -> dict[str, dict[int, float]]:
    """뇌별 hint. `HINT_SPEC_BY_BRAIN` 이 다르면 테이블이 갈라진다."""
    cache: dict[tuple[int | None, str], dict[int, float]] = {}
    out: dict[str, dict[int, float]] = {}
    for tag in BRAIN_TAGS:
        spec = HINT_SPEC_BY_BRAIN.get(tag, (WINDOW_WEEKS, WINDOW_SIGNAL))
        if spec not in cache:
            cache[spec] = _build_hint_for_spec(draws, spec[0], spec[1], draw_no)
        out[tag] = dict(cache[spec])
    return out


def warm_learner_to_draw(
    learner: RollingSignalLearner,
    draw_start: int,
    before_draw: int,
    *,
    seed: int = MC_SEED,
) -> None:
    """draw_start .. before_draw-1 까지 WF로 learner EMA 갱신 (컨닝 없음)."""
    from app.testlotto.models import get_lotto_db

    if before_draw <= draw_start:
        return
    conn = get_lotto_db()
    try:
        rows = conn.execute(
            "SELECT * FROM lotto_draws WHERE draw_no >= ? AND draw_no < ? ORDER BY draw_no",
            (draw_start, before_draw),
        ).fetchall()
    finally:
        conn.close()

    for row in rows:
        row = dict(row)
        dno = int(row["draw_no"])
        actual = {int(row[f"num{k}"]) for k in range(1, 7)}
        set_learn_as_of(dno)
        draws = _get_draws_before(dno)
        if not draws:
            continue
        random.seed(seed)
        pool = expand_pool(draws, dno, seed=seed)
        pool_br = _pool_by_brain(pool)
        learner.update_from_pool(pool_br, actual)


def build_pool_and_repack(
    target_draw_no: int,
    *,
    seed: int = MC_SEED,
    learner_warm_start: int | None = None,
) -> dict[str, Any]:
    """단일 회차 10세트 pool + 5 몰아주기 세트 (뇌별). walk-forward only."""
    set_learn_as_of(target_draw_no)
    draws = _get_draws_before(target_draw_no)
    if not draws:
        return {"ok": False, "error": f"{target_draw_no}회 이전 데이터 없음"}

    warm_from = learner_warm_start if learner_warm_start is not None else max(1, target_draw_no - 200)
    learner = RollingSignalLearner()
    warm_learner_to_draw(learner, warm_from, target_draw_no, seed=seed)
    num_ema, pos_ema = learner.snapshot()

    random.seed(seed)
    pool = expand_pool(draws, target_draw_no, seed=seed)
    pool_br = _pool_by_brain(pool)
    hint = _build_hint(draws, target_draw_no)
    repacked = repack_by_brain(
        pool_br,
        hint,
        num_ema,
        pos_ema,
        target_draw_no=target_draw_no,
        hint_by_brain=build_hint_by_brain(draws, target_draw_no),
    )

    by_brain_pool: dict[str, list[dict]] = {}
    for tag in BRAIN_TAGS:
        sets = sorted(pool_br.get(tag, []), key=lambda x: int(x.get("pred_set_no") or 0))
        by_brain_pool[tag] = [
            {
                "set_no": int(c.get("pred_set_no") or c.get("set_no") or 1),
                "nums": [int(x) for x in c["nums"]],
                "brain_tag": tag,
                "kind": "pool",
            }
            for c in sets
        ]

    by_brain_repack: dict[str, list[dict]] = {t: [] for t in BRAIN_TAGS}
    for c in repacked:
        tag = str(c["brain_tag"])
        entry: dict[str, Any] = {
            "set_no": int(c.get("repack_rank") or c.get("set_no") or 1),
            "nums": [int(x) for x in c["nums"]],
            "brain_tag": tag,
            "kind": "repack",
            "assemble": c.get("assemble") or "baseline_repack",
        }
        if c.get("source"):
            entry["source"] = c["source"]
            entry["source_set_no"] = c.get("source_set_no")
        by_brain_repack.setdefault(tag, []).append(entry)

    # K-RARE-FILTER 삽입점 (WIRE OFF · 호출 금지):
    #   from app.testlotto.rare_annotate import RARE_ANNOTATE_WIRE, annotate_sets, policy_filter
    #   if RARE_ANNOTATE_WIRE:  # 형 GO 후에만
    #       for tag in BRAIN_TAGS:
    #           by_brain_pool[tag] = annotate_sets(by_brain_pool[tag])
    #           by_brain_repack[tag] = policy_filter(annotate_sets(by_brain_repack[tag]))
    # 기본: pass-through (발권 불변)

    return {
        "ok": True,
        "target_draw_no": target_draw_no,
        "no_peek": True,
        "pool_sets_per_brain": POOL_SETS_PER_BRAIN,
        "repack_sets_per_brain": REPACK_SETS_PER_BRAIN,
        "seed": seed,
        "window_hint": {
            "weeks": WINDOW_WEEKS,
            "signal": WINDOW_SIGNAL,
            "by_brain": {t: list(v) for t, v in HINT_SPEC_BY_BRAIN.items()},
            "shared_across_brains": hint_shared_across_brains(),
        },
        "hybrid": _assemble_meta(),
        "feature_lambda": _feature_lambda_meta(),
        "pool_by_brain": by_brain_pool,
        "repack_by_brain": by_brain_repack,
    }


def _assemble_meta() -> dict[str, Any]:
    """실제 조립 배선을 그대로 보고. 상수를 바꾸면 이 값도 따라 바뀐다."""
    if ASSEMBLE_MODE == "signal_top":
        return {
            "mode": "signal_top",
            "brains": sorted(SIGNAL_TOP_BRAINS),
            "pool_slots_by_brain": dict(POOL_SLOTS_BY_BRAIN),
            "pool_slot_rule": "위치 EMA 상위 (뇌별 성적표)",
            "rng_independent": True,
            "hint_shared_across_brains": hint_shared_across_brains(),
            "hint_spec_by_brain": {t: list(v) for t, v in HINT_SPEC_BY_BRAIN.items()},
        }
    if ASSEMBLE_MODE == "p45_r123":
        return {
            "mode": "p45_r123",
            "brains": sorted(HYBRID_P45_R123_BRAINS),
            "pool_slots_per_brain": 2,
            "pool_slot_rule": "set_no 4·5 고정 (구버전)",
        }
    return {"mode": "baseline_repack", "brains": [], "pool_slots_per_brain": 0}


def _feature_lambda_meta() -> dict[str, Any]:
    from app.testlotto.feature_lambda import FEATURE_LAMBDA_BY_BRAIN

    return {"wired": FEATURE_LAMBDA_WIRE, "by_brain": dict(FEATURE_LAMBDA_BY_BRAIN)}
