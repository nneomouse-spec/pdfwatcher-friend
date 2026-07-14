"""Mitnetz — SAP platform with two override patterns.

Differences from base SAP:
  - Date: "Cottbus, 09.04.2026" (city-prefix) instead of "Datum\nDD.MM.YYYY"
  - Invoice#: "Rechn.-Nr.:" (abbreviated label) instead of "Rechnungsnummer:"
"""

from ._base import SAPPlatformProvider


class MitnetzProvider(SAPPlatformProvider):
    company = "Mitnetz"
    date_pattern = r"\w[\w\s]+,\s*(\d{2})\.(\d{2})\.(\d{4})"
    rechnungsnr_label = r"Rechn\.-Nr\."
