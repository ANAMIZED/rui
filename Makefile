.PHONY: install test e2e verify clean cli api mcp surfaces

install:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v

e2e:
	python tests/e2e/test_rui_e2e.py

cli:
	rui version && rui status && rui gov constitution

api:
	@echo "Start API with: rui serve --port 8080  (or rui-api)"

mcp:
	@echo "Start MCP with: rui-mcp"

surfaces:
	python -c "from rui import RUI, __version__; from rui.cli import app; from rui.sdk import RUIClient; from rui.api.main import app as api; from rui.mcp.server import mcp; from rui.workflows import run_multi_agent_workflow; print('All surfaces import OK', __version__)"

verify: test surfaces cli e2e
	@echo "All verification checks passed."

clean:
	rm -rf .pytest_cache __pycache__ src/rui/**/__pycache__ dist build *.egg-info
