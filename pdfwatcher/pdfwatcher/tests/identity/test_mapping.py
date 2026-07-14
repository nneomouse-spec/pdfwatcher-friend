"""Unit tests for identity resolution."""

from detoplus.invoice_renamer.identity import resolve_identity, Identity, UNKNOWN
from detoplus.invoice_renamer.identity.repository import SettingsRepository


class TestResolveIdentity:

    def test_known_kundennummer_returns_identity(self, sample_mappings):
        result = resolve_identity("215000385783", "Avacon", sample_mappings)
        assert result == Identity(standort="Solarpark Musterstadt", firma="D5")

    def test_unknown_kundennummer_returns_unknown(self, sample_mappings):
        result = resolve_identity("999999999999", "Avacon", sample_mappings)
        assert result == UNKNOWN

    def test_none_key_returns_unknown(self, sample_mappings):
        result = resolve_identity(None, "Avacon", sample_mappings)
        assert result == UNKNOWN

    def test_empty_key_returns_unknown(self, sample_mappings):
        result = resolve_identity("", "Avacon", sample_mappings)
        assert result == UNKNOWN

    def test_unknown_company_returns_unknown(self, sample_mappings):
        result = resolve_identity("123", "NonexistentCorp", sample_mappings)
        assert result == UNKNOWN

    def test_identity_is_resolved(self):
        assert Identity(standort="A", firma="B").is_resolved is True
        assert Identity(standort="", firma="").is_resolved is False
        assert Identity(standort="A", firma="").is_resolved is False

    def test_mitnetz_mapping(self, sample_mappings):
        result = resolve_identity("316840090503", "Mitnetz", sample_mappings)
        assert result.firma == "I1"
        assert result.standort == "Windpark Nord"

    def test_ten_composite_key(self, sample_mappings):
        result = resolve_identity("50023840-27078391", "TEN", sample_mappings)
        assert result.standort == "Solarpark Süd"


class TestSettingsRepository:

    def test_read_empty_file(self, temp_settings_repo):
        assert temp_settings_repo.read() == {}

    def test_write_and_read(self, temp_settings_repo):
        data = {"theme": "dark", "lang": "de"}
        temp_settings_repo.write(data)
        assert temp_settings_repo.read() == data

    def test_update_preserves_existing(self, temp_settings_repo):
        temp_settings_repo.write({"theme": "dark", "lang": "de", "window_geometry": "1200x800"})
        temp_settings_repo.update(lang="en")
        result = temp_settings_repo.read()
        assert result["lang"] == "en"
        assert result["theme"] == "dark"  # preserved!
        assert result["window_geometry"] == "1200x800"  # preserved!

    def test_update_returns_merged(self, temp_settings_repo):
        temp_settings_repo.write({"a": 1})
        result = temp_settings_repo.update(b=2)
        assert result == {"a": 1, "b": 2}
