"""Small statistics helpers: log-linear growth fits with bootstrap intervals."""

import math

import numpy as np


def doubling_time(years, flop):
    """Doubling time in months from an OLS fit of log2(FLOP) on decimal year."""
    years = np.asarray(years, dtype=float)
    log2 = np.log2(np.asarray(flop, dtype=float))
    slope = np.polyfit(years, log2, 1)[0]
    return 12 / slope if slope > 1e-9 else math.inf


def fit(years, flop, reps=2000, seed=0):
    """Doubling time (months) with a percentile bootstrap 95% interval over models."""
    years = np.asarray(years, dtype=float)
    flop = np.asarray(flop, dtype=float)
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(reps):
        pick = rng.integers(0, len(years), len(years))
        if np.ptp(years[pick]) > 0:
            draws.append(doubling_time(years[pick], flop[pick]))
    low, high = np.percentile(draws, [2.5, 97.5])
    return {
        "n": int(len(years)),
        "doubling_months": float(doubling_time(years, flop)),
        "ci_low": float(low),
        "ci_high": float(high),
        "growth_per_year": float(2 ** (12 / doubling_time(years, flop))),
    }
