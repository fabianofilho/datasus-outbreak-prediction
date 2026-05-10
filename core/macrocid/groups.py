"""MacroCID: agrupamento clinico de CIDs relacionados.

Os grupos sao definidos em data/static/macrocid_groups.json.
"""

from __future__ import annotations

import json
from pathlib import Path

_STATIC = Path(__file__).parent.parent.parent / "data" / "static"
_GROUPS_FILE = _STATIC / "macrocid_groups.json"

_cache: dict | None = None


def load_groups() -> dict:
    global _cache
    if _cache is None:
        with open(_GROUPS_FILE, encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache


def group_of(cid: str) -> str | None:
    """Retorna o nome do MacroCID ao qual um CID pertence, ou None."""
    cid = cid.upper().strip()
    prefix3 = cid[:3]

    for group_name, group in load_groups().items():
        if prefix3 in group.get("prefixes", []):
            return group_name
    return None


def label_of(group_name: str) -> str:
    groups = load_groups()
    return groups.get(group_name, {}).get("label", group_name)


def color_of(group_name: str) -> str:
    groups = load_groups()
    return groups.get(group_name, {}).get("color", "#999999")


def all_group_names() -> list[str]:
    return list(load_groups().keys())


def add_macrocid_column(df, cid_col: str = "CAUSABAS", out_col: str = "macrocid") -> None:
    """Adiciona coluna macrocid ao DataFrame in-place."""
    df[out_col] = df[cid_col].apply(lambda x: group_of(str(x)) if isinstance(x, str) else None)
