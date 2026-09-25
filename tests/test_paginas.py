"""Smoke tests das paginas Streamlit com AppTest, sem rede.

Cada teste abre a pagina, escolhe uma doenca do caminho sintetico quando a
pagina pede doenca, clica em Analisar e verifica que o script chega ao fim
sem excecao. Os municipios vem do fallback de capitais (rede bloqueada).
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

RAIZ = Path(__file__).resolve().parent.parent

TIMEOUT = 180
DOENCA_SINTETICA = "diarreia_aguda"


def _erros(at: AppTest) -> list[str]:
    return [f"{e.message}\n{''.join(e.stack_trace)}" for e in at.exception]


def _abrir(pagina: str) -> AppTest:
    at = AppTest.from_file(str(RAIZ / pagina), default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, _erros(at)
    return at


def _analisar(at: AppTest, doenca: str | None = None) -> AppTest:
    if doenca is not None:
        at.sidebar.selectbox[0].set_value(doenca)
    at.sidebar.button[0].click().run()
    assert not at.exception, _erros(at)
    return at


def _specs_plotly(at: AppTest) -> list[dict]:
    return [json.loads(el.proto.spec) for el in at.get("plotly_chart")]


def _dataframes(at: AppTest) -> list[pd.DataFrame]:
    return [df.value for df in at.dataframe]


def test_home_sem_rede():
    at = _abrir("app.py")
    assert at.metric, "home deveria mostrar os KPIs mesmo sem dados"


def test_pagina_01_surtos_com_previsao():
    at = _analisar(_abrir("pages/01_surtos.py"), DOENCA_SINTETICA)

    assert not at.warning, [w.value for w in at.warning]
    brutos = [df for df in _dataframes(at) if "tipo" in df.columns]
    assert brutos, "tabela de dados brutos da previsao nao apareceu"
    assert (brutos[0]["tipo"] == "previsto").sum() == 4


def _sim_sintetico(state: str, year: int, progress_callback=None) -> pd.DataFrame:
    """Imita o DataFrame bruto do SIM com cadeias causais repetidas."""
    cadeias = [
        ("I219", "I10", "E119"),
        ("J189", "J449", "I10"),
        ("A09", "E86", ""),
        ("A90", "R571", ""),
        ("C349", "J189", ""),
    ]
    linhas = []
    for i in range(200):
        causa, linha_b, linha_a = cadeias[i % len(cadeias)]
        linhas.append({
            "NUMERODO": f"{i:08d}",
            "DTOBITO": f"15{(i % 12) + 1:02d}{year}",
            "DTNASC": "01011950",
            "IDADE": "470",
            "SEXO": "1" if i % 2 else "2",
            "RACACOR": "1",
            "CAUSABAS": causa,
            "LINHAA": linha_a,
            "LINHAB": linha_b,
            "LINHAC": "",
            "LINHAD": "",
            "CODMUNOCOR": "330455",
            "CODMUNRES": "330455",
        })
    return pd.DataFrame(linhas)


def test_pagina_02_macrocid_com_sim_sintetico(monkeypatch):
    import core.data.downloader as downloader

    monkeypatch.setattr(downloader, "fetch", _sim_sintetico)
    at = _analisar(_abrir("pages/02_macrocid.py"))

    assert not at.warning, [w.value for w in at.warning]
    rotulos = {m.label for m in at.metric}
    assert {"Nós (CIDs)", "Arestas"} <= rotulos


def test_pagina_03_insumos_com_previsao():
    at = _analisar(_abrir("pages/03_insumos.py"), DOENCA_SINTETICA)

    assert not at.warning, [w.value for w in at.warning]
    demanda = [df for df in _dataframes(at) if "demanda_total" in df.columns]
    assert demanda and not demanda[0].empty


def test_pagina_04_mapa_urbano_com_snis_sintetico():
    at = _analisar(_abrir("pages/04_mapa_urbano.py"))

    rotulos = {m.label for m in at.metric}
    assert "Spearman rho" in rotulos
    tipos = [t.get("mode") for spec in _specs_plotly(at) for t in spec["data"]]
    assert "lines" in tipos, "reta de tendencia ausente no scatter"


def test_pagina_05_mapa_surtos_com_ranking():
    at = _analisar(_abrir("pages/05_mapa_surtos.py"), DOENCA_SINTETICA)

    assert not at.warning, [w.value for w in at.warning]
    tipos = {t["type"] for spec in _specs_plotly(at) for t in spec["data"]}
    assert "scattermap" in tipos

    ranking = [df for df in _dataframes(at) if "nivel_alerta" in df.columns]
    assert ranking, "tabela de ranking nao apareceu"
    assert list(ranking[0].columns) == ["municipio", "uf", "nivel_alerta", "casos", "z_score"]
    assert len(ranking[0]) == 5


@pytest.mark.parametrize("pagina", [
    "pages/01_surtos.py",
    "pages/02_macrocid.py",
    "pages/03_insumos.py",
    "pages/04_mapa_urbano.py",
    "pages/05_mapa_surtos.py",
])
def test_estado_vazio_antes_de_analisar(pagina):
    at = _abrir(pagina)
    assert at.sidebar.button[0].label == "Analisar"
