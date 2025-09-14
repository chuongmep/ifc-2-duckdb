.PHONY: help install install-dev test lint format type-check clean build upload docs

help:
	@echo "Available commands:"
	@echo "  install      Install the package in development mode"
	@echo "  install-dev  Install the package with development dependencies"
	@echo "  test         Run tests with pytest"
	@echo "  lint         Run linting checks (black, flake8, isort)"
	@echo "  format       Format code with black and isort"
	@echo "  type-check   Run type checking with mypy"
	@echo "  clean        Clean build artifacts"
	@echo "  build        Build the package"
	@echo "  upload       Upload to PyPI (requires credentials)"
	@echo "  docs         Build documentation"

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --cov=ifc2duckdb --cov-report=term-missing --cov-report=html

lint:
	black --check ifc2duckdb tests
	flake8 ifc2duckdb tests
	isort --check-only ifc2duckdb tests

format:
	black ifc2duckdb tests
	isort ifc2duckdb tests

type-check:
	mypy ifc2duckdb --ignore-missing-imports

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

upload: build
	python -m twine upload dist/*

docs:
	@echo "Documentation building not yet implemented"
