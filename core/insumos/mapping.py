"""Mapeamento de CIDs para insumos/medicamentos.

Os dados sao carregados de data/static/cid_insumos.json.
Fonte: Protocolos Clinicos e Diretrizes Terapeuticas do MS (PCDT) e RENAME 2022.
"""

from __future__ import annotations

import json
from pathlib import Path

_STATIC = Path(__file__).parent.parent.parent / "data" / "static"
_FILE = _STATIC / "cid_insumos.json"

_cache: dict | None = None


def load() -> dict:
    global _cache
    if _cache is None:
        with open(_FILE, encoding="utf-8") as f:
            data = json.load(f)
        _cache = {k: v for k, v in data.items() if not k.startswith("_")}
    return _cache


def insumos_for_cid(cid: str) -> dict:
    """Retorna dict de insumos para um CID especifico."""
    cid = cid.upper().strip()[:3]
    return load().get(cid, {}).get("insumos", {})


def all_insumos() -> list[str]:
    """Lista todos os insumos cadastrados."""
    insumos = set()
    for entry in load().values():
        insumos.update(entry.get("insumos", {}).keys())
    return sorted(insumos)


def cids_with_mapping() -> list[str]:
    return list(load().keys())
