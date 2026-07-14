"""Unit tests for shared extraction helpers."""

import pytest
from detoplus.invoice_renamer.extraction.common import (
    clean_spaced_number,
    fix_scientific_notation,
    parse_german_long_date,
    parse_dmy_date,
    parse_city_date,
    parse_zeitraum_end_month,
    compute_zeitraum_days,
)


class TestCleanSpacedNumber:
    def test_removes_all_whitespace(self):
        assert clean_spaced_number("215 0003 857 83") == "215000385783"

    def test_handles_none(self):
        assert clean_spaced_number(None) == ""

    def test_handles_empty(self):
        assert clean_spaced_number("") == ""

    def test_preserves_already_clean(self):
        assert clean_spaced_number("123456789") == "123456789"


class TestFixScientificNotation:
    def test_simple_sci(self):
        assert fix_scientific_notation("9.1200275929e+11") == "912002759290"

    def test_no_exponent(self):
        assert fix_scientific_notation("123456789") == "123456789"

    def test_with_spaces(self):
        assert fix_scientific_notation("1.23 e+5") == "123000"


class TestParseGermanLongDate:
    def test_standard_format(self):
        assert parse_german_long_date("13. Mai 2026") == "20260513"

    def test_november(self):
        assert parse_german_long_date("01. November 2023") == "20231101"

    def test_april(self):
        assert parse_german_long_date("02. April 2026") == "20260402"

    def test_maerz_ascii(self):
        text = "4. März 2025"
        assert parse_german_long_date(text) == "20250304"

    def test_no_match(self):
        assert parse_german_long_date("No date here") is None


class TestParseDMYDate:
    def test_four_digit_year(self):
        assert parse_dmy_date("09.04.2026") == "20260409"

    def test_two_digit_year(self):
        assert parse_dmy_date("12.09.23") == "20230912"

    def test_no_match(self):
        assert parse_dmy_date("abc") is None


class TestParseCityDate:
    def test_mitnetz_format(self):
        assert parse_city_date("Cottbus, 09.04.2026") == "20260409"


class TestParseZeitraumEndMonth:
    def test_abrechnung_format(self):
        text = "Abrechnung von 01.02.2026 bis 28.02.2026"
        assert parse_zeitraum_end_month(text) == "2026.02"

    def test_vom_bis_format(self):
        text = "vom 01.08.23 bis 31.08.23"
        assert parse_zeitraum_end_month(text) == "2023.08"

    def test_schlussrechnung_format(self):
        text = "Schlussrechnung für Oktober 2025"
        assert parse_zeitraum_end_month(text) == "2025.10"

    def test_fuer_den_zeitraum_format(self):
        text = "für den Zeitraum vom 01.03.2025 bis 31.03.2025"
        assert parse_zeitraum_end_month(text) == "2025.03"

    def test_no_match(self):
        assert parse_zeitraum_end_month("No billing period here") is None


class TestComputeZeitraumDays:
    def test_one_month(self):
        assert compute_zeitraum_days("01.2026-02.2026") == 31

    def test_full_dates(self):
        assert compute_zeitraum_days("01.01.2026-31.01.2026") == 30

    def test_unparseable(self):
        assert compute_zeitraum_days("garbage") is None
