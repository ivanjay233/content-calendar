.PHONY: install dev test lint clean build

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=content_calendar

lint:
	ruff check content_calendar/ tests/
	mypy content_calendar/ --ignore-missing-imports

format:
	ruff format content_calendar/ tests/

clean:
	rm -rf build/ dist/ *.egg-info __pycache__ .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete

build: clean
	python -m build
