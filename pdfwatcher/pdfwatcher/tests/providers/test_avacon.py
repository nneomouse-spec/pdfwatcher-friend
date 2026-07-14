"""Unit tests for the Avacon provider (SAP platform)."""

from detoplus.invoice_renamer.providers.sap.avacon import AvaconProvider
from detoplus.invoice_renamer.providers.base import ExtractedFields


# Sample Avacon PDF text (anonymised, structure-preserving)
AVACON_SAMPLE = """
DETO Solarstrom 5 GmbH & Co. KG
#!#VNR#!#215000385783#!#
Datum
28.02.2026
Rechnungsnummer: 3111 4005 9500
Vertragskonto: 2150 0038 5783
Abrechnung von 01.02.2026 bis 28.02.2026
Netznutzungsentgelt
"""

AVACON_SAMPLE_NO_METADATA = """
DETO Solarstrom 5 GmbH & Co. KG
Datum
15.03.2026
Rechnungsnummer: 3111 4005 9999
Vertragskonto: 2150 0012 3456
Abrechnung von 01.03.2026 bis 31.03.2026
"""


class TestAvaconProvider:

    def setup_method(self):
        self.provider = AvaconProvider()

    def test_extracts_vertragskonto_from_metadata(self):
        fields = self.provider._extract_fields(AVACON_SAMPLE)
        assert fields.kundennummer == "215000385783"

    def test_extracts_vertragskonto_from_footer(self):
        fields = self.provider._extract_fields(AVACON_SAMPLE_NO_METADATA)
        assert fields.kundennummer == "215000123456"

    def test_extracts_date(self):
        fields = self.provider._extract_fields(AVACON_SAMPLE)
        assert fields.date_str == "20260228"

    def test_extracts_rechnungsnummer(self):
        fields = self.provider._extract_fields(AVACON_SAMPLE)
        assert fields.rechnungsnr == "311140059500"

    def test_extracts_zeitraum(self):
        fields = self.provider._extract_fields(AVACON_SAMPLE)
        assert fields.zeitraum == "2026.02"

    def test_full_analyse_with_mapping(self, sample_mappings):
        provider = AvaconProvider(lookup_table=sample_mappings)
        result = provider.analyse_text(AVACON_SAMPLE)
        assert result.is_ok
        assert result.new_name is not None
        assert "D5" in result.new_name
        assert "Solarpark Musterstadt" in result.new_name
        assert "Avacon" in result.new_name

    def test_redispatch_detection(self):
        provider = AvaconProvider()
        text = AVACON_SAMPLE + "\nRedispatch\n"
        result = provider.analyse_text(text)
        assert "Redispatch" in (result.new_name or "")

    def test_empty_text(self):
        result = self.provider.analyse_text("")
        assert not result.is_ok
        assert result.confidence == 0

    def test_maps_vertragskonto_to_identity(self, sample_mappings):
        provider = AvaconProvider(lookup_table=sample_mappings)
        result = provider.analyse_text(AVACON_SAMPLE)
        assert "D5" in (result.new_name or "")
        assert "Solarpark Musterstadt" in (result.new_name or "")
