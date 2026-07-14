"""Unit tests for Wemag provider — dashed KN, last-segment Rechnungsnr."""

from detoplus.invoice_renamer.providers.wemag import WemagProvider


WEMAG_SAMPLE = """
Wemag Netz GmbH
Kundennummer: 0002-6288567-1217875
Rechnungs-Nr. 0002-ARV-2026-200117785
Rechnungsdatum 15.03.2026
für die Zeit vom 01.03.2026 bis 31.03.2026
"""

WEMAG_KORRIGIERT = """
Wemag Netz GmbH
Kundennummer: 0002-6288567-9999999
Rechnungs-Nr. 0002-ARV-2026-300117786
Rechnungsdatum 20.04.2026
Korrigiert Rg.-Nr. 0002-ARV-2026-100117784
vom 01.04.2026 bis 30.04.2026
"""


class TestWemagProvider:

    def test_kundennummer_with_dashes(self):
        provider = WemagProvider()
        fields = provider._extract_fields(WEMAG_SAMPLE)
        assert fields.kundennummer == "0002-6288567-1217875"

    def test_rechnungsnr_last_segment(self):
        """0002-ARV-2026-200117785 → 200117785."""
        provider = WemagProvider()
        fields = provider._extract_fields(WEMAG_SAMPLE)
        assert fields.rechnungsnr == "200117785"

    def test_date(self):
        provider = WemagProvider()
        fields = provider._extract_fields(WEMAG_SAMPLE)
        assert fields.date_str == "20260315"

    def test_korrigiert_detected_as_korrektur(self):
        provider = WemagProvider()
        result = provider.analyse_text(WEMAG_KORRIGIERT)
        assert "Korrektur" in (result.new_name or "")
