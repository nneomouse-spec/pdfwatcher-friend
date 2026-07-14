"""Identity resolution — "Which DETO entity does this invoice belong to, and where?"

All Netzbetreiber customer numbers must eventually resolve to a (standort, firma) pair.
This module is the single source of truth. Nothing else calls get_mapping directly.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Identity:
    """Resolved identity of a DETO solar entity."""
    standort: str          # Physical location, e.g. "Solarpark Musterstadt"
    firma: str             # Legal entity, e.g. "D5", "I1", "K261"

    @property
    def is_resolved(self) -> bool:
        return bool(self.standort) and bool(self.firma)


UNKNOWN = Identity(standort="", firma="")


def resolve_identity(
    mapping_key: Optional[str],
    company: str,
    lookup_table: dict[str, list[dict[str, str]]],
) -> Identity:
    """Look up a Kundennummer (or Vertragskonto/Lieferstelle) in the per-company mapping table.

    Args:
        mapping_key: The identifier from the invoice (Kundennummer, Vertragskonto, etc.)
        company: The Netzbetreiber name (e.g. "Avacon", "Mitnetz")
        lookup_table: { company: [ {kundennummer, standort, firma}, ... ] }

    Returns:
        Identity if found, UNKNOWN otherwise.
    """
    if not mapping_key:
        return UNKNOWN

    rows = lookup_table.get(company, [])
    key_str = str(mapping_key).strip()

    for row in rows:
        if str(row.get("kundennummer", "")).strip() == key_str:
            return Identity(
                standort=row.get("standort", ""),
                firma=row.get("firma", ""),
            )
    return UNKNOWN
