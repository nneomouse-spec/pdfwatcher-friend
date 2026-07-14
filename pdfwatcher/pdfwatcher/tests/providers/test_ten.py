"""Unit tests for TEN provider — scientific notation + composite key."""

from detoplus.invoice_renamer.providers.ten import TENProvider


TEN_SAMPLE = """
DETO Solarstrom 3 GmbH & Co. KG
Vertragskonto
Kundennummer
27078391
50023840
Einspeiseabrechnung Nr. 9.1200275929e+11
13. Mai 2026
vom 01.05.2026 bis 31.05.2026
"""


class TestTENProvider:

    def test_composite_mapping_key(self):
        provider = TENProvider()
        fields = provider._extract_fields(TEN_SAMPLE)
        assert fields.kundennummer == "50023840-27078391"

    def test_scientific_notation_rechnungsnr(self):
        provider = TENProvider()
        fields = provider._extract_fields(TEN_SAMPLE)
        assert fields.rechnungsnr == "912002759290"

    def test_german_long_date(self):
        provider = TENProvider()
        fields = provider._extract_fields(TEN_SAMPLE)
        assert fields.date_str == "20260513"

    def test_mapping_applied(self, sample_mappings):
        provider = TENProvider(lookup_table=sample_mappings)
        result = provider.analyse_text(TEN_SAMPLE)
        assert "D3" in (result.new_name or "")
        assert "Solarpark Süd" in (result.new_name or "")
