"""SIM-DO (mortality declarations) preprocessor and causal chain extractor."""

from __future__ import annotations

import re

import pandas as pd


KEEP_COLS = [
    "NUMERODO",
    "DTOBITO",
    "DTNASC", "IDADE", "SEXO", "RACACOR",
    "CAUSABAS",
    "LINHAA", "LINHAB", "LINHAC", "LINHAD",
    "CODMUNOCOR", "CODMUNRES",
]

_ICD_RE = re.compile(r"[A-Z]\d{2,3}", re.IGNORECASE)

# Causal chain levels in causal order (underlying -> immediate)
CHAIN_LEVELS = ["CAUSABAS", "LINHAD", "LINHAC", "LINHAB", "LINHAA"]


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize a raw SIM DataFrame."""
    cols = [c for c in KEEP_COLS if c in df.columns]
    df = df[cols].copy()

    for col in ["DTOBITO", "DTNASC"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", format="%d%m%Y")

    if "IDADE" in df.columns:
        df["idade_anos"] = _decode_idade(df["IDADE"])

    if "DTOBITO" in df.columns:
        df["year"] = df["DTOBITO"].dt.year

    if "CODMUNRES" in df.columns:
        df["uf_code"] = df["CODMUNRES"].astype(str).str[:2]

    return df


def _decode_idade(serie: pd.Series) -> pd.Series:
    """Decode SIM IDADE field to age in years."""
    s = pd.to_numeric(serie, errors="coerce")
    unit = (s // 100).astype("Int64")
    value = (s % 100).astype(float)
    age = pd.Series(index=serie.index, dtype=float)
    age[unit == 4] = value[unit == 4]
    age[unit == 3] = value[unit == 3] / 12
    age[unit == 2] = value[unit == 2] / 365
    age[unit == 1] = value[unit == 1] / 8760
    return age


def extract_codes(value) -> list[str]:
    """Extract individual ICD-10 codes from a LINHA field value.

    Handles concatenated codes, semicolons, spaces, and other separators.
    Returns uppercase 3-4 char codes like ['I219', 'J189'].
    """
    if pd.isna(value):
        return []
    text = str(value).strip().upper()
    if not text or text == "NAN":
        return []
    return _ICD_RE.findall(text)


def extract_causal_chains(df: pd.DataFrame) -> pd.DataFrame:
    """Extract directed edges from the causal chain of each death certificate.

    For each DO, walks CAUSABAS -> LINHAD -> LINHAC -> LINHAB -> LINHAA.
    Adjacent non-empty levels produce edges (cartesian product when
    multiple codes exist in a level).

    Returns DataFrame with columns:
        source, target, numerodo, uf_code, year, sexo, idade_anos
    """
    rows = []

    for _, rec in df.iterrows():
        # Collect codes at each level
        levels = []
        for col in CHAIN_LEVELS:
            if col in rec.index:
                codes = extract_codes(rec.get(col))
                if codes:
                    levels.append(codes)

        if len(levels) < 2:
            continue

        meta = {
            "numerodo": rec.get("NUMERODO", ""),
            "uf_code": rec.get("uf_code", ""),
            "year": rec.get("year", None),
            "sexo": rec.get("SEXO", ""),
            "idade_anos": rec.get("idade_anos", None),
        }

        # Generate edges between adjacent levels
        for i in range(len(levels) - 1):
            for src in levels[i]:
                for tgt in levels[i + 1]:
                    if src != tgt:
                        rows.append({"source": src, "target": tgt, **meta})

    return pd.DataFrame(rows) if rows else pd.DataFrame(
        columns=["source", "target", "numerodo", "uf_code", "year", "sexo", "idade_anos"]
    )
