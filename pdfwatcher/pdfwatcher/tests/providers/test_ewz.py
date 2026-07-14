"""Unit tests for EWZ provider — truncated Kundennummer, stripped invoice#."""

from detoplus.invoice_renamer.providers.ewz import EWZProvider


EWZ_SAMPLE = """
EWZ Energiewerke Zeulenroda
DETO Solarstrom 2 GmbH & Co. KG
Kunden-Nr.: 310031/3100031
Rechnungsnummer
ES23-0146
Rechnungsdatum
12.09.2023
vom 01.08.23 bis 31.08.23
"""


class TestEWZProvider:

    def test_kundennummer_transform(self):
        """310031/3100031 → 310031-3100 (first4 of second part)."""
        provider = EWZProvider()
        fields = provider._extract_fields(EWZ_SAMPLE)
        assert fields.kundennummer == "310031-3100"

    def test_rechnungsnummer_strips_prefix(self):
        """ES23-0146 → 0146 (digits after dash only)."""
        provider = EWZProvider()
        fields = provider._extract_fields(EWZ_SAMPLE)
        assert fields.rechnungsnr == "0146"

    def test_two_digit_year_date(self):
        provider = EWZProvider()
        fields = provider._extract_fields(EWZ_SAMPLE)
        assert fields.date_str == "20230912"

    def test_zeitraum_two_digit_year(self):
        provider = EWZProvider()
        fields = provider._extract_fields(EWZ_SAMPLE)
        assert fields.zeitraum == "2023.08"
