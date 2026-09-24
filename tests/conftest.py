"""Fixtures comuns dos testes.

Coloca a raiz do repositorio no sys.path e bloqueia a rede: InfoDengue,
API do IBGE, mirror HTTP e FTP do DataSUS levantam erro. Assim os modulos
de dados caem nos caminhos de fallback (capitais fixas, serie sintetica
SINAN, SNIS sintetico) e os testes rodam offline e de forma deterministica.
"""

from __future__ import annotations

import ftplib
import sys
from pathlib import Path

import pytest
import requests

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


def _rede_bloqueada(*args, **kwargs):
    raise requests.ConnectionError("rede bloqueada nos testes")


def _ftp_bloqueado(*args, **kwargs):
    raise OSError("FTP bloqueado nos testes")


@pytest.fixture(autouse=True)
def sem_rede(monkeypatch):
    """Impede qualquer chamada externa e ignora o cache local do IBGE."""
    monkeypatch.setattr(requests.sessions.Session, "request", _rede_bloqueada)
    monkeypatch.setattr(ftplib.FTP, "connect", _ftp_bloqueado)

    import core.data.municipios as municipios

    monkeypatch.setattr(municipios, "_from_cache", lambda: None)


@pytest.fixture(autouse=True)
def cache_streamlit_limpo():
    """Evita que st.cache_data vaze resultados de um teste para outro."""
    import streamlit as st

    st.cache_data.clear()
    yield
    st.cache_data.clear()
