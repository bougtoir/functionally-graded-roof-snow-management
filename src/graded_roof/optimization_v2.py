"""Constructability-constrained optimisation for the R1 revision.

Every candidate is decoded into a *constructable* roof by a feasible
encoding, so all evaluated designs satisfy, by construction:

* piecewise-constant segments of at least ``min_segment_cells`` cells;
* at most ``max_transitions`` segment boundaries;
* integer-degree slopes in ``[slope_min, slope_max]``;
* adjacent slope change no larger than ``adjacent_slope_limit_deg``;
* surface properties taken only from the discrete manufacturable classes.

Modes: ``geometry`` (graded slope, one surface class for the whole roof),
``surface`` (one slope, graded classes) and ``joint`` (both).  Uniform roofs
are evaluated exhaustively over the same constructable set.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.termination import get_termination

from graded_roof.forcing_v2 import continuous_synthetic_weather
from graded_roof.models import RoofDesign, SimulationConfig, WeatherSeries
from graded_roof.simulation_v2 import EventSpec, simulate_v2


@dataclass(frozen=True)
class Constructability:
    cells: int = 24
    length_m: float = 8.0
    slope_min: int = 2
    slope_max: int = 45
    adjacent_slope_limit_deg: int = 12
    min_segment_cells: int = 3
    max_transitions: int = 6
    classes: tuple[tuple[str, float, float, float], ...] = ()

    @property
    def max_segments(self) -> int:
        return min(self.max_transitions + 1, self.cells // self.min_segment_cells)


def constructability_from_config(config: dict) -> Constructability:
    roof = config["roof"]
    classes = tuple(
        (name, v["mu_static"], v["mu_kinetic"], v["adhesion_pa"])
        for name, v in config["surface"]["discrete_classes"].items()
    )
    return Constructability(
        cells=roof["cells"],
        length_m=roof["length_m"],
        slope_min=int(roof["slope_bounds_deg"][0]),
        slope_max=int(roof["slope_bounds_deg"][1]),
        adjacent_slope_limit_deg=int(roof["adjacent_slope_limit_deg"]),
        min_segment_cells=roof["minimum_segment_cells"],
        max_transitions=roof["maximum_transitions"],
        classes=classes,
    )


def n_variables(mode: str, c: Constructability) -> int:
    k = c.max_segments
    slope_vars = k if mode in {"geometry", "joint"} else 1
    class_vars = k if mode in {"surface", "joint"} else 1
    return 1 + k + slope_vars + class_vars


def decode(u: np.ndarray, mode: str, c: Constructability) -> dict:
    """Map ``u`` in [0, 1]^n to a constructable segment description."""
    u = np.clip(np.asarray(u, dtype=float), 0.0, 1.0 - 1e-12)
    k = c.max_segments
    n_seg = 1 + int(u[0] * k)
    weights = u[1 : 1 + n_seg] + 1e-9
    spare = c.cells - c.min_segment_cells * n_seg
    raw = weights / weights.sum() * spare
    extra = np.floor(raw).astype(int)
    remainder = spare - extra.sum()
    extra[np.argsort(-(raw - extra), kind="stable")[:remainder]] += 1
    lengths = c.min_segment_cells + extra
    pos = 1 + k
    span = c.slope_max - c.slope_min
    if mode in {"geometry", "joint"}:
        s = u[pos : pos + n_seg]
        slopes = [c.slope_min + int(round(s[0] * span))]
        lim = c.adjacent_slope_limit_deg
        for value in s[1:]:
            step = int(np.floor(value * (2 * lim + 1))) - lim
            slopes.append(int(np.clip(slopes[-1] + step, c.slope_min, c.slope_max)))
        pos += k
    else:
        slopes = [c.slope_min + int(round(u[pos] * span))] * n_seg
        pos += 1
    n_cls = len(c.classes)
    if mode in {"surface", "joint"}:
        cls = [int(v * n_cls) for v in u[pos : pos + n_seg]]
    else:
        cls = [int(u[pos] * n_cls)] * n_seg
    merged: list[list[int]] = []
    for length, slope, klass in zip(lengths, slopes, cls, strict=True):
        if merged and merged[-1][1] == slope and merged[-1][2] == klass:
            merged[-1][0] += int(length)
        else:
            merged.append([int(length), int(slope), int(klass)])
    return {"segments": merged}


def segments_key(segments: list[list[int]]) -> str:
    return ";".join(f"{n}x{s}d{k}" for n, s, k in segments)


def design_from_segments(segments: list[list[int]], c: Constructability, label: str) -> RoofDesign:
    slope = np.concatenate([[s] * n for n, s, _ in segments]).astype(float)
    klass = np.concatenate([[k] * n for n, _, k in segments])
    props = np.array([c.classes[k][1:] for k in klass], dtype=float)
    return RoofDesign(
        slope_deg=slope,
        mu_static=props[:, 0],
        mu_kinetic=props[:, 1],
        adhesion_pa=props[:, 2],
        length_m=c.length_m,
        label=label,
    )


def check_constructable(segments: list[list[int]], c: Constructability) -> bool:
    if sum(n for n, _, _ in segments) != c.cells:
        return False
    if len(segments) - 1 > c.max_transitions:
        return False
    if any(n < c.min_segment_cells for n, _, _ in segments):
        return False
    slopes = [s for _, s, _ in segments]
    if min(slopes) < c.slope_min or max(slopes) > c.slope_max:
        return False
    if (
        len(slopes) > 1
        and max(abs(a - b) for a, b in zip(slopes, slopes[1:], strict=False))
        > c.adjacent_slope_limit_deg
    ):
        return False
    return all(0 <= k < len(c.classes) for _, _, k in segments)


def weather_set_v2(config: dict, dt_hours: float, **perturb) -> list[WeatherSeries]:
    settings = config["synthetic_weather"]
    return [
        continuous_synthetic_weather(
            s, duration_h=settings["duration_h"], dt_hours=dt_hours, **perturb
        )
        for s in settings["scenarios"]
    ]


OBJECTIVE_COLUMNS = ["l_max_kg_per_m", "s_event_max_kg_per_m"]


def evaluate_v2(
    design: RoofDesign, weathers: list[WeatherSeries], sim: SimulationConfig, spec: EventSpec
) -> dict:
    rec: dict = {}
    per = [simulate_v2(design, w, sim, spec) for w in weathers]
    rec["l_max_kg_per_m"] = max(r.l_max_kg_per_m for r in per)
    rec["s_event_max_kg_per_m"] = max(r.s_event_max_kg_per_m for r in per)
    for w in spec.windows_h:
        rec[f"s_window_{w:.4g}h_kg_per_m"] = max(r.s_window_max_kg_per_m[w] for r in per)
    rec["legacy_s_step_max_kg_per_m"] = max(r.legacy_s_step_max_kg_per_m for r in per)
    rec["total_shed_kg_per_m"] = max(r.total_shed_kg_per_m for r in per)
    rec["event_count_max"] = max(r.event_count for r in per)
    rec["event_ssci_max"] = max(r.event_ssci for r in per)
    rec["max_event_energy_j_per_m"] = max(r.max_event_energy_j_per_m for r in per)
    rec["time_above_intervention_h"] = max(r.time_above_intervention_h for r in per)
    rec["manual_triggers"] = max(r.manual_triggers for r in per)
    rec["residual_max_kg_per_m"] = max(r.residual_mass_kg_per_m for r in per)
    rec["mass_balance_abs_max"] = max(abs(r.mass_balance_error_kg_per_m) for r in per)
    for r, w in zip(per, weathers, strict=True):
        rec[f"l_max__{w.name}"] = r.l_max_kg_per_m
        rec[f"s_event_max__{w.name}"] = r.s_event_max_kg_per_m
    return rec


_WORKER: dict = {}


def _init_worker(config: dict, dt_hours: float, sim: SimulationConfig, spec: EventSpec) -> None:
    _WORKER.update(
        c=constructability_from_config(config),
        weathers=weather_set_v2(config, dt_hours),
        sim=sim,
        spec=spec,
    )


def _evaluate_segments(segments: list[list[int]]) -> dict:
    c = _WORKER["c"]
    design = design_from_segments(segments, c, "candidate")
    rec = evaluate_v2(design, _WORKER["weathers"], _WORKER["sim"], _WORKER["spec"])
    rec["segments"] = segments_key(segments)
    rec["feasible"] = check_constructable(segments, c)
    return rec


class ConstructableProblem(Problem):
    def __init__(self, mode: str, c: Constructability, pool, cache: dict) -> None:
        super().__init__(n_var=n_variables(mode, c), n_obj=2, xl=0.0, xu=1.0)
        self.mode, self.c, self.pool, self.cache = mode, c, pool, cache
        self.n_simulated = 0

    def _evaluate(self, x, out, *args, **kwargs):
        segs = [decode(row, self.mode, self.c)["segments"] for row in x]
        keys = [segments_key(s) for s in segs]
        todo = {k: s for k, s in zip(keys, segs, strict=True) if k not in self.cache}
        for rec in self.pool.map(_evaluate_segments, list(todo.values())):
            self.cache[rec["segments"]] = rec
        self.n_simulated += len(todo)
        out["F"] = np.array([[self.cache[k][col] for col in OBJECTIVE_COLUMNS] for k in keys])
        self.last_keys = keys


def run_constrained(
    config: dict,
    mode: str,
    seed: int,
    *,
    dt_hours: float,
    sim: SimulationConfig,
    spec: EventSpec,
    population: int,
    generations: int,
    out_dir: Path,
    workers: int = 2,
) -> dict:
    c = constructability_from_config(config)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache: dict = {}
    rows = []
    start = time.time()
    with Pool(workers, initializer=_init_worker, initargs=(config, dt_hours, sim, spec)) as pool:
        problem = ConstructableProblem(mode, c, pool, cache)
        algorithm = NSGA2(pop_size=population, eliminate_duplicates=True)
        algorithm.setup(
            problem, termination=get_termination("n_gen", generations), seed=seed, verbose=False
        )
        while algorithm.has_next():
            algorithm.next()
            for key in problem.last_keys:
                rows.append({"generation": int(algorithm.n_gen), "segments": key})
    runtime = time.time() - start
    history = pd.DataFrame(rows)
    evaluated = pd.DataFrame(list(cache.values()))
    evaluated.to_csv(out_dir / f"{mode}_seed_{seed}_evaluated.csv", index=False)
    history.to_csv(out_dir / f"{mode}_seed_{seed}_history.csv", index=False)
    meta = {
        "mode": mode,
        "seed": seed,
        "population": population,
        "generations": generations,
        "dt_hours": dt_hours,
        "objective_evaluations": int(len(history)),
        "unique_designs_simulated": int(problem.n_simulated),
        "runtime_s": runtime,
        "feasible_fraction": float(evaluated["feasible"].mean()),
        "config_sha256": hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest(),
    }
    (out_dir / f"{mode}_seed_{seed}_meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def uniform_constructable_segments(c: Constructability) -> list[list[list[int]]]:
    return [
        [[c.cells, s, k]]
        for s in range(c.slope_min, c.slope_max + 1)
        for k in range(len(c.classes))
    ]


def evaluate_many(
    config: dict,
    segment_list,
    *,
    dt_hours: float,
    sim: SimulationConfig,
    spec: EventSpec,
    workers: int = 2,
) -> pd.DataFrame:
    with Pool(workers, initializer=_init_worker, initargs=(config, dt_hours, sim, spec)) as pool:
        return pd.DataFrame(pool.map(_evaluate_segments, segment_list, chunksize=4))
