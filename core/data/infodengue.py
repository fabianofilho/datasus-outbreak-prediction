"""Cliente unificado de doencas epidemiologicas.

Fontes:
  Arboviroses            -> InfoDengue REST API (dados reais)
  Gastrointestinais/SRAG -> SINAN/SIVEP sintetico com sazonalidade brasileira

Documentacao InfoDengue: https://info.dengue.mat.br/services/api
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

_ARBOVIRUS = {"dengue", "chikungunya", "zika"}

DISEASE_GROUPS: dict[str, list[str]] = {
    "Arboviroses": ["dengue", "chikungunya", "zika"],
    "Gastrointestinais": ["diarreia_aguda", "hepatite_a", "leptospirose", "febre_tifoide"],
    "Respiratórias": ["influenza_a", "srag"],
}

DISEASES: list[str] = [d for group in DISEASE_GROUPS.values() for d in group]

DISEASE_CID: dict[str, str] = {
    "dengue": "A90",
    "chikungunya": "A92",
    "zika": "A92",
    "diarreia_aguda": "A09",
    "hepatite_a": "B15",
    "leptospirose": "A27",
    "febre_tifoide": "A01",
    "influenza_a": "J09",
    "srag": "J11",
}

DISEASE_LABELS: dict[str, str] = {
    "dengue": "Dengue",
    "chikungunya": "Chikungunya",
    "zika": "Zika",
    "diarreia_aguda": "Diarreia Aguda",
    "hepatite_a": "Hepatite A",
    "leptospirose": "Leptospirose",
    "febre_tifoide": "Febre Tifóide",
    "influenza_a": "Influenza A",
    "srag": "SRAG",
}


def _cache_path(geocode: str, disease: str, ey_start: int, ey_end: int) -> Path:
    return _CACHE_DIR / f"infodengue_{geocode}_{disease}_{ey_start}_{ey_end}.parquet"


def fetch_city(
    geocode: str | int,
    disease: str = "dengue",
    ey_start: int = 2020,
    ey_end: int = 2024,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Busca dados de alerta para um municipio.

    Roteia automaticamente:
      - Arboviroses  -> InfoDengue API (dados reais)
      - Demais       -> gerador sintetico SINAN/SIVEP com sazonalidade brasileira
    """
    geocode = str(geocode)

    if disease in _ARBOVIRUS:
        return _fetch_infodengue(geocode, disease, ey_start, ey_end, use_cache)

    from core.data.sinan import generate
    df = generate(geocode, disease, ey_start, ey_end)
    return df


def _fetch_infodengue(
    geocode: str,
    disease: str,
    ey_start: int,
    ey_end: int,
    use_cache: bool,
) -> pd.DataFrame:
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

    try:
        resp = requests.get(_BASE_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return pd.DataFrame()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df = _clean(df, geocode)

    if len(df) >= 52:
        try:
            df.to_parquet(cache, index=False)
        except Exception:
            pass

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
    """Extrai serie temporal indexada por data para uso no skforecast."""
    if df.empty or "data_iniSE" not in df.columns or col not in df.columns:
        return pd.Series(dtype=float)

    s = df.set_index("data_iniSE")[col].dropna()
    s = s.asfreq("W-MON", method="ffill")
    return s.astype(float)
