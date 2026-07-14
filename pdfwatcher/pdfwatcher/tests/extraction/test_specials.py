"""Unit tests for special suffix detection."""

import pytest
from detoplus.invoice_renamer.extraction.specials import detect_special_suffix, SpecialSuffix


class TestDetectSpecialSuffix:
    def test_redispatch_detected(self):
        assert detect_special_suffix("Dies ist ein Redispatch Dokument") == SpecialSuffix.REDISPATCH

    def test_storno_detected(self):
        assert detect_special_suffix("Stornorechnung März 2026") == SpecialSuffix.STORNO

    def test_korrektur_detected(self):
        assert detect_special_suffix("Korrekturrechnung vom 01.04.") == SpecialSuffix.KORREKTURNOTE

    def test_korrekturnote_detected(self):
        assert detect_special_suffix("Korrekturnote #12345") == SpecialSuffix.KORREKTURNOTE

    def test_redispatch_priority_over_korrektur(self):
        text = "Dies ist ein Redispatch mit Korrektur"
        assert detect_special_suffix(text) == SpecialSuffix.REDISPATCH

    def test_korrektur_priority_over_storno(self):
        text = "Korrektur und Storno"
        assert detect_special_suffix(text) == SpecialSuffix.KORREKTURNOTE

    def test_gutschrift_NOT_detected(self):
        """Gutschrift (credit note) is explicitly excluded per business rules."""
        assert detect_special_suffix("Gutschrift für Januar") is None

    def test_normal_invoice_no_suffix(self):
        assert detect_special_suffix("Rechnung vom 01.01.2026") is None

    def test_empty_text(self):
        assert detect_special_suffix("") is None

    def test_case_insensitive(self):
        assert detect_special_suffix("REDISPATCH") == SpecialSuffix.REDISPATCH
        assert detect_special_suffix("StOrNoReChNuNg") == SpecialSuffix.STORNO
