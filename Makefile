.PHONY: install test e2e verify clean

install:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

e2e:
	python tests/e2e/test_rui_e2e.py

verify: test e2e
	@echo "All verification checks passed."

clean:
	rm -rf .pytest_cache __pycache__ src/rui/**/__pycache__ dist build *.egg-info
