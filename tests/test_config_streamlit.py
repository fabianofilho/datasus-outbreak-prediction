"""Configuracao do app publico (OUT-16): protecoes ligadas e sem traceback."""

from __future__ import annotations

import tomllib
from pathlib import Path

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

    assert client.get("showErrorDetails") in (False, "none", "type")
