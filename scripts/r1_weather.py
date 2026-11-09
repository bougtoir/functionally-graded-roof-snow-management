"""Summarise the continuous-time synthetic winters used in R1."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

sys.path.insert(0, "src")
from graded_roof.forcing_v2 import (  # noqa: E402
    REFERENCE_DT_HOURS,
    continuous_synthetic_weather,
    snowfall_rate_kg_m2_h,
    temperature_c,
)

OUT = Path("results/r1/weather")


def summary(cfg: dict, dt_hours: float = 1.0) -> pd.DataFrame:
    s = cfg["synthetic_weather"]
    dur = s["duration_h"]
    t = np.arange(0.0, dur, REFERENCE_DT_HOURS)
    rows = []
    for sc in s["scenarios"]:
        w = continuous_synthetic_weather(sc, duration_h=dur, dt_hours=dt_hours)
        temp = temperature_c(t, sc)
        rows.append(
            {
                "scenario": sc["name"],
                "duration_h": dur,
                "snowfall_we_kg_m2": float(w.snowfall_kg_m2.sum()),
                "rain_mm": float(w.rain_mm.sum()),
                "total_precip_mm": float(w.snowfall_kg_m2.sum() + w.rain_mm.sum()),
                "t_min_c": float(w.temperature_c.min()),
                "t_mean_c": float(w.temperature_c.mean()),
                "t_max_c": float(w.temperature_c.max()),
                "hours_above_0c": float((w.temperature_c > 0).sum() * dt_hours),
                "peak_snowfall_kg_m2_h": float(w.snowfall_kg_m2.max() / dt_hours),
                "peak_snowfall_rate_continuous_kg_m2_h": float(
                    snowfall_rate_kg_m2_h(t, sc, dur).max()
                ),
                "t_min_c_continuous": float(temp.min()),
                "t_max_c_continuous": float(temp.max()),
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "synthetic_summary.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    df = summary(yaml.safe_load(open("config/production.yaml")))
    df.to_csv(out, index=False)
    print(df.round(3).to_string())
