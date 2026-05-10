"""Lista de municipios brasileiros via API IBGE.

Busca todos os ~5570 municipios do Brasil com nome, UF e geocodigo IBGE.
Resultado fica em cache local (data/cache/) para evitar requests repetidos.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import requests

_CACHE = Path(__file__).parent.parent.parent / "data" / "cache" / "municipios_ibge.json"
_IBGE_URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"

_CAPITAIS_FALLBACK = [
    ("Rio de Janeiro", "RJ", "3304557"),
    ("Sao Paulo", "SP", "3550308"),
    ("Belo Horizonte", "MG", "3106200"),
    ("Salvador", "BA", "2927408"),
    ("Fortaleza", "CE", "2304400"),
    ("Manaus", "AM", "1302603"),
    ("Recife", "PE", "2611606"),
    ("Porto Alegre", "RS", "4314902"),
    ("Curitiba", "PR", "4106902"),
    ("Belem", "PA", "1501402"),
    ("Goiania", "GO", "5208707"),
    ("Brasilia", "DF", "5300108"),
    ("Natal", "RN", "2408102"),
    ("Maceio", "AL", "2704302"),
    ("Campo Grande", "MS", "5002704"),
    ("Teresina", "PI", "2211001"),
    ("Joao Pessoa", "PB", "2507507"),
    ("Aracaju", "SE", "2800308"),
    ("Cuiaba", "MT", "5103403"),
    ("Porto Velho", "RO", "1100205"),
    ("Macapa", "AP", "1600303"),
    ("Boa Vista", "RR", "1400100"),
    ("Palmas", "TO", "1721000"),
    ("Rio Branco", "AC", "1200401"),
    ("Sao Luis", "MA", "2111300"),
    ("Vitoria", "ES", "3205309"),
    ("Florianopolis", "SC", "4205407"),
]


def _from_cache() -> list | None:
    if _CACHE.exists():
        try:
            with open(_CACHE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None


def _fetch_ibge() -> list | None:
    try:
        resp = requests.get(_IBGE_URL, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        _CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(_CACHE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        return data
    except Exception:
        return None


def _parse(data: list) -> pd.DataFrame:
    rows = []
    for m in data:
        try:
            uf = m["microrregiao"]["mesorregiao"]["UF"]["sigla"]
            rows.append({"nome": m["nome"], "uf": uf, "geocode": str(m["id"])})
        except (KeyError, TypeError):
            continue
    return pd.DataFrame(rows).sort_values(["uf", "nome"]).reset_index(drop=True)


def _fallback() -> pd.DataFrame:
    return pd.DataFrame(_CAPITAIS_FALLBACK, columns=["nome", "uf", "geocode"])


def load() -> pd.DataFrame:
    """Retorna DataFrame com nome, uf, geocode de todos os municipios.

    Tenta cache local -> API IBGE -> fallback de capitais.
    """
    data = _from_cache() or _fetch_ibge()
    if data:
        df = _parse(data)
        if not df.empty:
            return df
    return _fallback()


def display_options(df: pd.DataFrame | None = None) -> dict[str, str]:
    """Retorna dict {nome_exibicao: geocode} para uso em selectbox/multiselect."""
    if df is None:
        df = load()
    return {f"{row.nome} ({row.uf})": row.geocode for row in df.itertuples()}


def default_capitals() -> list[str]:
    """Nomes de exibicao das capitais para usar como default no multiselect."""
    caps = ["Rio de Janeiro", "Sao Paulo", "Belo Horizonte", "Fortaleza", "Manaus"]
    uf_map = {n: uf for n, uf, _ in _CAPITAIS_FALLBACK}
    return [f"{c} ({uf_map[c]})" for c in caps if c in uf_map]
