"""Unit tests for Lichtblick provider — Lieferstelle as mapping key."""

from detoplus.invoice_renamer.providers.lichtblick import LichtblickProvider


LICHTBLICK_SAMPLE = """
Lichtblick SE
DETO Solarstrom 4 GmbH & Co. KG
Lieferstelle: 12345678
02. April 2026
Belegnummer: 9988776655
Strom-Rechnung für 01.03.2026 - 31.03.2026
"""


class TestLichtblickProvider:

    def test_lieferstelle_is_mapping_key(self):
        provider = LichtblickProvider()
        fields = provider._extract_fields(LICHTBLICK_SAMPLE)
        assert fields.kundennummer == "12345678"

    def test_belegnummer_is_rechnungsnr(self):
        provider = LichtblickProvider()
        fields = provider._extract_fields(LICHTBLICK_SAMPLE)
        assert fields.rechnungsnr == "9988776655"

    def test_default_doc_type_is_er(self):
        provider = LichtblickProvider()
        assert provider.default_doc_type == "ER"

    def test_german_long_date(self):
        provider = LichtblickProvider()
        fields = provider._extract_fields(LICHTBLICK_SAMPLE)
        assert fields.date_str == "20260402"

    def test_zeitraum(self):
        provider = LichtblickProvider()
        fields = provider._extract_fields(LICHTBLICK_SAMPLE)
        assert fields.zeitraum == "2026.03"

    def test_mapping_applied(self, sample_mappings):
        provider = LichtblickProvider(lookup_table=sample_mappings)
        result = provider.analyse_text(LICHTBLICK_SAMPLE)
        assert "K261" in (result.new_name or "")
        assert "Dachanlage Berlin" in (result.new_name or "")
