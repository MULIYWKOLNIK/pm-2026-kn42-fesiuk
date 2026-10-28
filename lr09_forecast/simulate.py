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


if __name__ == "__main__":
    self_check()
    root = Path(__file__).resolve().parents[1]
    with (root / "lr06_backlog/backlog.csv").open(encoding="utf-8-sig", newline="") as f:
        rel1 = {r["story_id"] for r in csv.DictReader(f) if r["release"] == "REL-1"}
    with (root / "lr08_poker/estimates.csv").open(encoding="utf-8-sig", newline="") as f:
        estimates = {r["story_id"]: int(r["final_estimate"]) for r in csv.DictReader(f)}
    assert rel1 <= estimates.keys(), "Missing REL-1 estimates"
    print(json.dumps({
        "runs": RUNS, "seed": SEED, "reference_points": 220,
        "reference_all_12": simulate(220, REFERENCE),
        "reference_1_2": simulate(220, REFERENCE[:2]),
        "reference_5_6": simulate(220, REFERENCE[4:6]),
        "our_rel1_points": sum(estimates[s] for s in rel1),
        "sprint1_committed_reconciled": sum(estimates[s] for s in ["S-01", "S-03", "S-04"]),
        "sprint2_current_committed": estimates["S-01"],
        "own_forecast": "pending second closed sprint; reference data are not substituted"
    }, indent=2))
