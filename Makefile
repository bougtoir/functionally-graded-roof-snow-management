PYTHON ?= python
export PYTHONPATH := $(CURDIR)/src$(if $(PYTHONPATH),:$(PYTHONPATH))

.PHONY: test lint data baseline convergence uniform optimize jma sensitivity robustness figures tables manuscript validate all clean

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
