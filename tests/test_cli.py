"""Tests for the CLI module."""

import sys
from unittest.mock import Mock, patch

import pytest

from ifc2duckdb.cli import main, setup_logging


class TestCLI:
    """Test cases for the CLI module."""

    def test_setup_logging_verbose(self):
        """Test logging setup with verbose mode."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(verbose=True)
            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args
            assert call_args[1]['level'] == 20  # DEBUG level

    def test_setup_logging_normal(self):
        """Test logging setup in normal mode."""
        with patch('logging.basicConfig') as mock_basic_config:
            setup_logging(verbose=False)
            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args
            assert call_args[1]['level'] == 20  # INFO level

    @patch('ifc2duckdb.cli.ifcopenshell')
    @patch('ifc2duckdb.cli.Patcher')
    @patch('sys.argv', ['ifc2duckdb', 'test.ifc', '--database', 'output.duckdb'])
    def test_main_success(self, mock_patcher_class, mock_ifcopenshell):
        """Test successful CLI execution."""
        # Setup mocks
        mock_file = Mock()
        mock_ifcopenshell.open.return_value = mock_file
        
        mock_patcher = Mock()
        mock_patcher.get_output.return_value = "output.duckdb"
        mock_patcher_class.return_value = mock_patcher
        
        # Mock Path.exists to return True for input file
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.print') as mock_print:
                main()
        
        # Verify file was opened
        mock_ifcopenshell.open.assert_called_once_with("test.ifc")
        
        # Verify patcher was created and called
        mock_patcher_class.assert_called_once()
        mock_patcher.patch.assert_called_once()
        
        # Verify success message was printed
        assert any("Conversion completed successfully!" in str(call) for call in mock_print.call_args_list)

    @patch('sys.argv', ['ifc2duckdb', 'nonexistent.ifc'])
    def test_main_file_not_found(self):
        """Test CLI with non-existent input file."""
        with patch('pathlib.Path.exists', return_value=False):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch('ifc2duckdb.cli.ifcopenshell')
    @patch('sys.argv', ['ifc2duckdb', 'test.ifc'])
    def test_main_ifc_open_error(self, mock_ifcopenshell):
        """Test CLI when IFC file cannot be opened."""
        mock_ifcopenshell.open.side_effect = Exception("Cannot open IFC file")
        
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    @patch('ifc2duckdb.cli.ifcopenshell')
    @patch('ifc2duckdb.cli.Patcher')
    @patch('sys.argv', ['ifc2duckdb', 'test.ifc', '--verbose'])
    def test_main_verbose_mode(self, mock_patcher_class, mock_ifcopenshell):
        """Test CLI with verbose mode."""
        # Setup mocks
        mock_file = Mock()
        mock_ifcopenshell.open.return_value = mock_file
        
        mock_patcher = Mock()
        mock_patcher.get_output.return_value = "database.duckdb"
        mock_patcher_class.return_value = mock_patcher
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('ifc2duckdb.cli.setup_logging') as mock_setup_logging:
                main()
        
        # Verify verbose logging was set up
        mock_setup_logging.assert_called_once_with(True)
