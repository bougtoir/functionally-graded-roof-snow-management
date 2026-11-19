# REPRODUCIBILITY_AUDIT_FINAL (R1)

- Full R1 chain: `make r1 PYTHON=./.venv/bin/python` (weather, convergence, optimisation, Pareto, robustness, event sensitivity, JMA, review analyses, figures, documents). Documents only: `make r1-docs`. Exception audit: `python scripts/r1_exception_audit.py`.
- Final pass reran: review analyses, exception audit, figures, manuscript, package, tracked comparison, reference audit, QC (44/44; 5 author-pending placeholders), ruff, pytest (41 passed), `make validate`.
- Deliberately not rerun: NSGA-II optimisation, convergence study, robustness Monte Carlo, JMA acquisition (frozen canonical outputs reused).
- Config hash recorded in each optimisation meta.json (`config_sha256`); seeds 1701, 2903, 4517, 6007, 8191; robustness seed 7021.
- Private inputs (reviewer comments, Editorial Manager DOCX) are required only for the tracked comparison and the response letter; `private/` is gitignored.
