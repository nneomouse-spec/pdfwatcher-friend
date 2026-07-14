"""Avacon — SAP platform. No overrides needed from base."""

from ._base import SAPPlatformProvider


class AvaconProvider(SAPPlatformProvider):
    company = "Avacon"
