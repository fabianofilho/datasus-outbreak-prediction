"""Configuracao do app publico (OUT-16): protecoes ligadas e sem traceback."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10: usa o toml, dependencia do streamlit
    import toml as tomllib

CONFIG = Path(__file__).resolve().parent.parent / ".streamlit" / "config.toml"


def _config() -> dict:
    return tomllib.loads(CONFIG.read_text(encoding="utf-8"))


def test_xsrf_e_cors_nao_desligados():
    server = _config().get("server", {})

    # Ausente equivale ao padrao do Streamlit, que e ligado
    assert server.get("enableXsrfProtection", True) is True
    assert server.get("enableCORS", True) is True


def test_erros_sem_traceback_para_o_visitante():
    client = _config().get("client", {})

    # O valor legado false equivale a "stacktrace" e ainda manda o traceback
    # ao navegador; so "type" e "none" escondem traceback e mensagem
    assert client.get("showErrorDetails") in ("none", "type")


def test_excecao_nao_expoe_traceback_nem_caminho(tmp_path):
    """Aplica o valor do config.toml e confere o que chega ao navegador."""
    from streamlit import config
    from streamlit.testing.v1 import AppTest

    caminho = "/srv/interno/segredo.csv"
    script = tmp_path / "quebra.py"
    script.write_text(
        "import streamlit as st\n"
        f"raise FileNotFoundError({caminho!r})\n",
        encoding="utf-8",
    )

    anterior = config.get_option("client.showErrorDetails")
    config.set_option("client.showErrorDetails", _config()["client"]["showErrorDetails"])
    try:
        at = AppTest.from_file(str(script)).run()
    finally:
        config.set_option("client.showErrorDetails", anterior)

    assert len(at.exception) == 1
    erro = at.exception[0]
    assert list(erro.stack_trace) == []
    assert caminho not in erro.message
