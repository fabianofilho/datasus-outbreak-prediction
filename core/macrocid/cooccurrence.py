"""Matriz de co-ocorrencia entre MacroCIDs.

A co-ocorrencia e calculada a partir dos dados do SIM:
para cada obito com cadeia causal (CAUSABAS + LINHA*),
conta quantas vezes dois MacroCIDs aparecem juntos na mesma cadeia.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from core.macrocid.groups import all_group_names, group_of
from core.data.sim import extract_codes, CHAIN_LEVELS


def build_cooccurrence(sim_df: pd.DataFrame) -> pd.DataFrame:
    """Constroi matriz de co-ocorrencia entre grupos MacroCID.

    Parameters
    ----------
    sim_df : DataFrame preprocessado pelo SIM (saida de sim.preprocess)

    Returns
    -------
    DataFrame simetrico: index e columns = grupos MacroCID, valores = contagens
    """
    groups = all_group_names()
    matrix = pd.DataFrame(0, index=groups, columns=groups)

    for _, row in sim_df.iterrows():
        codes_in_chain = []
        for col in CHAIN_LEVELS:
            if col in row.index:
                codes_in_chain.extend(extract_codes(row.get(col, "")))

        macros = set(filter(None, (group_of(c) for c in codes_in_chain)))

        for g1 in macros:
            for g2 in macros:
                if g1 in groups and g2 in groups:
                    matrix.loc[g1, g2] += 1

    return matrix


def normalized_cooccurrence(matrix: pd.DataFrame) -> pd.DataFrame:
    """Normaliza a matriz de co-ocorrencia pela diagonal (jaccard-like)."""
    result = pd.DataFrame(0.0, index=matrix.index, columns=matrix.columns)
    for i in matrix.index:
        for j in matrix.columns:
            union = matrix.loc[i, i] + matrix.loc[j, j] - matrix.loc[i, j]
            result.loc[i, j] = matrix.loc[i, j] / union if union > 0 else 0.0
    return result
