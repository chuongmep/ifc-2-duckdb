# ifc2duckdb

convert ifc to duckdb format, fast analyst and read  

# Requirements

- Python 3.10+
- ifcopenshell
- duckdb

## How to usage 

```py
import ifc2duckdb
import ifcopenshell
    # For SQLite
patcher = ifc2duckdb.Patcher(
    ifcopenshell.open("racbasicsampleproject.ifc"),
    database="output.duckdb", # Path to your SQLite database file
    # Optional arguments:
    # full_schema=True,
    # is_strict=False,
    # should_expand=True,
    # should_get_inverses=True,
    # should_get_psets=True,
    # should_get_geometry=True,
)
patcher.patch()
```

## Reference

- https://docs.ifcopenshell.org/autoapi/ifcpatch/index.html
- https://docs.ifcopenshell.org/ifcpatch.html
- https://community.osarch.org/discussion/1535/ifc-stored-as-sqlite-and-mysql
- https://github.com/xBimTeam/XbimEssentials
- https://github.com/IfcOpenShell/IfcOpenShell/blob/v0.7.0/src/ifcpatch/ifcpatch/recipes/Ifc2Sql.py
- https://duckdb.org/docs/stable/guides/network_cloud_storage/duckdb_over_https_or_s3.html
