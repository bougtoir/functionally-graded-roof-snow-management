from __future__ import annotations

import csv
import pickle
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


def _load_checkpoint(path: Path) -> Algorithm:
    with path.open("rb") as handle:
        checkpoint = pickle.load(handle)
    if isinstance(checkpoint, OptimizationCheckpoint):
        np.random.set_state(checkpoint.numpy_random_state)
        return checkpoint.algorithm
    if isinstance(checkpoint, Algorithm):
        return checkpoint
    raise TypeError(f"unsupported optimization checkpoint: {type(checkpoint)}")


def _save_checkpoint(path: Path, algorithm: Algorithm) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(f"{path.suffix}.tmp")
    checkpoint = OptimizationCheckpoint(
        algorithm=algorithm,
        numpy_random_state=np.random.get_state(),
    )
    with temporary_path.open("wb") as handle:
        pickle.dump(checkpoint, handle)
    temporary_path.replace(path)


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

    if checkpoint_path.exists():
        algorithm = _load_checkpoint(checkpoint_path)
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
        _save_checkpoint(checkpoint_path, algorithm)

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
