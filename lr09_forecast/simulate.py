"""LR9 reproducible Monte Carlo. Reference data are educational, not our velocity."""
import csv
import json
import math
import random
from pathlib import Path

RUNS = 10000
SEED = 20261028
REFERENCE = [21, 17, 26, 14, 23, 6, 28, 12, 22, 25, 18, 9]


def simulate(points, velocity, runs=RUNS, seed=SEED):
    if points < 0 or runs < 1000 or not velocity or any(v < 0 for v in velocity):
        raise ValueError("Invalid points, runs or velocity")
    if points > 0 and max(velocity) == 0:
        raise ValueError("No finite forecast: every observed velocity is zero")
    rng = random.Random(seed)
    results = []
    for _ in range(runs):
        remaining, sprints = points, 0
        while remaining > 0:
            remaining -= rng.choice(velocity)
            sprints += 1
        results.append(sprints)
    results.sort()
    # Nearest-rank empirical quantiles; integer sprint counts, no interpolation.
    p50 = results[math.ceil(0.50 * runs) - 1]
    p85 = results[math.ceil(0.85 * runs) - 1]
    return {"p50": p50, "p85": p85, "width": p85 - p50}


def self_check():
    assert simulate(0, [0]) == {"p50": 0, "p85": 0, "width": 0}
    assert simulate(40, [20])["p50"] == 2  # exact boundary
    assert simulate(41, [20])["p85"] == 3
    mixed = simulate(20, [0, 20])
    assert mixed["p85"] >= mixed["p50"] >= 1
    try:
        simulate(1, [0, 0])
    except ValueError:
        pass
    else:
        raise AssertionError("All-zero history must not loop forever")


def own_forecasts(root):
    from datetime import date, timedelta
    def rows(path):
        with (root / path).open(encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    rel1 = {r["story_id"] for r in rows("lr06_backlog/backlog.csv") if r["release"] == "REL-1"}
    estimates = {r["story_id"]: int(r["final_estimate"]) for r in rows("lr08_poker/estimates.csv")}
    history = rows("lr09_forecast/velocity.csv")
    assert len(history) >= 2 and rel1 <= estimates.keys()
    # Accepted IDs are evidence-based, not inferred from the number of SP.
    accepted = {"S-01"}  # review 2026-10-30, issue #13, sprints.md
    assert sum(int(r["points_done"]) for r in history) == sum(estimates[s] for s in accepted)
    velocity = [int(r["points_done"]) for r in history]
    whole = sum(estimates[s] for s in rel1)
    remaining = sum(estimates[s] for s in rel1 - accepted)
    output = []
    for label, points, anchor, offset in [
        ("Весь перший реліз", whole, history[0]["end_date"], -1),
        ("Залишок після двох спринтів", remaining, history[-1]["end_date"], 0),
    ]:
        result = simulate(points, velocity)
        output.append({"scenario": label, "remaining_points": points, "simulations": RUNS,
                       "p50_sprints": result["p50"], "p85_sprints": result["p85"],
                       "p50_date": (date.fromisoformat(anchor)+timedelta(days=(result["p50"]+offset)*14)).isoformat(),
                       "p85_date": (date.fromisoformat(anchor)+timedelta(days=(result["p85"]+offset)*14)).isoformat()})
    return output


if __name__ == "__main__":
    self_check()
    root = Path(__file__).resolve().parents[1]
    own = own_forecasts(root)
    with (root / "lr09_forecast/forecast.csv").open(encoding="utf-8-sig", newline="") as f:
        saved = list(csv.DictReader(f))
    assert saved == [{k: str(v) for k,v in row.items()} for row in own], "Saved forecast differs from calculation"
    print(json.dumps({"runs": RUNS, "seed": SEED,
        "reference_all_12": simulate(220, REFERENCE),
        "reference_1_2": simulate(220, REFERENCE[:2]),
        "reference_5_6": simulate(220, REFERENCE[4:6]),
        "own_forecast": own,
        "limitation": "Second sprint is 3 elapsed days; 14-day projection is conditional, not a reliable calendar promise."
    }, ensure_ascii=False, indent=2))
