import numpy as np
import pytest

from graded_roof.forcing_v2 import continuous_synthetic_weather
from graded_roof.models import RoofDesign, SimulationConfig, WeatherSeries
from graded_roof.optimization_v2 import Constructability, check_constructable, decode, n_variables
from graded_roof.simulation_v2 import EventSpec, OutflowLog, max_window_mass, segment_events, simulate_v2

SCEN = {"name": "t", "snowfall_peak_kg_m2_h": 6.0, "snowfall_hours": 48, "base_temperature_c": -4.0,
        "warming_c_per_day": 0.3, "repeated_events": 3, "rain_on_snow_mm": 5.0}


def _const_weather(hours, dt, rate):
    n = int(hours / dt)
    return WeatherSeries(np.full(n, -10.0), np.full(n, rate * dt), np.zeros(n), dt, "c")


def test_static_threshold_release_mass_is_analytic():
    cfg = SimulationConfig(friction_model="constant")
    d = RoofDesign.uniform(8, 8.0, 30.0, 0.28, 0.21, 80.0)
    r = simulate_v2(d, _const_weather(200, 0.5, 1.0), cfg)
    th = np.deg2rad(30.0)
    m_star = 80.0 * 1.0 / (cfg.gravity_m_s2 * (np.sin(th) - 0.28 * np.cos(th)))
    assert r.l_max_kg_per_m == pytest.approx(8 * m_star, rel=1e-6)
    assert r.s_event_max_kg_per_m == pytest.approx(8 * m_star, rel=1e-6)


@pytest.mark.parametrize("design", [(40, 0.12, 0.0), (30, 0.28, 80.0), (35, 0.12, 25.0), (20, 0.55, 180.0)])
def test_mass_conservation_and_dt_independence(design):
    s, mu, a = design
    d = RoofDesign.uniform(24, 8.0, s, mu, 0.78 * mu, a)
    res = [simulate_v2(d, continuous_synthetic_weather(SCEN, duration_h=240, dt_hours=dt), SimulationConfig()) for dt in (0.5, 0.125)]
    for r in res:
        assert abs(r.mass_balance_error_kg_per_m) < 1e-6
    assert res[0].input_snow_kg_per_m == pytest.approx(res[1].input_snow_kg_per_m, rel=1e-9)
    assert res[0].l_max_kg_per_m == pytest.approx(res[1].l_max_kg_per_m, rel=0.02, abs=1.0)
    assert res[0].s_window_max_kg_per_m[1.0] == pytest.approx(res[1].s_window_max_kg_per_m[1.0], rel=0.02, abs=1.0)


def test_event_merging_rules():
    log = OutflowLog()
    log.impulse_time_h += [1.0, 1.5, 5.0]
    log.impulse_mass += [10.0, 5.0, 7.0]
    log.impulse_energy += [0.0, 0.0, 0.0]
    log.add_stream(5.2, 6.0, 0.4)  # 0.5 kg/m/h: below q_min, counted inside event
    ev = segment_events(log, EventSpec())
    assert [round(e["mass_kg_per_m"], 6) for e in ev] == [15.0, 7.0]
    assert max_window_mass(log, 1.0) == pytest.approx(15.0)
    assert max_window_mass(log, 10.0) == pytest.approx(22.4)


def test_encoding_is_always_constructable():
    c = Constructability(classes=(("a", 0.1, 0.08, 10.0), ("b", 0.3, 0.2, 50.0), ("c", 0.5, 0.4, 150.0)))
    rng = np.random.default_rng(1)
    for mode in ("geometry", "surface", "joint"):
        for _ in range(500):
            assert check_constructable(decode(rng.random(n_variables(mode, c)), mode, c)["segments"], c)
