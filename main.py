#!/usr/bin/env python3
"""Forecast Polymarket "Next CEO of NVIDIA?" Yes prices, 240 minutes ahead.

For every market of a case, write five quantiles (5%, 25%, 50%, 75%, 95%)
of its Yes price at each of the 240 minutes after the case's checkpoint.

Model: the median is the persistence forecast -- the price at the
checkpoint -- because these prices sit still for long stretches and their
recent drift does not persist. The spread around it widens more slowly
than a random walk (h ** 0.4, fitted on the practice cases: the prices
are bounded and jump-driven, so variance grows sub-linearly), scaled by
the market's own recent volatility: the root-mean-square of its one-minute
changes over the last VOL_WINDOW minutes, shrunk toward the house
baseline's flat 0.0025 per root minute, then globally calibrated.

Standard library only, no network, fully deterministic: the same case
always produces the same bytes.
"""

import json
import math
import os

QUANTILES = [0.05, 0.25, 0.5, 0.75, 0.95]
# The standard normal's quantile at each level, to 6 decimals.
Z = [-1.644854, -0.674490, 0.0, 0.674490, 1.644854]

BASE_SIGMA = 0.0025    # the house baseline's spread per root minute
VOL_WINDOW = 120       # minutes of history behind the volatility estimate
VOL_SHRINK = 0.8       # weight on the market's own estimate vs BASE_SIGMA
SIGMA_CAP = 0.0075     # a just-happened spike must not blow the spread up
SPREAD_MULT = 0.85     # global spread calibration, fitted on the practice
HORIZON_POWER = 0.4    # the spread grows like h ** HORIZON_POWER
TAIL_MULT = 1.15       # the outer quantiles sit wider than the normal's
INNER_MULT = 0.85      # the inner quantiles sit narrower than the normal's
Z_EFF = [Z[0] * TAIL_MULT, Z[1] * INNER_MULT, 0.0,
         Z[3] * INNER_MULT, Z[4] * TAIL_MULT]


def price6(value):
    """Clamp to [0, 1] and round to 6 decimals (never -0.0)."""
    return round(min(1.0, max(0.0, value)) * 1e6) / 1e6 + 0.0


def market_sigma(prices):
    """Per-root-minute volatility from the recent one-minute changes."""
    window = prices[-VOL_WINDOW - 1:] if len(prices) > VOL_WINDOW else prices
    if len(window) < 2:
        return BASE_SIGMA
    sq = 0.0
    for i in range(len(window) - 1):
        d = window[i + 1] - window[i]
        sq += d * d
    own = math.sqrt(sq / (len(window) - 1))
    est = VOL_SHRINK * own + (1.0 - VOL_SHRINK) * BASE_SIGMA
    return min(SIGMA_CAP, est)


def forecast(prices, horizon):
    """240 rows of five quantiles for one market."""
    x = prices[-1] if prices else 0.0
    sigma = market_sigma(prices) if prices else BASE_SIGMA
    rows = []
    for h in range(1, horizon + 1):
        spread = SPREAD_MULT * sigma * (h ** HORIZON_POWER)
        row = [price6(x + z * spread) for z in Z_EFF]
        for j in range(1, len(row)):  # rounding must not break the order
            if row[j] < row[j - 1]:
                row[j] = row[j - 1]
        rows.append(row)
    return rows


def main():
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR", "/input")
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(output_dir, exist_ok=True)
    # Every case file, in name order, so two runs write the same bytes.
    names = sorted(n for n in os.listdir(input_dir) if n.endswith(".in"))
    for name in names:
        with open(os.path.join(input_dir, name), encoding="utf-8") as fh:
            case = json.load(fh)
        if [float(q) for q in case["quantiles"]] != QUANTILES:
            raise ValueError("%s asks for quantiles %r" % (name, case["quantiles"]))
        horizon = int(case["horizon_minutes"])
        forecasts = [
            {"id": m["id"], "q": forecast(m["prices"], horizon)}
            for m in case["markets"]
        ]
        out = os.path.join(output_dir, name[:-3] + ".out")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"forecasts": forecasts}, separators=(",", ":")))
            fh.write("\n")


if __name__ == "__main__":
    main()
