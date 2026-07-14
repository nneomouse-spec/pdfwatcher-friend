"""Provider registry — maps Netzbetreiber names to their analyser classes.

All 30 companies are registered. 15 have dedicated analysers,
15 use the universal fallback.
"""

from __future__ import annotations

from .base import BaseProvider
from .sap import AvaconProvider, BayernwerkProvider, EDisProvider, MitnetzProvider
from .avu_netz import AvuNetzProvider
from .bielefelder import BielefelderProvider
from .ena import ENAProvider
from .e_on import EOnProvider
from .ewz import EWZProvider
from .geranetz import GeraNetzProvider
from .lichtblick import LichtblickProvider
from .redinet import RedinetProvider
from .sachsennetze import SachsenNetzeProvider
from .ten import TENProvider
from .wemag import WemagProvider
from .universal import UniversalProvider


# All dedicated provider classes, keyed by company name
_PROVIDER_CLASSES: dict[str, type[BaseProvider]] = {
    "Avacon":        AvaconProvider,
    "Avu Netz":      AvuNetzProvider,
    "Bayernwerk":    BayernwerkProvider,
    "Bielefelder":   BielefelderProvider,
    "E.Dis":         EDisProvider,
    "ENA":           ENAProvider,
    "E-On":          EOnProvider,
    "EWZ":           EWZProvider,
    "GeraNetz":      GeraNetzProvider,
    "Lichtblick":    LichtblickProvider,
    "Mitnetz":       MitnetzProvider,
    "Redinet":       RedinetProvider,
    "SachsenNetze":  SachsenNetzeProvider,
    "TEN":           TENProvider,
    "Wemag":         WemagProvider,
}


def get_provider(
    company: str,
    lookup_table: dict[str, list[dict[str, str]]] | None = None,
) -> BaseProvider:
    """Return the analyser for a given Netzbetreiber.

    Dedicated analysers are used when available; otherwise the universal
    fallback is used.
    """
    cls = _PROVIDER_CLASSES.get(company)
    if cls is not None:
        return cls(lookup_table=lookup_table)
    return UniversalProvider(company=company, lookup_table=lookup_table)


def has_dedicated_analyser(company: str) -> bool:
    """Check if a company has a hand-tuned analyser."""
    return company in _PROVIDER_CLASSES
