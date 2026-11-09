"""Revised (R1) reduced-order roof-snow model with timestep-independent release.

Differences from the submitted ``simulation.simulate``:

* A cell fails when its retained mass reaches the static threshold
  ``m* = c A / (g (sin(theta) - mu_s cos(theta)))`` (per unit width).  The
  crossing time inside a forcing step is located exactly because forcing is
  piecewise constant in time; release is not tied to step boundaries.
* A released slab moves along the roof as a rigid Coulomb block.  Its squared
  velocity follows the work-energy relation ``v^2 += 2 g (sin - mu_k cos) dx``
  cell by cell; resting snow in traversed cells is entrained with perfectly
  inelastic momentum exchange; the slab deposits where ``v^2 <= 0`` or leaves
  at the eave.  Transport distance is therefore independent of ``dt``.
* Cells that cannot retain snow (``m* = 0``) route their inflow continuously
  to the stopping cell or the eave (stream outflow, kg m-1 h-1).
* Eave outflow is logged in continuous time (impulses and stream segments) and
  aggregated into physical shedding events by :func:`segment_events`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from graded_roof.models import RoofDesign, SimulationConfig, WeatherSeries
from graded_roof.simulation import _effective_friction

TIME_TOL_H = 1e-9
MASS_TOL = 1e-12


@dataclass(frozen=True)
class EventSpec:
    flow_threshold_kg_m_h: float = 1.0
    separation_h: float = 1.0
    windows_h: tuple[float, ...] = (1.0 / 6.0, 1.0, 3.0)


@dataclass
class OutflowLog:
    impulse_time_h: list[float] = field(default_factory=list)
    impulse_mass: list[float] = field(default_factory=list)
    impulse_energy: list[float] = field(default_factory=list)
    stream_t0: list[float] = field(default_factory=list)
    stream_t1: list[float] = field(default_factory=list)
    stream_mass: list[float] = field(default_factory=list)

    def add_stream(self, t0: float, t1: float, mass: float) -> None:
        if mass <= MASS_TOL or t1 <= t0:
            return
        if self.stream_t1 and abs(self.stream_t1[-1] - t0) < TIME_TOL_H:
            last_rate = self.stream_mass[-1] / (self.stream_t1[-1] - self.stream_t0[-1])
            if abs(last_rate - mass / (t1 - t0)) <= 1e-9 * max(1.0, last_rate):
                self.stream_t1[-1] = t1
                self.stream_mass[-1] += mass
                return
        self.stream_t0.append(t0)
        self.stream_t1.append(t1)
        self.stream_mass.append(mass)


@dataclass
class V2Result:
    l_max_kg_per_m: float
    s_event_max_kg_per_m: float
    s_window_max_kg_per_m: dict[float, float]
    legacy_s_step_max_kg_per_m: float
    total_shed_kg_per_m: float
    event_count: int
    events: list[dict]
    event_ssci: float
    max_event_energy_j_per_m: float
    input_snow_kg_per_m: float
    melt_kg_per_m: float
    residual_mass_kg_per_m: float
    mass_balance_error_kg_per_m: float
    time_above_intervention_h: float
    manual_triggers: int
    roof_mass_end_of_step: np.ndarray
    shed_per_step: np.ndarray
    outflow: OutflowLog
    final_cell_mass: np.ndarray


def segment_events(log: OutflowLog, spec: EventSpec) -> list[dict]:
    """Group eave outflow into physical shedding events.

    Activity = every slab impulse plus every stream segment whose rate is at
    least ``flow_threshold``.  Activity intervals separated by less than
    ``separation_h`` merge into one event.  Event mass is all eave outflow
    (impulses and stream, including sub-threshold flow) inside the merged
    interval.
    """
    intervals = [(t, t) for t in log.impulse_time_h]
    for t0, t1, m in zip(log.stream_t0, log.stream_t1, log.stream_mass, strict=True):
        if m / (t1 - t0) >= spec.flow_threshold_kg_m_h:
            intervals.append((t0, t1))
    if not intervals:
        return []
    intervals.sort()
    merged = [list(intervals[0])]
    for t0, t1 in intervals[1:]:
        if t0 - merged[-1][1] < spec.separation_h:
            merged[-1][1] = max(merged[-1][1], t1)
        else:
            merged.append([t0, t1])
    imp_t = np.asarray(log.impulse_time_h)
    imp_m = np.asarray(log.impulse_mass)
    imp_e = np.asarray(log.impulse_energy)
    s0 = np.asarray(log.stream_t0)
    s1 = np.asarray(log.stream_t1)
    sm = np.asarray(log.stream_mass)
    events = []
    for t0, t1 in merged:
        sel = (imp_t >= t0 - TIME_TOL_H) & (imp_t <= t1 + TIME_TOL_H)
        mass = float(imp_m[sel].sum()) if imp_t.size else 0.0
        energy = float(imp_e[sel].sum()) if imp_t.size else 0.0
        if s0.size:
            overlap = np.clip(np.minimum(s1, t1) - np.maximum(s0, t0), 0.0, None)
            mass += float((sm * overlap / (s1 - s0)).sum())
        events.append(
            {
                "start_h": float(t0),
                "end_h": float(t1),
                "duration_h": float(t1 - t0),
                "mass_kg_per_m": mass,
                "slab_impulses": int(sel.sum()) if imp_t.size else 0,
                "slab_energy_j_per_m": energy,
            }
        )
    return events


def max_window_mass(log: OutflowLog, window_h: float) -> float:
    """Largest eave outflow inside any closed window of length ``window_h``."""
    imp_t = np.asarray(log.impulse_time_h, dtype=float)
    imp_m = np.asarray(log.impulse_mass, dtype=float)
    s0 = np.asarray(log.stream_t0, dtype=float)
    s1 = np.asarray(log.stream_t1, dtype=float)
    sm = np.asarray(log.stream_mass, dtype=float)
    if imp_t.size == 0 and s0.size == 0:
        return 0.0
    breaks = np.concatenate([imp_t, s0, s1])
    starts = np.unique(np.concatenate([breaks, breaks - window_h]))
    ends = starts + window_h
    order = np.argsort(imp_t)
    imp_t, imp_m = imp_t[order], imp_m[order]
    cum = np.concatenate([[0.0], np.cumsum(imp_m)])
    lo = np.searchsorted(imp_t, starts - TIME_TOL_H, side="left")
    hi = np.searchsorted(imp_t, ends + TIME_TOL_H, side="right")
    total = cum[hi] - cum[lo]
    if s0.size:
        rate = sm / (s1 - s0)
        for chunk in np.array_split(np.arange(starts.size), max(1, starts.size // 2000)):
            overlap = np.clip(
                np.minimum(s1[None, :], ends[chunk, None])
                - np.maximum(s0[None, :], starts[chunk, None]),
                0.0,
                None,
            )
            total[chunk] += overlap @ rate
    return float(total.max())


def _static_threshold(theta, mu_s, adhesion_pa, cell_area, gravity):
    drive = np.sin(theta) - mu_s * np.cos(theta)
    with np.errstate(divide="ignore"):
        return np.where(drive > 0, adhesion_pa * cell_area / (gravity * np.where(drive > 0, drive, 1.0)), np.inf)


def _stream_destinations(accel: np.ndarray, dx: float, can_retain: np.ndarray) -> np.ndarray:
    """Stopping cell (or ``cells`` for the eave) for snow starting at rest."""
    cells = accel.size
    dest = np.full(cells, cells, dtype=int)
    for i in range(cells):
        if can_retain[i]:
            dest[i] = i
            continue
        v2 = accel[i] * dx
        for j in range(i + 1, cells):
            v2 += 2.0 * accel[j] * dx
            if v2 <= 0:
                dest[i] = j
                break
    return dest


def simulate_v2(
    design: RoofDesign,
    weather: WeatherSeries,
    config: SimulationConfig,
    spec: EventSpec | None = None,
    entrainment: bool = True,
) -> V2Result:
    spec = spec or EventSpec()
    cells = design.cells
    area = design.cell_area_m2
    width = design.width_m
    dx = design.length_m / cells
    dt = weather.dt_hours
    g = config.gravity_m_s2
    theta = np.deg2rad(design.slope_deg)
    sin_t, cos_t = np.sin(theta), np.cos(theta)
    mass = np.zeros(cells)
    volume = np.zeros(cells)
    age = np.zeros(cells)
    steps = len(weather.temperature_c)
    roof_end = np.zeros(steps)
    shed_step = np.zeros(steps)
    log = OutflowLog()
    total_melt = 0.0
    total_input = 0.0
    l_max = 0.0
    above_h = 0.0
    triggers = 0
    was_above = False

    def release(i: int, t_abs: float, mu_k: np.ndarray) -> float:
        moving = mass[i]
        mov_age, mov_vol = age[i], volume[i]
        mass[i] = age[i] = volume[i] = 0.0
        v2 = 2.0 * g * (sin_t[i] - mu_k[i] * cos_t[i]) * dx / 2.0
        for j in range(i + 1, cells):
            if entrainment and mass[j] > 0:
                v2 *= (moving / (moving + mass[j])) ** 2
                moving += mass[j]
                mov_age += age[j]
                mov_vol += volume[j]
                mass[j] = age[j] = volume[j] = 0.0
            v2 += 2.0 * g * (sin_t[j] - mu_k[j] * cos_t[j]) * dx
            if v2 <= 0:
                mass[j] += moving
                age[j] += mov_age
                volume[j] += mov_vol
                return 0.0
        log.impulse_time_h.append(t_abs)
        log.impulse_mass.append(moving / width)
        log.impulse_energy.append(0.5 * moving * v2 / width)
        return moving

    for step in range(steps):
        t_start = step * dt
        temp = weather.temperature_c[step]
        with np.errstate(divide="ignore", invalid="ignore"):
            age_days = np.where(mass > 0, age / np.where(mass > 0, mass, 1.0), 0.0)
        mu_s = _effective_friction(design.mu_static, age_days, temp, config)
        mu_k = _effective_friction(design.mu_kinetic, age_days, temp, config)
        threshold = _static_threshold(theta, mu_s, design.adhesion_pa, area, g)
        accel = g * (sin_t - mu_k * cos_t)
        stream = threshold <= 0
        dest = _stream_destinations(accel, dx, ~stream)
        shed_here = 0.0
        for i in range(cells):
            if mass[i] > 0 and mass[i] >= threshold[i] - MASS_TOL:
                shed_here += release(i, t_start, mu_k)
        snow_rate = weather.snowfall_kg_m2[step] * area / dt
        total_input += weather.snowfall_kg_m2[step] * area * cells
        melt_rate = (
            config.melt_factor_kg_m2_c_h * max(temp, 0.0)
            + config.rain_heat_factor_kg_m2_mm * weather.rain_mm[step] / dt
        ) * area
        inflow = np.zeros(cells + 1)
        np.add.at(inflow, dest[stream], snow_rate)
        eave_stream_rate = inflow[cells]
        gain = np.where(stream, 0.0, snow_rate) + inflow[:cells]
        tau = 0.0
        while tau < dt - TIME_TOL_H:
            melting = (mass > MASS_TOL) | (gain >= melt_rate)
            net = gain - np.where(melting, melt_rate, np.minimum(melt_rate, gain))
            net[stream] = 0.0
            horizon = dt - tau
            with np.errstate(divide="ignore", invalid="ignore"):
                t_cross = np.where(
                    (net > 0) & np.isfinite(threshold) & (threshold > 0),
                    (threshold - mass) / net,
                    np.inf,
                )
                t_zero = np.where((net < 0) & (mass > MASS_TOL), mass / -net, np.inf)
            nxt = min(horizon, float(t_cross.min()), float(t_zero.min()))
            nxt = max(nxt, 0.0)
            melted = np.minimum(mass + gain * nxt, (gain - net) * nxt)
            melted = np.where(stream, 0.0, np.clip(melted, 0.0, None))
            frac = np.where(mass > 0, np.clip(1 - melted / np.where(mass > 0, mass, 1.0), 0, 1), 0)
            age *= frac
            volume *= frac
            added = np.where(stream, 0.0, gain * nxt)
            volume += added / config.initial_density_kg_m3
            mass[:] = np.where(stream, 0.0, np.clip(mass + net * nxt, 0.0, None))
            total_melt += float(melted.sum())
            log.add_stream(t_start + tau, t_start + tau + nxt, eave_stream_rate * nxt / width)
            shed_here += eave_stream_rate * nxt
            tau += nxt
            l_max = max(l_max, mass.sum() / width)
            hit = np.flatnonzero(t_cross <= nxt + TIME_TOL_H) if nxt < horizon else []
            for i in hit:
                if mass[i] >= threshold[i] - 1e-9 * max(1.0, threshold[i]):
                    shed_here += release(int(i), t_start + tau, mu_k)
            if nxt == 0.0 and len(hit) == 0:
                break
        age += mass * dt / 24.0
        density = np.where(volume > 0, mass / np.where(volume > 0, volume, 1.0), config.initial_density_kg_m3)
        density += config.compaction_rate_per_day * dt / 24.0 * (config.maximum_density_kg_m3 - density)
        density = np.minimum(density, config.maximum_density_kg_m3)
        volume = np.where(mass > 0, mass / density, 0.0)
        roof_end[step] = mass.sum() / width
        shed_step[step] = shed_here / width
        above = roof_end[step] > config.intervention_mass_kg_per_m
        if above:
            above_h += dt
        if above and not was_above:
            triggers += 1
        was_above = above

    events = segment_events(log, spec)
    masses = np.array([e["mass_kg_per_m"] for e in events])
    total_shed = float(np.sum(log.impulse_mass) + np.sum(log.stream_mass))
    residual = float(mass.sum() / width)
    balance = total_input / width - total_shed - total_melt / width - residual
    return V2Result(
        l_max_kg_per_m=float(l_max),
        s_event_max_kg_per_m=float(masses.max()) if masses.size else 0.0,
        s_window_max_kg_per_m={w: max_window_mass(log, w) for w in spec.windows_h},
        legacy_s_step_max_kg_per_m=float(shed_step.max(initial=0.0)),
        total_shed_kg_per_m=total_shed,
        event_count=len(events),
        events=events,
        event_ssci=float(np.square(masses / masses.sum()).sum()) if masses.sum() > 0 else 0.0,
        max_event_energy_j_per_m=max((e["slab_energy_j_per_m"] for e in events), default=0.0),
        input_snow_kg_per_m=total_input / width,
        melt_kg_per_m=total_melt / width,
        residual_mass_kg_per_m=residual,
        mass_balance_error_kg_per_m=float(balance),
        time_above_intervention_h=above_h,
        manual_triggers=triggers,
        roof_mass_end_of_step=roof_end,
        shed_per_step=shed_step,
        outflow=log,
        final_cell_mass=mass / width,
    )
