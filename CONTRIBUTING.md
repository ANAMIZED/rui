# Contributing to RUI

Thank you for your interest in contributing to Recursive UltraIntelligence.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest tests/ -v
python tests/e2e/test_rui_e2e.py
```

All PRs must keep the verification suite green.

## Principles

- Cost and governance are first-class; never bypass budgets or constitutional invariants.
- Prefer small, well-tested changes.
- Update CHANGELOG.md and docs when adding features.
- Follow the existing package layout under `src/rui/`.

## Code of Conduct

See CODE_OF_CONDUCT.md.
