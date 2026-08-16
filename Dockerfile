FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml requirements.txt README.md LICENSE ./
COPY src/ src/
COPY tests/ tests/
COPY docs/ docs/

RUN pip install --no-cache-dir -e ".[dev]"

CMD ["python", "-m", "pytest", "tests/", "-v"]
