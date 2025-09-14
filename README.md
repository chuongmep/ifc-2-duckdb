# ifc2duckdb

Convert IFC files to DuckDB format for fast analysis and querying of Building Information Modeling (BIM) data.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-LGPL--3.0--or--later-green.svg)](https://spdx.org/licenses/LGPL-3.0-or-later.html)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

![](./docs/ifc2duckdb.png)

## Features

- **Fast Conversion**: Convert IFC files to DuckDB format for high-performance querying
- **Full Schema Support**: Create complete IFC schema tables or only those present in the file
- **Geometry Support**: Extract and store 3D geometry data with materials
- **Property Sets**: Include IFC property set data
- **Inverse Relationships**: Store entity relationships for complex queries
- **Command Line Interface**: Easy-to-use CLI for batch processing
- **Python API**: Programmatic access for integration into larger workflows

## Installation

### From PyPI (recommended)

```bash
pip install ifc2duckdb
```

### From source

```bash
git clone https://github.com/chuongmep/ifc-2-duckdb.git
cd ifc-2-duckdb
pip install -e .
```

### Development installation

```bash
git clone https://github.com/chuongmep/ifc-2-duckdb.git
cd ifc-2-duckdb
pip install -e ".[dev]"
```

## Requirements

- Python 3.10+
- ifcopenshell >= 1.0.0
- duckdb >= 0.7.0
- numpy >= 1.20.0
- ifcpatch >= 0.1.0

## Quick Start

### Command Line Usage

```bash
# Basic conversion
ifc2duckdb input.ifc output.duckdb

# With options
ifc2duckdb input.ifc --database output.duckdb --no-geometry --verbose

# Help
ifc2duckdb --help
```

### Python API Usage

```python
import ifc2duckdb
import ifcopenshell

# Open IFC file
ifc_file = ifcopenshell.open("racbasicsampleproject.ifc")

# Create patcher with default settings
patcher = ifc2duckdb.Patcher(
    ifc_file,
    database="output.duckdb"
)

# Convert to DuckDB
patcher.patch()

# Get output path
output_path = patcher.get_output()
print(f"Database created at: {output_path}")
```

### Advanced Usage

```python
import ifc2duckdb
import ifcopenshell

# Open IFC file
ifc_file = ifcopenshell.open("racbasicsampleproject.ifc")

# Create patcher with custom settings
patcher = ifc2duckdb.Patcher(
    ifc_file,
    database="output.duckdb",
    full_schema=False,           # Only create tables for classes in the file
    is_strict=True,              # Strict data type validation
    should_expand=True,          # Expand entity lists into separate rows
    should_get_inverses=True,    # Include inverse relationships
    should_get_psets=True,       # Include property set data
    should_get_geometry=True,    # Include geometry data
    should_skip_geometry_data=False  # Include geometry for representation tables
)

# Convert to DuckDB
patcher.patch()
```

## Database Schema

The converted DuckDB database contains several types of tables:

### Core Tables
- **`id_map`**: Maps IFC entity IDs to their class names
- **`metadata`**: Contains IFC file metadata (schema, preprocessor info)

### IFC Entity Tables
- One table per IFC class (e.g., `IfcWall`, `IfcDoor`, `IfcWindow`)
- Each table contains all attributes of the IFC entity
- Primary key is `ifc_id` (the IFC entity ID)

### Geometry Tables
- **`shape`**: Contains placement and transformation data
- **`geometry`**: Contains mesh data (vertices, edges, faces, materials)

### Property Set Tables
- **`psets`**: Contains property set data in key-value format

## Querying Examples

```sql
-- Find all walls
SELECT * FROM "IfcWall";

-- Find walls with specific properties
SELECT w.*, p.name, p.value 
FROM "IfcWall" w
JOIN psets p ON w.ifc_id = p.ifc_id
WHERE p.pset_name = 'Pset_WallCommon';

-- Get geometry for all elements
SELECT s.*, g.verts, g.faces
FROM shape s
JOIN geometry g ON s.geometry = g.id;

-- Find elements by material
SELECT s.ifc_id, g.materials
FROM shape s
JOIN geometry g ON s.geometry = g.id
WHERE g.materials LIKE '%concrete%';
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ifc2duckdb --cov-report=html

# Run specific test file
pytest tests/test_patcher.py
```

### Code Formatting

```bash
# Format code
black ifc2duckdb tests
isort ifc2duckdb tests

# Check formatting
black --check ifc2duckdb tests
isort --check-only ifc2duckdb tests
```

### Type Checking

```bash
mypy ifc2duckdb --ignore-missing-imports
```

### Linting

```bash
flake8 ifc2duckdb tests
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`make test lint`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later) - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on the [Ifc2Sql](https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.7.0/src/ifcpatch/ifcpatch/recipes/Ifc2Sql.py) recipe from IfcOpenShell
- Inspired by the [XbimEssentials](https://github.com/xBimTeam/XbimEssentials) project
- Built on top of [IfcOpenShell](https://ifcopenshell.org/) and [DuckDB](https://duckdb.org/)

## References

- [IfcOpenShell Documentation](https://docs.ifcopenshell.org/)
- [IfcPatch Documentation](https://docs.ifcopenshell.org/ifcpatch.html)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [OSArch Community Discussion](https://community.osarch.org/discussion/1535/ifc-stored-as-sqlite-and-mysql)
- [DuckDB Cloud Storage](https://duckdb.org/docs/stable/guides/network_cloud_storage/duckdb_over_https_or_s3.html)
