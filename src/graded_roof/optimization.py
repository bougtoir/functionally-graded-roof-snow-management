from __future__ import annotations

import csv
import hashlib
import json
import pickle
import subprocess
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.algorithm import Algorithm
from pymoo.core.problem import ElementwiseProblem
from pymoo.termination import get_termination

from graded_roof.metrics import nondominated_mask
from graded_roof.models import SimulationConfig, WeatherSeries
from graded_roof.study import evaluate_design, heterogeneous_design


@dataclass
class OptimizationCheckpoint:
    algorithm: Algorithm
    numpy_random_state: tuple[str, np.ndarray, int, int, float]
    metadata: dict[str, str | int | float]


def variable_bounds(config: dict, mode: str) -> tuple[np.ndarray, np.ndarray]:
    control_points = config["optimizer"]["profile_control_points"]
    slope_low, slope_high = config["roof"]["slope_bounds_deg"]
    mu_low, mu_high = config["surface"]["static_friction_bounds"]
    adhesion_low, adhesion_high = config["surface"]["adhesion_bounds_pa"]
    if mode == "geometry":
        return (
            np.full(control_points, slope_low),
            np.full(control_points, slope_high),
        )
    if mode == "surface":
        return (
            np.r_[
                np.full(control_points, mu_low),
                np.full(control_points, adhesion_low),
            ],
            np.r_[
                np.full(control_points, mu_high),
                np.full(control_points, adhesion_high),
            ],
        )
    if mode == "joint":
        return (
            np.r_[
                np.full(control_points, slope_low),
                np.full(control_points, mu_low),
                np.full(control_points, adhesion_low),
            ],
            np.r_[
                np.full(control_points, slope_high),
                np.full(control_points, mu_high),
                np.full(control_points, adhesion_high),
            ],
        )
    raise ValueError("mode must be geometry, surface, or joint")


class GradedRoofProblem(ElementwiseProblem):
    def __init__(
        self,
        config: dict,
        weathers: list[WeatherSeries],
        simulation_settings: SimulationConfig,
        mode: str,
    ) -> None:
        lower, upper = variable_bounds(config, mode)
        super().__init__(
            n_var=lower.size,
            n_obj=2,
            n_ieq_constr=1,
            xl=lower,
            xu=upper,
        )
        self.config = config
        self.weathers = weathers
        self.simulation_settings = simulation_settings
        self.mode = mode

    def _evaluate(
        self,
        variables: np.ndarray,
        output: dict,
        *args: object,
        **kwargs: object,
    ) -> None:
        design = heterogeneous_design(
            variables,
            self.config,
            self.mode,
            label=self.mode,
        )
        aggregate, _ = evaluate_design(
            design,
            self.weathers,
            self.simulation_settings,
        )
        output["F"] = [
            aggregate["l_max_kg_per_m"],
            aggregate["s_max_kg_per_m"],
        ]
        output["G"] = [
            np.max(np.abs(np.diff(design.slope_deg)))
            - self.config["roof"]["adjacent_slope_limit_deg"]
        ]


def _append_population(
    path: Path,
    generation: int,
    variables: np.ndarray,
    objectives: np.ndarray,
    constraints: np.ndarray,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "generation",
        "l_max_kg_per_m",
        "s_max_kg_per_m",
        "constraint",
        *[f"x_{index:02d}" for index in range(variables.shape[1])],
    ]
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            lineterminator="\n",
        )
        if write_header:
            writer.writeheader()
        for variable, objective, constraint in zip(
            variables,
            objectives,
            constraints,
            strict=True,
        ):
            writer.writerow(
                {
                    "generation": generation,
                    "l_max_kg_per_m": objective[0],
                    "s_max_kg_per_m": objective[1],
                    "constraint": constraint[0],
                    **{
                        f"x_{index:02d}": value
                        for index, value in enumerate(variable)
                    },
                }
            )


