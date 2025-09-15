# IfcPatch - IFC to DuckDB conversion utility
# Copyright chuongmep (C) 2025
#
# This file is based on the existing Ifc2Sql recipe but simplified to
# support DuckDB only. It mirrors the public behaviour of Ifc2Sql
# (SQLite mode) while using DuckDB specific data types where useful.
#
# SPDX-License-Identifier: LGPL-3.0-or-later

from __future__ import annotations

import itertools
import json
import logging
import os
import re
import time
from typing import Any, Union, Optional

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.ifcopenshell_wrapper as W
import ifcopenshell.util.attribute
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.representation
import ifcopenshell.util.schema
import ifcopenshell.util.shape
import ifcopenshell.util.unit
import ifcpatch
import numpy as np

# DuckDB will be imported in the patch method when needed

DEFAULT_DATABASE_NAME = "database.duckdb"

# Data type mapping for DuckDB (chosen to stay close to SQLite logic)
# - TEXT -> TEXT
# - INTEGER -> BIGINT
# - REAL -> DOUBLE
# - JSON -> JSON
# - BLOB -> BLOB
# DuckDB supports JSON natively (>=0.7). We rely on that.


class Patcher(ifcpatch.BasePatcher):
    """Convert an IFC-SPF model to a DuckDB database.

    Parameters mirror a subset of the original Ifc2Sql patcher geared for
    SQLite. Only the arguments relevant to behaviour are retained.
    """

    def __init__(
        self,
        file: ifcopenshell.file,
        logger: Union[logging.Logger, None] = None,
        database: str = DEFAULT_DATABASE_NAME,
        full_schema: bool = True,
        is_strict: bool = False,
        should_expand: bool = False,
        should_get_inverses: bool = True,
        should_get_psets: bool = True,
        should_get_geometry: bool = True,
        should_skip_geometry_data: bool = False,
    ) -> None:
        super().__init__(file, logger)
        # Configure logger
        if logger is None:
            configured_logger = logging.getLogger("ifc2duckdb")
            if not configured_logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    fmt="%(asctime)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                handler.setFormatter(formatter)
                configured_logger.addHandler(handler)
                configured_logger.setLevel(logging.INFO)
            self.logger = configured_logger
        else:
            self.logger = logger
        self.database = database
        self.full_schema = full_schema
        self.is_strict = is_strict
        self.should_expand = should_expand
        self.should_get_inverses = should_get_inverses
        self.should_get_psets = should_get_psets
        self.should_get_geometry = should_get_geometry
        self.should_skip_geometry_data = should_skip_geometry_data

        self.file_patched: Union[str, None] = None

    geometry_rows: dict[str, tuple[str, bytes, bytes, bytes, bytes, str]]
    shape_rows: dict[int, tuple[int, float, float, float, bytes, Union[str, None]]]

    def get_output(self) -> Union[str, None]:
        return self.file_patched

    def patch(self) -> None:
        from pathlib import Path

        import duckdb
        import ifcopenshell

        database = Path(self.database)
        if database.is_dir():
            database = database / "default.duckdb"
        elif not database.parent.exists():
            database.parent.mkdir(parents=True, exist_ok=True)
        if database.suffix.lower() != ".duckdb":
            database = database.with_suffix(database.suffix + ".duckdb")

        self.schema = ifcopenshell.schema_by_name(self.file.schema_identifier)
        self.db = duckdb.connect(str(database))
        self.c = self.db.cursor()
        self.file_patched = str(database)

        self.check_existing_ifc_database()
        self.create_id_map()
        self.create_metadata()

        if self.should_get_psets:
            self.create_pset_table()

        if self.should_get_geometry:
            self.create_geometry_table()
            self.create_geometry()

        if self.full_schema:
            ifc_classes = [
                d.name()
                for d in self.schema.declarations()
                if isinstance(d, ifcopenshell.ifcopenshell_wrapper.entity)
            ]
        else:
            ifc_classes = self.file.wrapped_data.types()

        for ifc_class in ifc_classes:
            declaration = self.schema.declaration_by_name(ifc_class)
            if self.should_skip_geometry_data and (
                ifcopenshell.util.schema.is_a(declaration, "IfcRepresentation")
                or ifcopenshell.util.schema.is_a(declaration, "IfcRepresentationItem")
            ):
                continue
            self.create_table(ifc_class, declaration)
            self.insert_data(ifc_class)

        # Fix executemany input: convert dict_values to list of tuples
        if self.should_get_geometry:
            if self.shape_rows:
                shape_values = [tuple(v) for v in self.shape_rows.values()]
                if shape_values:  # ensure not empty
                    self.c.executemany(
                        "INSERT INTO shape VALUES (?, ?, ?, ?, ?, ?);", shape_values
                    )

            if self.geometry_rows:
                geometry_values = [tuple(v) for v in self.geometry_rows.values()]
                if geometry_values:  # ensure not empty
                    self.c.executemany(
                        "INSERT INTO geometry VALUES (?, ?, ?, ?, ?, ?);",
                        geometry_values,
                    )

        self.db.commit()
        self.c.close()
        self.db.close()

    # ---- Schema helpers ----
    def check_existing_ifc_database(self) -> None:
        try:
            row = self.c.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_name='id_map'"
            ).fetchone()
        except Exception:  # information_schema may differ or not list before creation
            row = None
        if row is not None:
            print(
                "WARNING. DuckDB database already appears to contain IFC data ('id_map' table found). "
                "This could lead to mixed ids or duplicate content."
            )

    def create_id_map(self) -> None:
        self.c.execute(
            "CREATE TABLE IF NOT EXISTS id_map (ifc_id BIGINT PRIMARY KEY, ifc_class TEXT NOT NULL);"
        )

    def create_metadata(self) -> None:
        metadata = [
            "IfcOpenShell-1.0.0",
            self.file.schema,
            self.file.header.file_description.description[0],
        ]
        self.c.execute(
            "CREATE TABLE IF NOT EXISTS metadata (preprocessor TEXT, schema TEXT, mvd TEXT);"
        )
        self.c.execute("INSERT INTO metadata VALUES (?, ?, ?);", metadata)

    def create_pset_table(self) -> None:
        self.c.execute(
            """
            CREATE TABLE IF NOT EXISTS psets (
                ifc_id BIGINT NOT NULL,
                pset_name TEXT,
                name TEXT,
                value TEXT
            );
            """
        )

    def create_geometry_table(self) -> None:
        self.c.execute(
            """
            CREATE TABLE IF NOT EXISTS shape (
                ifc_id BIGINT NOT NULL,
                x DOUBLE,
                y DOUBLE,
                z DOUBLE,
                matrix BLOB,
                geometry TEXT
            );
            """
        )
        self.c.execute(
            """
            CREATE TABLE IF NOT EXISTS geometry (
                id TEXT NOT NULL,
                verts BLOB,
                edges BLOB,
                faces BLOB,
                material_ids BLOB,
                materials JSON
            );
            """
        )

    def create_table(
        self, ifc_class: str, declaration: ifcopenshell.ifcopenshell_wrapper.declaration
    ) -> None:
        # Start CREATE TABLE statement, quote table name
        statement = f'CREATE TABLE IF NOT EXISTS "{ifc_class}" ('

        # Add ifc_id column
        if self.should_expand:
            statement += "ifc_id BIGINT NOT NULL"
        else:
            statement += "ifc_id BIGINT PRIMARY KEY"

        # Validate declaration
        assert isinstance(declaration, ifcopenshell.ifcopenshell_wrapper.entity)
        total_attributes = declaration.attribute_count()
        if total_attributes:
            statement += ", "

        derived = declaration.derived()
        for i in range(total_attributes):
            attribute = declaration.attribute_by_index(i)
            primitive = ifcopenshell.util.attribute.get_primitive_type(attribute)

            # Determine data type
            if primitive in ("string", "enum", "binary"):
                data_type = "TEXT"
            elif primitive in ("entity", "integer", "boolean"):
                data_type = "BIGINT"
            elif primitive == "float":
                data_type = "DOUBLE"
            elif self.should_expand and self.is_entity_list(attribute):
                data_type = "BIGINT"
            elif isinstance(primitive, tuple):
                data_type = "JSON"
            else:
                data_type = "TEXT"
                print(
                    "Possibly not implemented attribute data type:",
                    attribute,
                    primitive,
                )

            # Handle optional/NOT NULL
            if not self.is_strict or derived[i]:
                optional = ""
            else:
                optional = "" if attribute.optional() else " NOT NULL"

            # Add comma if not last column
            comma = "" if i == total_attributes - 1 else ", "

            # Add column, quote attribute name (double quotes)
            statement += f'"{attribute.name()}" {data_type}{optional}{comma}'

        # Add inverses column if needed
        if self.should_get_inverses:
            statement += ", inverses JSON"

        # Close statement
        statement += ");"

        # Execute
        self.c.execute(statement)

    def insert_data(self, ifc_class: str, batch_size: int = 1000) -> None:
        """
        Insert data of a specific IFC class into the database.
        Optimized for large datasets using batching and transactions.
        """
        elements = self.file.by_type(ifc_class, include_subtypes=False)
        rows: list[list[Any]] = []
        id_map_rows: list[tuple[int, str]] = []
        pset_rows: list[tuple[int, str, str, Any]] = []

        def batch_insert(cursor: Any, table_name: str, data: list[Any], batch_size: int = batch_size) -> None:
            for i in range(0, len(data), batch_size):
                batch = data[i : i + batch_size]
                cursor.executemany(
                    f"INSERT INTO {table_name} VALUES ({','.join(['?'] * len(batch[0]))});",
                    batch,
                )

        for element in elements:
            nested_indices: list[int] = []
            values: list[Any] = [element.id()]

            for i, attribute in enumerate(element):
                if isinstance(attribute, ifcopenshell.entity_instance):
                    if attribute.id():
                        values.append(attribute.id())
                    else:
                        values.append(
                            json.dumps(
                                {
                                    "type": attribute.is_a(),
                                    "value": attribute.wrappedValue,
                                }
                            )
                        )
                elif (
                    self.should_expand
                    and attribute
                    and isinstance(attribute, tuple)
                    and isinstance(attribute[0], ifcopenshell.entity_instance)
                ):
                    nested_indices.append(i + 1)
                    serialized = self.serialise_value(element, attribute)
                    if attribute[0].id():
                        values.append(serialized)
                    else:
                        values.append(json.dumps(serialized))
                elif isinstance(attribute, tuple):
                    values.append(json.dumps(self.serialise_value(element, attribute)))
                else:
                    values.append(attribute)

            if self.should_get_inverses:
                inverse_ids = [e.id() for e in self.file.get_inverse(element)]
                values.append(json.dumps(inverse_ids))

            if self.should_expand:
                rows.extend(self.get_permutations(values, nested_indices))
            else:
                rows.append(values)

            id_map_rows.append((element.id(), ifc_class))

            if self.should_get_psets:
                psets = ifcopenshell.util.element.get_psets(element)
                for pset_name, pset_data in psets.items():
                    for prop_name, value in pset_data.items():
                        if prop_name == "id":
                            continue
                        if isinstance(value, list):
                            value = json.dumps(value)
                        pset_rows.append((element.id(), pset_name, prop_name, value))

            if self.should_get_geometry and element.id() not in self.shape_rows:
                if placement := getattr(element, "ObjectPlacement", None):
                    m = ifcopenshell.util.placement.get_local_placement(placement)
                    x, y, z = m[:, 3][0:3].tolist()
                    self.shape_rows[element.id()] = (
                        element.id(),
                        x,
                        y,
                        z,
                        m.tobytes(),
                        None,
                    )

        # ---- Insert into database using transaction + batching ----
        if rows or id_map_rows or pset_rows:
            self.c.execute("BEGIN;")
            if rows:
                batch_insert(self.c, ifc_class, rows, batch_size)
            if id_map_rows:
                batch_insert(self.c, "id_map", id_map_rows, batch_size)
            if pset_rows:
                batch_insert(self.c, "psets", pset_rows, batch_size)
            self.c.execute("COMMIT;")

    # ---- Geometry ----
    def create_geometry(self) -> None:
        self.unit_scale = ifcopenshell.util.unit.calculate_unit_scale(self.file)
        self.shape_rows = {}
        self.geometry_rows = {}

        if self.file.schema in ("IFC2X3", "IFC4"):
            elements = self.file.by_type("IfcElement") + self.file.by_type("IfcProxy")
        else:
            elements = self.file.by_type("IfcElement")

        self.settings = ifcopenshell.geom.settings()
        self.settings.set("apply-default-materials", False)

        body_contexts = [
            c.id()
            for c in self.file.by_type("IfcGeometricRepresentationSubContext")
            if c.ContextIdentifier in ["Body", "Facetation"]
        ]
        body_contexts.extend(
            [
                c.id()
                for c in self.file.by_type(
                    "IfcGeometricRepresentationContext", include_subtypes=False
                )
                if c.ContextType == "Model"
            ]
        )
        self.settings.set("context-ids", body_contexts)

        products = elements
        iterator = ifcopenshell.geom.iterator(
            self.settings, self.file, os.cpu_count() or 1, include=products
        )
        if not iterator.initialize():
            if products:
                print("WARNING. Geometry iterator failed to initialize.")
            return
        start_time = time.time()
        checkpoint = start_time
        progress = 0
        total = len(products)
        while True:
            progress += 1
            if progress % 250 == 0:
                percent_created = round(progress / total * 100) if total else 100
                percent_preprocessed = iterator.progress()
                elapsed_since_checkpoint = time.time() - checkpoint
                elapsed_total = time.time() - start_time
                rate = (250 / elapsed_since_checkpoint) if elapsed_since_checkpoint > 0 else 0.0
                remaining = total - progress
                eta_seconds = (remaining / rate) if rate > 0 else 0.0
                self.logger.info(
                    "Processed %d/%d | created=%d%% preprocessed=%d%% | batch=%.2fs rate=%.1f/s | elapsed=%.2fs ETA=%.2fs",
                    progress,
                    total,
                    percent_created,
                    percent_preprocessed,
                    elapsed_since_checkpoint,
                    rate,
                    elapsed_total,
                    eta_seconds,
                )
                checkpoint = time.time()
            shape = iterator.get()
            if shape:
                assert isinstance(shape, W.TriangulationElement)
                shape_id = shape.id
                geometry = shape.geometry
                geometry_id = geometry.id
                if geometry_id not in self.geometry_rows:
                    self.add_geometry_row(geometry_id, geometry)
                m = ifcopenshell.util.shape.get_shape_matrix(shape).copy()
                m[:3, 3] /= self.unit_scale
                x, y, z = m[:, 3][0:3].tolist()
                self.shape_rows[shape_id] = (
                    shape_id,
                    x,
                    y,
                    z,
                    m.tobytes(),
                    geometry_id,
                )
            if not iterator.next():
                break

        element_types = self.file.by_type("IfcElementType")
        body_contexts_objs = [self.file.by_id(i) for i in body_contexts]
        m_bytes = np.eye(4, dtype=np.float64).tobytes()
        for element_type in element_types:
            representation = None
            for context in body_contexts_objs:
                representation = ifcopenshell.util.representation.get_representation(
                    element_type, context
                )
                if representation:
                    break
            element_geometry_id: Optional[str] = None
            if representation:
                geometry_id_ = str(representation.id())
                if geometry_id_ in self.geometry_rows:
                    element_geometry_id = geometry_id_
                else:
                    element_geometry: Any = ifcopenshell.geom.create_shape(
                        self.settings, representation
                    )
                    if element_geometry is not None:
                        element_geometry_id = geometry_id_
                        assert isinstance(element_geometry, W.Triangulation)
                        self.add_geometry_row(element_geometry_id, element_geometry)
            shape_id = element_type.id()
            self.shape_rows[shape_id] = (
                shape_id,
                *(0.0, 0.0, 0.0),
                m_bytes,
                element_geometry_id,
            )

    def add_geometry_row(self, geometry_id: str, geometry: W.Triangulation) -> None:
        v = geometry.verts_buffer
        e = geometry.edges_buffer
        f = geometry.faces_buffer
        mids = geometry.material_ids_buffer
        m = json.dumps([m.instance_id() for m in geometry.materials])
        self.geometry_rows[geometry_id] = (geometry_id, v, e, f, mids, m)

    # ---- Utilities ----
    def serialise_value(self, element: ifcopenshell.entity_instance, value: Any) -> Any:
        return element.walk(
            lambda v: isinstance(v, ifcopenshell.entity_instance),
            lambda v: v.id() if v.id() else {"type": v.is_a(), "value": v.wrappedValue},
            value,
        )

    def get_permutations(self, lst: list[Any], indexes: list[int]) -> list[Any]:
        nested_lists = [lst[i] for i in indexes]
        products = list(itertools.product(*nested_lists))
        final_lists = []
        for product in products:
            temp_list = lst[:]
            for i, index in enumerate(indexes):
                temp_list[index] = product[i]
            final_lists.append(temp_list)
        return final_lists

    def is_entity_list(
        self, attribute: ifcopenshell.ifcopenshell_wrapper.attribute
    ) -> bool:
        attr = str(attribute.type_of_attribute())
        if (attr.startswith("<list") or attr.startswith("<set")) and "<entity" in attr:
            for data_type in re.findall("<(.*?) .*?>", attr):
                if data_type not in ("list", "set", "select", "entity"):
                    return False
            return True
        return False
