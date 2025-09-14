#!/usr/bin/env python3
"""
Basic usage example for ifc2duckdb.

This script demonstrates how to convert an IFC file to DuckDB format
and perform some basic queries on the resulting database.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import ifc2duckdb
sys.path.insert(0, str(Path(__file__).parent.parent))

import ifc2duckdb
import ifcopenshell
import duckdb


def main():
    """Main function demonstrating basic usage."""
    # Path to the sample IFC file
    ifc_file_path = Path(__file__).parent.parent / "racbasicsampleproject.ifc"
    output_db_path = "example_output.duckdb"
    
    if not ifc_file_path.exists():
        print(f"Error: IFC file not found at {ifc_file_path}")
        print("Please ensure the sample IFC file is available.")
        return
    
    print(f"Converting IFC file: {ifc_file_path}")
    print(f"Output database: {output_db_path}")
    
    try:
        # Open the IFC file
        ifc_file = ifcopenshell.open(str(ifc_file_path))
        print(f"IFC file loaded successfully. Schema: {ifc_file.schema}")
        
        # Create the patcher with default settings
        patcher = ifc2duckdb.Patcher(
            ifc_file,
            database=output_db_path,
            full_schema=True,        # Create full IFC schema
            should_get_geometry=True,  # Include geometry data
            should_get_psets=True,   # Include property sets
            should_get_inverses=True # Include inverse relationships
        )
        
        # Convert to DuckDB
        print("Converting to DuckDB...")
        patcher.patch()
        
        output_path = patcher.get_output()
        if output_path:
            print(f"Conversion completed successfully!")
            print(f"Database created at: {output_path}")
            
            # Demonstrate some basic queries
            demonstrate_queries(output_path)
        else:
            print("Error: Conversion failed - no output file generated.")
            
    except Exception as e:
        print(f"Error during conversion: {e}")
        import traceback
        traceback.print_exc()


def demonstrate_queries(db_path: str):
    """Demonstrate some basic queries on the converted database."""
    print("\n" + "="*50)
    print("DEMONSTRATING BASIC QUERIES")
    print("="*50)
    
    try:
        # Connect to the database
        conn = duckdb.connect(db_path)
        cursor = conn.cursor()
        
        # Query 1: Show available tables
        print("\n1. Available tables:")
        tables = cursor.execute("SHOW TABLES").fetchall()
        for table in tables:
            print(f"   - {table[0]}")
        
        # Query 2: Count entities by type
        print("\n2. Entity counts by type:")
        try:
            entity_counts = cursor.execute("""
                SELECT ifc_class, COUNT(*) as count 
                FROM id_map 
                GROUP BY ifc_class 
                ORDER BY count DESC 
                LIMIT 10
            """).fetchall()
            for entity_type, count in entity_counts:
                print(f"   - {entity_type}: {count}")
        except Exception as e:
            print(f"   Error querying entity counts: {e}")
        
        # Query 3: Show metadata
        print("\n3. IFC file metadata:")
        try:
            metadata = cursor.execute("SELECT * FROM metadata").fetchall()
            for row in metadata:
                print(f"   - Preprocessor: {row[0]}")
                print(f"   - Schema: {row[1]}")
                print(f"   - Description: {row[2]}")
        except Exception as e:
            print(f"   Error querying metadata: {e}")
        
        # Query 4: Show some geometry data
        print("\n4. Geometry data sample:")
        try:
            geometry_sample = cursor.execute("""
                SELECT s.ifc_id, s.x, s.y, s.z, g.id as geometry_id
                FROM shape s
                LEFT JOIN geometry g ON s.geometry = g.id
                LIMIT 5
            """).fetchall()
            for row in geometry_sample:
                print(f"   - ID: {row[0]}, Position: ({row[1]:.2f}, {row[2]:.2f}, {row[3]:.2f}), Geometry: {row[4]}")
        except Exception as e:
            print(f"   Error querying geometry: {e}")
        
        # Query 5: Show property sets
        print("\n5. Property sets sample:")
        try:
            pset_sample = cursor.execute("""
                SELECT pset_name, name, value
                FROM psets
                LIMIT 10
            """).fetchall()
            for row in pset_sample:
                print(f"   - {row[0]}.{row[1]}: {row[2]}")
        except Exception as e:
            print(f"   Error querying property sets: {e}")
        
        conn.close()
        print(f"\nQueries completed. Database is ready for analysis!")
        print(f"You can open it with: duckdb {db_path}")
        
    except Exception as e:
        print(f"Error during query demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
