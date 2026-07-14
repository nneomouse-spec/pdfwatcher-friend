"""Pytest configuration and shared fixtures."""

import pytest
from pathlib import Path

# Ensure src is importable
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from detoplus.invoice_renamer.identity import SettingsRepository
from detoplus.invoice_renamer.extraction.reader import clear_cache


@pytest.fixture(autouse=True)
def clear_pdf_cache():
    """Clear the PDF text cache between tests."""
    clear_cache()


@pytest.fixture
def sample_mappings() -> dict:
    """Sample mapping table: Kundennummer → (Standort, Firma)."""
    return {
        "Avacon": [
            {"kundennummer": "215000385783", "standort": "Solarpark Musterstadt", "firma": "D5"},
            {"kundennummer": "215000123456", "standort": "Solarpark Beispiel", "firma": "D2"},
        ],
        "Mitnetz": [
            {"kundennummer": "316840090503", "standort": "Windpark Nord", "firma": "I1"},
        ],
        "TEN": [
            {"kundennummer": "50023840-27078391", "standort": "Solarpark Süd", "firma": "D3"},
        ],
        "Lichtblick": [
            {"kundennummer": "12345678", "standort": "Dachanlage Berlin", "firma": "K261"},
        ],
    }


@pytest.fixture
def temp_settings_repo(tmp_path):
    """Temporary SettingsRepository for isolated tests."""
    repo = SettingsRepository(tmp_path / "test_settings.json")
    yield repo
    # Cleanup
    p = tmp_path / "test_settings.json"
    if p.exists():
        p.unlink()
