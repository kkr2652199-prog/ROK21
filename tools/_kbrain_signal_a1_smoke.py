import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.testlotto.brains.coordinator import run_coordinated_prediction

for draw_no in range(1225, 1235):
    result = run_coordinated_prediction(draw_no)
    if "error" in result:
        raise RuntimeError(f"draw {draw_no}: {result['error']}")
    print(f"draw {draw_no}: OK status={result.get('status', '?')}")
print("SMOKE PASS 1225-1234")
