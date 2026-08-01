import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.testlotto.brains.coordinator import run_coordinated_prediction
from app.testlotto.brains.shared.pattern_signal import get_pattern_signal, make_signal_draws
from app.testlotto.data_service import _get_draws_before

active = 0
for draw_no in range(1225, 1235):
    draws = _get_draws_before(draw_no)
    sig = get_pattern_signal(draws)
    vd = make_signal_draws(sig, int(draws[-1]["draw_no"]) if draws else 0)
    if vd:
        active += 1
    result = run_coordinated_prediction(draw_no)
    if "error" in result:
        raise RuntimeError(f"draw {draw_no}: {result['error']}")
    print(f"draw {draw_no}: OK virtual={len(vd)}")

print(f"SMOKE PASS 1225-1234 · virtual_draws_active={active}/10")
