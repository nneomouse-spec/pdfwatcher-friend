"""Unit tests for filename assembly."""

from detoplus.invoice_renamer.naming import build_filename, RenameStatus
from detoplus.invoice_renamer.identity import Identity


class TestBuildFilename:

    def test_full_filename_with_mapping(self):
        identity = Identity(standort="Solarpark Musterstadt", firma="D5")
        name, status, info = build_filename(
            company="Avacon",
            kundennummer="215000385783",
            date_str="20260228",
            rechnungsnr="311140059500",
            zeitraum="2026.02",
            doc_type="AR",
            identity=identity,
        )
        assert name is not None
        parts = name.replace(".pdf", "").split(" ")
        assert parts[0] == "D5"            # Our company
        assert parts[1] == "AR"            # Doc type
        assert "20260228" in parts         # Date
        assert "Avacon" in parts           # Network provider
        assert "215000385783" in parts     # Kundennummer
        # Standort appears (space-separated, so split across tokens)
        assert "Solarpark" in parts
        assert "Musterstadt" in parts
        assert "2026.02_311140059500" in parts   # Zeitraum_Rechnungsnr
        assert status == RenameStatus.OK

    def test_redispatch_appended(self):
        name, status, info = build_filename(
            company="Avacon",
            date_str="20260228",
            rechnungsnr="12345",
            zeitraum="2026.02",
            doc_type="AR",
            raw_text="Dies ist ein Redispatch Dokument",
        )
        assert "Redispatch" in (name or "")

    def test_storno_appended(self):
        name, status, info = build_filename(
            company="Mitnetz",
            date_str="20260409",
            rechnungsnr="99999",
            doc_type="AR",
            raw_text="Stornorechnung vom April",
        )
        assert "Storno" in (name or "")

    def test_gutschrift_not_appended(self):
        name, status, info = build_filename(
            company="Avacon",
            date_str="20260228",
            rechnungsnr="11111",
            doc_type="AR",
            raw_text="Gutschrift für Januar 2026",
        )
        assert "Gutschrift" not in (name or "")

    def test_no_fields_returns_low_confidence(self):
        name, status, info = build_filename(
            company="Avacon",
            doc_type="AR",
        )
        assert name is None
        assert status == RenameStatus.MANUAL

    def test_partial_fields_returns_incomplete(self):
        name, status, info = build_filename(
            company="Avacon",
            date_str="20260228",
            zeitraum="2026.02",
            doc_type="AR",
        )
        # Date (35) + Zeitraum (20) = 55, above partial (50) but below OK (85)
        assert status == RenameStatus.INCOMPLETE

    def test_zeitraum_over_35_days_uses_year_only(self):
        name, status, info = build_filename(
            company="Avacon",
            date_str="20260415",
            rechnungsnr="12345",
            zeitraum="01.2026-04.2026",  # ~90 days
            doc_type="AR",
        )
        assert name is not None
        # Date should be year-only
        assert "2026" in name
        assert "20260415" not in name

    def test_sanitize_illegal_chars(self):
        name, status, info = build_filename(
            company="Test:Netz*",
            date_str="20260228",
            rechnungsnr="12345",
            doc_type="AR",
        )
        assert name is not None
        assert ":" not in name
        assert "*" not in name

    def test_network_firma_shown_when_different(self):
        identity = Identity(standort="A", firma="D5")
        name, status, info = build_filename(
            company="Avacon",
            date_str="20260228",
            rechnungsnr="12345",
            zeitraum="2026.02",
            doc_type="AR",
            identity=identity,
        )
        # D5 ≠ Avacon → both shown
        assert "D5" in (name or "")
        assert "Avacon" in (name or "")

    def test_network_firma_hidden_when_same_as_company(self):
        """If no mapping found, firma falls back to company → show only once."""
        name, status, info = build_filename(
            company="Avacon",
            date_str="20260228",
            rechnungsnr="12345",
            zeitraum="2026.02",
            doc_type="AR",
            # No identity → firma = "Avacon"
        )
        parts = (name or "").replace(".pdf", "").split(" ")
        # Avacon should appear only once
        assert parts.count("Avacon") == 1
