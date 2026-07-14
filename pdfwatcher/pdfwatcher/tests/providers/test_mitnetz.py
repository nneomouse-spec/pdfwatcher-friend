"""Unit tests for Mitnetz provider (SAP platform with overrides)."""

from detoplus.invoice_renamer.providers.sap.mitnetz import MitnetzProvider


MITNETZ_SAMPLE = """
DETO Solarstrom 1 GmbH & Co. KG
Impulsgeber Stromfabrik 1
Cottbus, 09.04.2026
Rechn.-Nr.: 3168 4009 0503
Vertragskonto: 3168 4009 0503
Abrechnung von 01.04.2026 bis 30.04.2026
"""


class TestMitnetzProvider:

    def test_extracts_date_city_format(self):
        provider = MitnetzProvider()
        fields = provider._extract_fields(MITNETZ_SAMPLE)
        assert fields.date_str == "20260409"

    def test_extracts_rechnungsnr_abbreviated_label(self):
        provider = MitnetzProvider()
        fields = provider._extract_fields(MITNETZ_SAMPLE)
        assert fields.rechnungsnr == "316840090503"

    def test_different_label_from_avacon(self):
        """Mitnetz uses 'Rechn.-Nr.:' not 'Rechnungsnummer:'."""
        avacon_text = "Rechnungsnummer: 1234567890"
        provider = MitnetzProvider()
        fields = provider._extract_fields(avacon_text)
        # Should NOT find it under the standard label
        assert fields.rechnungsnr == ""

    def test_mapping_applied(self, sample_mappings):
        provider = MitnetzProvider(lookup_table=sample_mappings)
        result = provider.analyse_text(MITNETZ_SAMPLE)
        assert "I1" in (result.new_name or "")
        assert "Windpark Nord" in (result.new_name or "")
