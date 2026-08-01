"""shared.db_facts — draws 기반 파생 통계 (Phase1 이전).

번호 빈도·pair 빈도·gap·carry 후보 등 DB/draws 공통 fact 추출.
각 brain engine·aux hint 입력용 — 컨닝 방지 cutoff는 호출측 책임.
"""


def get_number_freq(draws: list[dict]) -> dict[int, float]:
    """각 번호(1~45) 출현 빈도(정규화 비율)를 반환한다."""
    raise NotImplementedError


def get_pair_freq(draws: list[dict]) -> dict[tuple, int]:
    """번호 쌍 (a, b) 동시 출현 횟수를 반환한다. a < b 정렬 키."""
    raise NotImplementedError


def get_gap_map(draws: list[dict]) -> dict[int, int]:
    """각 번호의 최근 미출현 회차(gap)를 반환한다."""
    raise NotImplementedError


def get_carry_candidates(draws: list[dict]) -> list[int]:
    """직전 회차 당첨번호 중 이월(carry-over) 후보 번호 목록을 반환한다."""
    raise NotImplementedError
