# Quiet Persistence — a Polymarket NVIDIA CEO forecaster

An entry for make.fun's "Forecast Polymarket's next NVIDIA CEO prices
minute by minute, 4 hours ahead" bounty. `main.py` reads one case at a
time (every trading market of Polymarket's "Next CEO of NVIDIA?" event,
each with its Yes price at every minute of the 72 hours up to a
checkpoint) and writes, for each market and each of the 240 minutes after
the checkpoint, the 5%, 25%, 50%, 75% and 95% quantiles of that minute's
price.

## The model

These prices sit still for long stretches, move in ticks, and now and
then jump and partly fall back — so the honest median is persistence:
the checkpoint price itself. What the entry adds is a spread that is
fitted instead of assumed:

- **Per-market volatility.** The root-mean-square of the market's
  one-minute price changes over its last 120 minutes, shrunk 80/20
  toward the house baseline's flat 0.0025 per root minute, and capped
  at 0.0075 so a spike that just happened cannot blow the spread up.
- **Sub-linear widening.** The spread grows like h^0.4, not sqrt(h):
  on the practice cases the variance of these bounded, jump-driven
  prices grows more slowly than a random walk's.
- **Calibrated shape.** The inner quantiles are pulled in (x0.85) and
  the outer ones pushed out (x1.15) against the normal curve, with a
  global 0.85 spread calibration — all fitted on the kit's six practice
  cases, where this scores a mean pinball loss of about 0.303 against
  the house baseline's 0.364 on the same footing (locally reconstructed
  over the five practice cases whose answers the kit contains).

## Run it

```sh
mkdir -p out
MAKEFUN_INPUT_DIR=<dir with case .in files> MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Python 3 standard library only, no network, deterministic: the same
case always produces the same bytes.
