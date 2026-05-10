"""Acesso a dados demograficos e shapefile do IBGE.

Municipios: https://servicodados.ibge.gov.br/api/v1/localidades/municipios
GeoJSON simplificado: salvo em data/static/br_municipios.geojson
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

_API_URL = "https://servicodados.ibge.gov.br/api/v1/localidades"
_STATIC = Path(__file__).parent.parent.parent / "data" / "static"
_CACHE = Path(__file__).parent.parent.parent / "data" / "cache"

try:
    _CACHE.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    _CACHE = Path("/tmp/epidemio_cache")
    _CACHE.mkdir(parents=True, exist_ok=True)


def municipios(uf: str | None = None, use_cache: bool = True) -> pd.DataFrame:
    """Retorna DataFrame com municipios IBGE.

    Colunas: codigo, nome, uf_sigla, uf_codigo, regiao
    """
    cache_path = _CACHE / f"ibge_municipios{'_' + uf if uf else ''}.parquet"
    if use_cache and cache_path.exists():
        return pd.read_parquet(cache_path)

    url = f"{_API_URL}/municipios"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()

    data = resp.json()
    rows = []
    for m in data:
        rows.append({
            "codigo": str(m["id"]),
            "codigo_6d": str(m["id"])[:6],
            "nome": m["nome"],
            "uf_sigla": m["microrregiao"]["mesorregiao"]["UF"]["sigla"],
            "uf_codigo": str(m["microrregiao"]["mesorregiao"]["UF"]["id"]),
            "uf_nome": m["microrregiao"]["mesorregiao"]["UF"]["nome"],
            "regiao": m["microrregiao"]["mesorregiao"]["UF"]["regiao"]["nome"],
        })

    df = pd.DataFrame(rows)
    if uf:
        df = df[df["uf_sigla"].str.upper() == uf.upper()]

    df.to_parquet(cache_path, index=False)
    return df


def geojson_path() -> Path:
    """Retorna path para GeoJSON de municipios (data/static/br_municipios.geojson)."""
    p = _STATIC / "br_municipios.geojson"
    if not p.exists():
        raise FileNotFoundError(
            "GeoJSON nao encontrado. Baixe de "
            "https://raw.githubusercontent.com/codeforamerica/click_that_hood/"
            "master/public/data/brazil-states.geojson e salve em data/static/br_municipios.geojson"
        )
    return p
