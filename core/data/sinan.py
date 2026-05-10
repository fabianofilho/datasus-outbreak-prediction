"""Gerador de series temporais sinteticas para doencas do SINAN.

O SINAN disponibiliza dados reais via FTP em formato DBC, incompativel com
Streamlit Cloud. Este modulo gera series realistas com sazonalidade brasileira
para uso em modo demonstracao, mantendo a mesma estrutura de DataFrame que
o modulo InfoDengue retorna.

Sazonalidade de referencia (regiao sudeste como base):
  Gastrointestinais : pico dezembro-marco (chuvas e calor)
  Leptospirose      : pico janeiro-fevereiro (enchentes)
  Respiratorias     : pico junho-agosto (inverno)
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

_WEEK_FREQ = "W-MON"

DISEASE_SEASONALITY: dict[str, dict] = {
    "diarreia_aguda": {
        "baseline": 120,
        "amplitude": 0.55,
        "peak_month": 2,
        "label": "Diarreia Aguda (SINAN)",
        "cid": "A09",
    },
    "hepatite_a": {
        "baseline": 8,
        "amplitude": 0.40,
        "peak_month": 2,
        "label": "Hepatite A (SINAN)",
        "cid": "B15",
    },
    "leptospirose": {
        "baseline": 15,
        "amplitude": 0.70,
        "peak_month": 1,
        "label": "Leptospirose (SINAN)",
        "cid": "A27",
    },
    "febre_tifoide": {
        "baseline": 3,
        "amplitude": 0.35,
        "peak_month": 2,
        "label": "Febre Tifóide (SINAN)",
        "cid": "A01",
    },
    "influenza_a": {
        "baseline": 60,
        "amplitude": 0.65,
        "peak_month": 7,
        "label": "Influenza A (SIVEP-Gripe)",
        "cid": "J09",
    },
    "srag": {
        "baseline": 45,
        "amplitude": 0.60,
        "peak_month": 7,
        "label": "SRAG (SIVEP-Gripe)",
        "cid": "J11",
    },
}


def _seed(geocode: str, disease: str) -> int:
    h = hashlib.md5(f"{geocode}{disease}".encode()).hexdigest()
    return int(h[:8], 16) % (2**31)


def generate(
    geocode: str,
    disease: str,
    ey_start: int = 2020,
    ey_end: int = 2024,
) -> pd.DataFrame:
    """Gera serie temporal sintetica com sazonalidade para a doenca/municipio.

    Retorna DataFrame com as mesmas colunas que infodengue.fetch_city():
      data_iniSE, SE, casos_est, casos, municipio_geocodigo, nivel, Rt, pop, ano, semana_epi
    """
    cfg = DISEASE_SEASONALITY.get(disease)
    if cfg is None:
        return pd.DataFrame()

    rng = np.random.default_rng(_seed(geocode, disease))

    dates = pd.date_range(
        start=f"{ey_start}-01-01",
        end=f"{ey_end}-12-31",
        freq=_WEEK_FREQ,
    )
    n = len(dates)

    # sazonalidade sinusoidal centrada no mes de pico
    peak_day = (cfg["peak_month"] - 1) * 30.5
    day_of_year = np.array(dates.dayofyear, dtype=float)
    phase = 2 * np.pi * (day_of_year - peak_day) / 365
    seasonal = 1 + cfg["amplitude"] * np.cos(phase)

    # escala de populacao aproximada por geocodigo (primeiros 2 digitos = UF)
    uf_code = int(str(geocode)[:2])
    pop_factor = _uf_pop_factor(uf_code)

    baseline = cfg["baseline"] * pop_factor * seasonal
    noise = rng.negative_binomial(5, 0.5, n) * 0.15
    casos_raw = np.clip(baseline + noise, 0, None)

    # tendencia leve crescente ao longo dos anos
    trend = 1 + 0.03 * np.linspace(0, n / 52, n)
    casos = (casos_raw * trend).astype(float)
    casos_est = np.clip(casos * rng.uniform(0.9, 1.2, n), 0, None)

    # nivel simplificado (1-4 como InfoDengue)
    p75 = np.percentile(casos, 75)
    p90 = np.percentile(casos, 90)
    nivel = np.where(casos > p90, 4, np.where(casos > p75, 3, np.where(casos > np.median(casos), 2, 1)))

    se = dates.year * 100 + dates.isocalendar().week.values

    return pd.DataFrame({
        "data_iniSE": dates,
        "SE": se.astype(int),
        "casos_est": casos_est.round(1),
        "casos": casos.round(0).astype(int),
        "municipio_geocodigo": geocode,
        "nivel": nivel.astype(int),
        "Rt": rng.uniform(0.8, 1.3, n).round(2),
        "pop": int(pop_factor * 500_000),
        "ano": dates.year,
        "semana_epi": dates.isocalendar().week.values.astype(int),
        "_sintetico": True,
    })


def _uf_pop_factor(uf_code: int) -> float:
    """Fator de escala de casos baseado no porte demografico da UF."""
    grandes = {35: 3.5, 33: 2.5, 31: 2.0, 29: 1.5, 23: 1.3, 26: 1.3}
    medios  = {41: 1.1, 43: 1.1, 52: 0.9, 15: 0.9, 13: 0.9, 21: 0.8}
    return grandes.get(uf_code, medios.get(uf_code, 0.6))
