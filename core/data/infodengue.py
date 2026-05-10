"""Cliente para a API publica do InfoDengue.

Documentacao da API: https://info.dengue.mat.br/services/api
Endpoint: /api/alertcity

Parametros principais:
  geocode   : codigo IBGE do municipio (7 digitos)
  disease   : dengue | chikungunya | zika
  format    : json
  ew_start  : semana epidemiologica de inicio (1-52)
  ew_end    : semana epidemiologica de fim
  ey_start  : ano de inicio
  ey_end    : ano de fim
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

_BASE_URL = "https://info.dengue.mat.br/api/alertcity"

_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cache"
try:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    _CACHE_DIR = Path("/tmp/epidemio_cache")
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)

DISEASES = ["dengue", "chikungunya", "zika"]


def _cache_path(geocode: str, disease: str, ey_start: int, ey_end: int) -> Path:
    return _CACHE_DIR / f"infodengue_{geocode}_{disease}_{ey_start}_{ey_end}.parquet"


def fetch_city(
    geocode: str | int,
    disease: str = "dengue",
    ey_start: int = 2020,
    ey_end: int = 2024,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Busca dados de alerta de arbovirose para um municipio.

    Retorna DataFrame com colunas:
      data_iniSE, SE, casos_est, casos, municipio_geocodigo, nivel, Rt, pop
    """
    geocode = str(geocode)
    cache = _cache_path(geocode, disease, ey_start, ey_end)

    if use_cache and cache.exists():
        return pd.read_parquet(cache)

    params = {
        "geocode": geocode,
        "disease": disease,
        "format": "json",
        "ew_start": 1,
        "ew_end": 52,
        "ey_start": ey_start,
        "ey_end": ey_end,
    }

    resp = requests.get(_BASE_URL, params=params, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df = _clean(df, geocode)

    if len(df) >= 52:
        df.to_parquet(cache, index=False)

    return df


def _clean(df: pd.DataFrame, geocode: str) -> pd.DataFrame:
    if df.empty:
        return df

    if "data_iniSE" in df.columns:
        df["data_iniSE"] = pd.to_datetime(df["data_iniSE"], errors="coerce")

    for col in ["casos_est", "casos"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0)

    if "SE" in df.columns:
        df["ano"] = (df["SE"] // 100).astype("Int64")
        df["semana_epi"] = (df["SE"] % 100).astype("Int64")

    if "municipio_geocodigo" not in df.columns:
        df["municipio_geocodigo"] = geocode

    return df.sort_values("data_iniSE").reset_index(drop=True)


def fetch_state(
    geocodes: list[str | int],
    disease: str = "dengue",
    ey_start: int = 2020,
    ey_end: int = 2024,
) -> pd.DataFrame:
    """Busca dados de alerta para multiplos municipios."""
    dfs = []
    for gc in geocodes:
        try:
            df = fetch_city(gc, disease, ey_start, ey_end)
            if not df.empty:
                dfs.append(df)
        except Exception:
            continue
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def series_for_forecast(df: pd.DataFrame, col: str = "casos_est") -> pd.Series:
    """Extrai serie temporal indexada por data para uso no skforecast.

    Filtra municipios com menos de 52 semanas de historico.
    """
    if df.empty or "data_iniSE" not in df.columns or col not in df.columns:
        return pd.Series(dtype=float)

    s = df.set_index("data_iniSE")[col].dropna()
    s = s.asfreq("W-MON", method="ffill")
    return s.astype(float)
