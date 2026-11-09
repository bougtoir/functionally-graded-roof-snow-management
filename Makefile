PYTHON ?= python
export PYTHONPATH := $(CURDIR)/src$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: test lint data baseline convergence uniform optimize jma sensitivity robustness figures tables manuscript validate all clean r1 r1-docs

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src scripts tests

data:
	$(PYTHON) scripts/run_pipeline.py data

baseline:
	$(PYTHON) scripts/run_pipeline.py baseline

convergence:
	$(PYTHON) scripts/run_pipeline.py convergence

uniform:
	$(PYTHON) scripts/run_pipeline.py uniform

optimize:
	$(PYTHON) scripts/run_pipeline.py optimize

jma:
	$(PYTHON) scripts/run_pipeline.py jma

sensitivity:
	$(PYTHON) scripts/run_pipeline.py sensitivity

robustness:
	$(PYTHON) scripts/run_pipeline.py robustness

figures: tables
	$(PYTHON) scripts/run_pipeline.py figures

tables:
	$(PYTHON) scripts/run_pipeline.py tables

manuscript:
	$(PYTHON) scripts/run_pipeline.py manuscript

validate:
	$(PYTHON) scripts/run_pipeline.py validate

all:
	$(PYTHON) scripts/run_pipeline.py data
	$(PYTHON) scripts/run_pipeline.py baseline
	$(PYTHON) scripts/run_pipeline.py convergence
	$(PYTHON) scripts/run_pipeline.py uniform
	$(PYTHON) scripts/run_pipeline.py optimize
	$(PYTHON) scripts/run_pipeline.py jma
	$(PYTHON) scripts/run_pipeline.py sensitivity
	$(PYTHON) scripts/run_pipeline.py robustness
	$(PYTHON) scripts/run_final_revision_analyses.py --stage frontier
	$(PYTHON) scripts/run_final_revision_analyses.py --stage knee
	$(PYTHON) scripts/run_final_revision_analyses.py --stage robustness
	$(PYTHON) scripts/run_final_revision_analyses.py --stage jma
	$(PYTHON) scripts/run_final_revision_analyses.py --stage literature
	$(PYTHON) scripts/run_final_revision_analyses.py --stage targeted
	$(PYTHON) scripts/run_pipeline.py tables
	$(PYTHON) scripts/run_final_revision_analyses.py --stage constructability
	$(PYTHON) scripts/run_0p5h_revision.py --stage timestep
	$(PYTHON) scripts/run_0p5h_revision.py --stage comparison
	$(PYTHON) scripts/run_0p5h_revision.py --stage quarter-hour
	$(PYTHON) scripts/run_0p5h_revision.py --stage checkpoint-audit
	$(PYTHON) scripts/run_pipeline.py figures
	$(PYTHON) scripts/run_pipeline.py manuscript
	$(PYTHON) scripts/run_pipeline.py validate

clean:
	rm -rf results/generated figures/png figures/tiff figures/vector tables/generated manuscript/build submission/CRST_submission_package.zip submission/CRST_submission_package_final.zip submission/CRST_submission_package_FINAL.zip

# Reviewer-driven revision (R1). Writes only to results/r1, checkpoints/r1, figures/r1, manuscript/r1;
# the submitted pipeline above (`all`) and its outputs are left untouched.
r1:
	$(PYTHON) scripts/r1_weather.py
	$(PYTHON) scripts/r1_convergence.py
	$(PYTHON) scripts/r1_optimize.py
	$(PYTHON) scripts/r1_analyze.py
	$(PYTHON) scripts/r1_robustness.py
	$(PYTHON) scripts/r1_robustness_summary.py
	$(PYTHON) scripts/r1_event_sensitivity.py
	$(PYTHON) scripts/r1_jma.py
	$(PYTHON) scripts/r1_jma_summary.py
	$(PYTHON) scripts/r1_figures.py
	$(MAKE) r1-docs PYTHON=$(PYTHON)

r1-docs:
	$(PYTHON) scripts/r1_build_manuscript.py
	$(PYTHON) scripts/r1_package.py
	$(PYTHON) scripts/r1_reference_audit.py manuscript/r1/manuscript_R1_clean.docx revision_r1/REFERENCE_AUDIT_R1.csv
	$(PYTHON) scripts/r1_qc.py
