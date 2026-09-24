"""Ranking do Mapa de Surtos (OUT-02): ordenacao sem KeyError."""

from __future__ import annotations

import pandas as pd

from core.surtos.detector import (
    AMARELO,
    NIVEL_RANK,
    RANKING_COLS,
    VERDE,
    VERMELHO,
    ranking_alertas,
)


def _map_df(com_rank: bool) -> pd.DataFrame:
    df = pd.DataFrame({
        "municipio": ["A (RJ)", "B (SP)", "C (MG)", "D (CE)", "E (AM)"],
        "geocode": ["1", "2", "3", "4", "5"],
        "uf": ["RJ", "SP", "MG", "CE", "AM"],
        "nivel_alerta": [VERDE, VERMELHO, AMARELO, VERMELHO, VERDE],
        "casos": [500.0, 10.0, 80.4, 300.0, 20.0],
        "z_score": [0.123, 3.456, 1.789, 4.0, -0.5],
        "lat": [0.0] * 5,
        "lon": [0.0] * 5,
    })
    if com_rank:
        # Como a pagina monta o map_df: nivel_rank ja existe e fica fora do recorte
        df["nivel_rank"] = df["nivel_alerta"].map(NIVEL_RANK)
    return df


def test_ranking_com_nivel_rank_no_map_df_nao_levanta_keyerror():
    display = ranking_alertas(_map_df(com_rank=True))

    assert list(display.columns) == RANKING_COLS
    assert display["municipio"].tolist() == ["D (CE)", "B (SP)", "C (MG)", "A (RJ)", "E (AM)"]


def test_ranking_ordena_por_gravidade_e_depois_casos():
    display = ranking_alertas(_map_df(com_rank=False))

    assert display["nivel_alerta"].tolist() == ["VERMELHO", "VERMELHO", "AMARELO", "VERDE", "VERDE"]
    assert display["casos"].tolist() == [300, 10, 80, 500, 20]
    assert display["z_score"].tolist() == [4.0, 3.46, 1.79, 0.12, -0.5]


def test_ranking_nivel_desconhecido_conta_como_verde():
    df = _map_df(com_rank=False)
    df.loc[0, "nivel_alerta"] = "sem_dado"

    display = ranking_alertas(df)

    assert display["nivel_alerta"].tolist()[-2:] == ["SEM_DADO", "VERDE"]


def test_ranking_nao_altera_map_df():
    df = _map_df(com_rank=True)
    antes = df.copy()

    ranking_alertas(df)

    pd.testing.assert_frame_equal(df, antes)
