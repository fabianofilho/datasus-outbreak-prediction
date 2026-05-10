"""Acesso a dados do SNIS (Sistema Nacional de Informacoes sobre Saneamento).

Os dados SNIS sao publicados anualmente com 1-2 anos de atraso.
Download manual: http://app4.mdr.gov.br/serieHistorica/

Indicadores utilizados:
  IN055 : Indice de atendimento com rede de agua (% populacao)
  IN056 : Indice de atendimento com rede de esgotos (% populacao)
  IN046 : Indice de coleta de esgoto (% esgoto coletado / agua consumida)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

_STATIC = Path(__file__).parent.parent.parent / "data" / "static"
_CACHE = Path(__file__).parent.parent.parent / "data" / "cache"

try:
    _CACHE.mkdir(parents=True, exist_ok=True)
except (PermissionError, OSError):
    _CACHE = Path("/tmp/epidemio_cache")
    _CACHE.mkdir(parents=True, exist_ok=True)


def load(csv_path: str | Path | None = None) -> pd.DataFrame:
    """Carrega dados SNIS de um CSV pre-baixado.

    Se csv_path nao fornecido, procura por snis_*.csv em data/static/.

    Colunas esperadas (subconjunto):
      CO_MUNICIPIO, NO_MUNICIPIO, SG_UF, IN055_AE, IN056_ES, IN046_ES, ANOREF
    """
    if csv_path is None:
        candidates = list(_STATIC.glob("snis_*.csv"))
        if not candidates:
            return _empty()
        csv_path = sorted(candidates)[-1]

    df = pd.read_csv(csv_path, sep=";", encoding="latin-1", low_memory=False)
    return _clean(df)


def _clean(df: pd.DataFrame) -> pd.DataFrame:
    col_map = {}
    for col in df.columns:
        low = col.strip().lower()
        if "co_municipio" in low or "cod_municipio" in low:
            col_map[col] = "codigo"
        elif "no_municipio" in low or "nom_municipio" in low:
            col_map[col] = "nome_municipio"
        elif "sg_uf" in low or "uf" == low:
            col_map[col] = "uf"
        elif "in055" in low:
            col_map[col] = "cobertura_agua_pct"
        elif "in056" in low:
            col_map[col] = "cobertura_esgoto_pct"
        elif "in046" in low:
            col_map[col] = "coleta_esgoto_pct"
        elif "anoref" in low or "ano_referencia" in low:
            col_map[col] = "ano_referencia"

    df = df.rename(columns=col_map)

    keep = [c for c in ["codigo", "nome_municipio", "uf", "cobertura_agua_pct",
                        "cobertura_esgoto_pct", "coleta_esgoto_pct", "ano_referencia"]
            if c in df.columns]
    df = df[keep].copy()

    for col in ["cobertura_agua_pct", "cobertura_esgoto_pct", "coleta_esgoto_pct"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "."), errors="coerce"
            )

    if "codigo" in df.columns:
        df["codigo"] = df["codigo"].astype(str).str.zfill(7)
        df["codigo_6d"] = df["codigo"].str[:6]

    return df.dropna(subset=["codigo"] if "codigo" in df.columns else [])


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=[
        "codigo", "nome_municipio", "uf",
        "cobertura_agua_pct", "cobertura_esgoto_pct", "coleta_esgoto_pct", "ano_referencia"
    ])
