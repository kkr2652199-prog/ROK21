# -*- coding: utf-8 -*-
"""4군 v13·전략X 뇌 제품 삭제 플래그.

테스트로또/효도/combinadic/전체조합/데이터수집과 독립.
롤백: ARMY4_SX_BRAINS_REMOVED=False.
"""

ARMY4_SX_BRAINS_REMOVED = True
REMOVED_MSG = "4군·전략X 뇌는 삭제됨. 테스트로또와 독립."


def removed_response() -> dict:
    return {
        "ok": False,
        "removed": True,
        "error": "army4_sx_brains_removed",
        "message": REMOVED_MSG,
    }
