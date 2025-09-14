# Package Structure Overview

This document provides an overview of the complete Python package structure for `ifc2duckdb`.

## Directory Structure

```
ifc-2-duckdb/
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD pipeline
├── .gitignore                     # Git ignore patterns
├── .pre-commit-config.yaml        # Pre-commit hooks configuration
├── examples/
│   └── basic_usage.py             # Example usage script
├── ifc2duckdb/                    # Main package directory
│   ├── __init__.py                # Package initialization
│   ├── cli.py                     # Command-line interface
│   ├── patcher.py                 # Core conversion logic
│   ├── py.typed                   # Type hints marker
│   └── version.py                 # Version information
├── tests/                         # Test suite
│   ├── __init__.py
│   ├── test_cli.py                # CLI tests
│   └── test_patcher.py            # Core functionality tests
├── docs/                          # Documentation
│   └── preview.png
├── LICENSE                        # License file
├── MANIFEST.in                    # Package manifest
├── README.md                      # Main documentation
├── makefile                       # Development commands
├── pyproject.toml                 # Modern Python packaging config
├── requirements.txt               # Dependencies
├── setup.cfg                      # Setuptools configuration
├── setup.py                       # Setuptools setup script
├── tox.ini                        # Tox testing configuration
├── ifc2duckdb.ipynb              # Jupyter notebook (legacy)
├── ifc2duckdb.py                 # Original script (legacy)
└── racbasicsampleproject.ifc     # Sample IFC file
```

## Key Files Description

### Core Package Files

- **`ifc2duckdb/__init__.py`**: Package initialization, exports main classes
- **`ifc2duckdb/patcher.py`**: Core conversion logic (moved from `ifc2duckdb.py`)
- **`ifc2duckdb/cli.py`**: Command-line interface for the package
- **`ifc2duckdb/version.py`**: Version management
- **`ifc2duckdb/py.typed`**: Type hints marker for mypy

### Configuration Files

- **`setup.py`**: Traditional setuptools setup script
- **`pyproject.toml`**: Modern Python packaging configuration (PEP 621)
- **`setup.cfg`**: Additional setuptools configuration
- **`requirements.txt`**: Package dependencies
- **`MANIFEST.in`**: Files to include in package distribution

### Development Files

- **`tox.ini`**: Multi-environment testing configuration
- **`.pre-commit-config.yaml`**: Pre-commit hooks for code quality
- **`makefile`**: Development commands and shortcuts
- **`.gitignore`**: Git ignore patterns

### Testing

- **`tests/`**: Complete test suite with unit tests
- **`tests/test_patcher.py`**: Tests for core conversion functionality
- **`tests/test_cli.py`**: Tests for command-line interface

### Documentation

- **`README.md`**: Comprehensive documentation with examples
- **`examples/basic_usage.py`**: Example script showing usage
- **`docs/`**: Additional documentation assets

### CI/CD

- **`.github/workflows/ci.yml`**: GitHub Actions workflow for testing and deployment

## Package Features

### Installation Methods

1. **From PyPI**: `pip install ifc2duckdb`
2. **From source**: `pip install -e .`
3. **Development**: `pip install -e ".[dev]"`

### Command Line Interface

```bash
ifc2duckdb input.ifc output.duckdb [options]
```

### Python API

```python
import ifc2duckdb
import ifcopenshell

ifc_file = ifcopenshell.open("input.ifc")
patcher = ifc2duckdb.Patcher(ifc_file, database="output.duckdb")
patcher.patch()
```

### Dependencies

- **Core**: `ifcopenshell>=1.0.0`, `duckdb>=0.7.0`, `numpy>=1.20.0`, `ifcpatch>=0.1.0`
- **Development**: `pytest`, `black`, `flake8`, `mypy`, `pre-commit`
- **Documentation**: `sphinx`, `sphinx-rtd-theme`, `myst-parser`

## Development Workflow

### Setup Development Environment

```bash
git clone https://github.com/chuongmep/ifc-2-duckdb.git
cd ifc-2-duckdb
pip install -e ".[dev]"
pre-commit install
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=ifc2duckdb --cov-report=html

# Specific test file
pytest tests/test_patcher.py
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check
```

### Building Package

```bash
# Build wheel and source distribution
make build

# Upload to PyPI (requires credentials)
make upload
```

## Package Distribution

The package is configured for distribution on PyPI with:

- **Wheel distribution** for easy installation
- **Source distribution** for development
- **Automatic versioning** from `version.py`
- **Comprehensive metadata** including classifiers, keywords, and URLs
- **Entry points** for CLI access

## Testing Strategy

- **Unit tests** for core functionality
- **Integration tests** for CLI interface
- **Multi-Python version** testing (3.10, 3.11, 3.12)
- **Code coverage** reporting
- **Type checking** with mypy
- **Linting** with flake8 and black

## Deployment

- **GitHub Actions** for CI/CD
- **Automatic PyPI upload** on main branch pushes
- **Multi-platform** testing support
- **Pre-commit hooks** for code quality

This package structure follows Python packaging best practices and provides a complete, professional-grade Python package ready for distribution and use.
