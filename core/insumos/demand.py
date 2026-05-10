"""Projecao de demanda por insumos a partir de casos previstos.

Logica: demanda = casos_previstos * consumo_medio_por_caso

IMPORTANTE: este modulo projeta DEMANDA com base em previsoes epidemiologicas.
Nao ha dados de estoque em tempo real no SUS publico.
O output deve ser interpretado como estimativa de necessidade, nao de deficit.
"""

from __future__ import annotations

import pandas as pd

from core.insumos.mapping import insumos_for_cid, all_insumos


def project_demand(
    forecasts: dict[str, float],
    horizon_weeks: int = 4,
) -> pd.DataFrame:
    """Projeta demanda de insumos a partir de casos previstos.

    Parameters
    ----------
    forecasts : dict {cid_prefix -> casos_previstos_por_semana}
                Ex: {"A90": 150, "J18": 80}
    horizon_weeks : semanas de horizonte (multiplica a demanda semanal)

    Returns
    -------
    DataFrame com colunas: insumo, unidade, demanda_total, cids_associados
    """
    rows = []
    for cid, casos_semana in forecasts.items():
        insumos = insumos_for_cid(cid)
        for insumo, spec in insumos.items():
            consumo = spec.get("consumo_medio_por_caso", 0)
            unidade = spec.get("unidade", "unidade")
            demanda = casos_semana * consumo * horizon_weeks
            rows.append({
                "insumo": insumo,
                "unidade": unidade,
                "demanda_total": round(demanda),
                "cid": cid,
            })

    if not rows:
        return pd.DataFrame(columns=["insumo", "unidade", "demanda_total", "cid"])

    df = pd.DataFrame(rows)
    return (
        df.groupby(["insumo", "unidade"])
        .agg(demanda_total=("demanda_total", "sum"), cids_associados=("cid", lambda x: ", ".join(sorted(set(x)))))
        .reset_index()
        .sort_values("demanda_total", ascending=False)
    )


def project_by_municipio(
    alert_df: pd.DataFrame,
    municipio_col: str = "municipio",
    cid_col: str = "doenca",
    casos_col: str = "previsao_4sem",
    horizon_weeks: int = 4,
) -> pd.DataFrame:
    """Projeta demanda agregada por municipio.

    Parameters
    ----------
    alert_df : DataFrame de alertas com colunas municipio, doenca, previsao_4sem

    Returns
    -------
    DataFrame com colunas: municipio, insumo, unidade, demanda_total
    """
    dfs = []
    for municipio, group in alert_df.groupby(municipio_col):
        forecasts = {}
        for _, row in group.iterrows():
            cid = str(row.get(cid_col, ""))[:3]
            casos = float(row.get(casos_col, 0) or 0)
            forecasts[cid] = forecasts.get(cid, 0) + casos

        demand = project_demand(forecasts, horizon_weeks=horizon_weeks)
        if not demand.empty:
            demand[municipio_col] = municipio
            dfs.append(demand)

    if not dfs:
        return pd.DataFrame()

    result = pd.concat(dfs, ignore_index=True)
    return result[[municipio_col, "insumo", "unidade", "demanda_total", "cids_associados"]]
