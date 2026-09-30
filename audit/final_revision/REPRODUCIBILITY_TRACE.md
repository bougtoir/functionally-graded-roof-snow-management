# Reproducibility trace

- Canonical command: `make all`.
- Production timestep: 0.5 h; sensitivity reference: 0.25 h.
- Uniform grid: 6,300 designs; heterogeneous optimizer: population 48, 45 generations, and three frozen seeds per mode.
- Nine `checkpoints/dt_0p5h/` files passed checksum and compatibility validation: True.
- Fresh detached reproduction: PASS (CHECKPOINT-BASED). All canonical 0.5-h checkpoint manifests passed configuration, source, weather, seed, and checksum compatibility checks. Figures, Tables, manuscript files, and the submission package were regenerated and validated from those outputs; no detached full optimizer rerun is claimed.
- Preserved 1-h outputs are historical references under `results/reference_1h/`, not current production results.
