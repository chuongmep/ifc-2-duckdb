"""Tests for the Patcher class."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ifc2duckdb.patcher import Patcher


class TestPatcher:
    """Test cases for the Patcher class."""

    def test_init_default_values(self):
        """Test Patcher initialization with default values."""
        mock_file = Mock()
        patcher = Patcher(mock_file)
        
        assert patcher.database == "database.duckdb"
        assert patcher.full_schema is True
        assert patcher.is_strict is False
        assert patcher.should_expand is False
        assert patcher.should_get_inverses is True
        assert patcher.should_get_psets is True
        assert patcher.should_get_geometry is True
        assert patcher.should_skip_geometry_data is False

    def test_init_custom_values(self):
        """Test Patcher initialization with custom values."""
        mock_file = Mock()
        patcher = Patcher(
            file=mock_file,
            database="custom.duckdb",
            full_schema=False,
            is_strict=True,
            should_expand=True,
            should_get_inverses=False,
            should_get_psets=False,
            should_get_geometry=False,
            should_skip_geometry_data=True,
        )
        
        assert patcher.database == "custom.duckdb"
        assert patcher.full_schema is False
        assert patcher.is_strict is True
        assert patcher.should_expand is True
        assert patcher.should_get_inverses is False
        assert patcher.should_get_psets is False
        assert patcher.should_get_geometry is False
        assert patcher.should_skip_geometry_data is True

    def test_get_output_before_patch(self):
        """Test get_output before patch is called."""
        mock_file = Mock()
        patcher = Patcher(mock_file)
        assert patcher.get_output() is None

    @patch('ifc2duckdb.patcher.duckdb')
    @patch('ifc2duckdb.patcher.ifcopenshell')
    def test_patch_basic_functionality(self, mock_ifcopenshell, mock_duckdb):
        """Test basic patch functionality."""
        # Setup mocks
        mock_file = Mock()
        mock_file.schema_identifier = "IFC4"
        mock_file.schema = "IFC4"
        mock_file.header.file_description.description = [["Test Description"]]
        mock_file.wrapped_data.types.return_value = ["IfcWall"]
        
        mock_schema = Mock()
        mock_declaration = Mock()
        mock_declaration.attribute_count.return_value = 0
        mock_schema.declaration_by_name.return_value = mock_declaration
        mock_schema.declarations.return_value = []
        mock_ifcopenshell.schema_by_name.return_value = mock_schema
        
        mock_db = Mock()
        mock_cursor = Mock()
        mock_db.cursor.return_value = mock_cursor
        mock_duckdb.connect.return_value = mock_db
        
        # Create patcher and run patch
        patcher = Patcher(mock_file, database="test.duckdb")
        patcher.patch()
        
        # Verify database connection was created
        mock_duckdb.connect.assert_called_once()
        mock_db.cursor.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_db.close.assert_called_once()
        
        # Verify output path is set
        assert patcher.get_output() == "test.duckdb"

    def test_serialise_value(self):
        """Test serialise_value method."""
        mock_file = Mock()
        patcher = Patcher(mock_file)
        
        # Mock element with walk method
        mock_element = Mock()
        mock_element.walk.return_value = "serialized_value"
        
        result = patcher.serialise_value(mock_element, "test_value")
        
        mock_element.walk.assert_called_once()
        assert result == "serialized_value"

    def test_get_permutations(self):
        """Test get_permutations method."""
        mock_file = Mock()
        patcher = Patcher(mock_file)
        
        lst = [1, 2, 3, 4, 5]
        indexes = [1, 3]
        
        result = patcher.get_permutations(lst, indexes)
        
        # Should return all combinations of values at indexes 1 and 3
        expected = [
            [1, 2, 3, 4, 5],  # 2, 4
            [1, 2, 3, 5, 5],  # 2, 5
            [1, 4, 3, 4, 5],  # 4, 4
            [1, 4, 3, 5, 5],  # 4, 5
        ]
        assert len(result) == 4

    def test_is_entity_list(self):
        """Test is_entity_list method."""
        mock_file = Mock()
        patcher = Patcher(mock_file)
        
        # Mock attribute
        mock_attribute = Mock()
        mock_attribute.type_of_attribute.return_value = "<list <entity IfcWall>>"
        
        result = patcher.is_entity_list(mock_attribute)
        assert result is True
        
        # Test non-entity list
        mock_attribute.type_of_attribute.return_value = "<list <string>>"
        result = patcher.is_entity_list(mock_attribute)
        assert result is False
