PYTHON ?= python

.PHONY: test lint data baseline optimize sensitivity robustness figures tables manuscript validate all clean

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src scripts tests

data:
	$(PYTHON) scripts/run_pipeline.py data

baseline:
	$(PYTHON) scripts/run_pipeline.py baseline

optimize:
	$(PYTHON) scripts/run_pipeline.py optimize

sensitivity:
	$(PYTHON) scripts/run_pipeline.py sensitivity

robustness:
	$(PYTHON) scripts/run_pipeline.py robustness

figures:
	$(PYTHON) scripts/run_pipeline.py figures

tables:
	$(PYTHON) scripts/run_pipeline.py tables

manuscript:
	$(PYTHON) scripts/run_pipeline.py manuscript

validate:
	$(PYTHON) scripts/run_pipeline.py validate

all:
	$(PYTHON) scripts/run_pipeline.py all

clean:
	rm -rf results/generated figures/png figures/tiff figures/vector tables/generated manuscript/build submission/CRST_submission_package.zip