def _front_from_history(history_path: Path, output_path: Path) -> pd.DataFrame:
    history = pd.read_csv(history_path)
    feasible = history.loc[history["constraint"] <= 1e-9].copy()
    feasible = feasible.drop_duplicates(
        subset=[
            column
            for column in feasible.columns
            if column.startswith("x_")
        ]
    )
    mask = nondominated_mask(
        feasible[["l_max_kg_per_m", "s_max_kg_per_m"]].to_numpy()
    )
    front = feasible.loc[mask].sort_values(
        ["l_max_kg_per_m", "s_max_kg_per_m"]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    front.to_csv(output_path, index=False)
    return front


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_sha256() -> str:
    source_root = Path(__file__).resolve().parent
    digest = hashlib.sha256()
    for name in [
        "metrics.py",
        "models.py",
        "optimization.py",
        "simulation.py",
        "study.py",
        "weather.py",
    ]:
        path = source_root / name
        digest.update(name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _weather_sha256(weathers: list[WeatherSeries]) -> str:
    digest = hashlib.sha256()
    for weather in weathers:
        digest.update(weather.name.encode("utf-8"))
        digest.update(np.asarray([weather.dt_hours], dtype=np.float64).tobytes())
        for values in [
            weather.temperature_c,
            weather.snowfall_kg_m2,
            weather.rain_mm,
        ]:
            digest.update(np.asarray(values, dtype=np.float64).tobytes())
    return digest.hexdigest()


def _git_commit() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[2],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _checkpoint_metadata(
    config: dict,
    weathers: list[WeatherSeries],
    mode: str,
    seed: int,
) -> dict[str, str | int | float]:
    encoded_config = json.dumps(
        config,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "mode": mode,
        "seed": seed,
        "dt_hours": float(config["simulation"]["dt_hours"]),
        "population": int(config["optimizer"]["population"]),
        "generations": int(config["optimizer"]["generations"]),
        "config_sha256": hashlib.sha256(encoded_config).hexdigest(),
        "weather_sha256": _weather_sha256(weathers),
        "source_sha256": _source_sha256(),
        "code_commit": _git_commit(),
    }


def _load_checkpoint(
    path: Path,
    expected_metadata: dict[str, str | int | float],
) -> Algorithm:
    manifest_path = path.with_suffix(f"{path.suffix}.json")
    if not manifest_path.exists():
        raise ValueError(f"checkpoint manifest is missing: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if _sha256(path) != manifest["checkpoint_sha256"]:
        raise ValueError(f"checkpoint checksum mismatch: {path}")
    with path.open("rb") as handle:
        checkpoint = pickle.load(handle)
    if isinstance(checkpoint, OptimizationCheckpoint):
        compatibility_keys = [
            "mode",
            "seed",
            "dt_hours",
            "population",
            "generations",
            "config_sha256",
            "weather_sha256",
            "source_sha256",
        ]
        mismatches = [
            key
            for key in compatibility_keys
            if checkpoint.metadata.get(key) != expected_metadata.get(key)
        ]
        if mismatches:
            raise ValueError(
                "checkpoint metadata mismatch: " + ", ".join(mismatches)
            )
        np.random.set_state(checkpoint.numpy_random_state)
        return checkpoint.algorithm
    raise TypeError(f"unsupported optimization checkpoint: {type(checkpoint)}")


def _save_checkpoint(
    path: Path,
    algorithm: Algorithm,
    metadata: dict[str, str | int | float],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    checkpoint = OptimizationCheckpoint(
        algorithm=algorithm,
        numpy_random_state=np.random.get_state(),
        metadata=metadata,
    )
    with temporary_path.open("wb") as handle:
        pickle.dump(checkpoint, handle)
    temporary_path.replace(path)
    manifest_path = path.with_suffix(f"{path.suffix}.json")
    temporary_manifest = manifest_path.with_suffix(
        f"{manifest_path.suffix}.tmp"
    )
    temporary_manifest.write_text(
        json.dumps(
            {
                **metadata,
                "checkpoint_sha256": _sha256(path),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary_manifest.replace(manifest_path)


def run_optimization(
    config: dict,
    weathers: list[WeatherSeries],
    simulation_settings: SimulationConfig,
    mode: str,
    seed: int,
    *,
    results_dir: Path,
    checkpoint_dir: Path,
) -> Path:
    generations = config["optimizer"]["generations"]
    population = config["optimizer"]["population"]
    history_path = results_dir / f"{mode}_seed_{seed}_history.csv"
    front_path = results_dir / f"{mode}_seed_{seed}_pareto.csv"
    checkpoint_path = checkpoint_dir / f"{mode}_seed_{seed}.pkl"
    problem = GradedRoofProblem(config, weathers, simulation_settings, mode)
    metadata = _checkpoint_metadata(config, weathers, mode, seed)

    if checkpoint_path.exists():
        algorithm = _load_checkpoint(checkpoint_path, metadata)
    else:
        history_path.unlink(missing_ok=True)
        front_path.unlink(missing_ok=True)
        algorithm = NSGA2(pop_size=population, eliminate_duplicates=True)
        algorithm.setup(
            problem,
            termination=get_termination("n_gen", generations),
            seed=seed,
            verbose=False,
        )

    while algorithm.has_next():
        algorithm.next()
        variables = np.asarray(algorithm.pop.get("X"), dtype=float)
        objectives = np.asarray(algorithm.pop.get("F"), dtype=float)
        constraints = np.asarray(algorithm.pop.get("G"), dtype=float)
        _append_population(
            history_path,
            int(algorithm.n_gen),
            variables,
            objectives,
            constraints,
        )
        _save_checkpoint(checkpoint_path, algorithm, metadata)

    _front_from_history(history_path, front_path)
    return front_path


def combine_fronts(
    front_paths: list[Path],
    output_path: Path,
) -> pd.DataFrame:
    combined = pd.concat(
        [pd.read_csv(path).assign(source=path.stem) for path in front_paths],
        ignore_index=True,
    )
    mask = nondominated_mask(
        combined[["l_max_kg_per_m", "s_max_kg_per_m"]].to_numpy()
    )
    front = combined.loc[mask].sort_values(
        ["l_max_kg_per_m", "s_max_kg_per_m"]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    front.to_csv(output_path, index=False)
    return front
