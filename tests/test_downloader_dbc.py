"""Leitura de DBC do SIM: dependencias declaradas e caminho DBC -> DataFrame."""

from __future__ import annotations

import struct
import sys

import pytest

from core.data import downloader

_SEM_WHEEL = sys.version_info >= (3, 13)


def _dbf_bytes(campos: list[tuple[str, int]], registros: list[list[str]]) -> bytes:
    """Monta um DBF dBase III minimo com campos de texto."""
    tam_registro = 1 + sum(tam for _, tam in campos)
    tam_header = 32 + 32 * len(campos) + 1
    header = struct.pack("<BBBBIHH20x", 0x03, 124, 1, 1, len(registros), tam_header, tam_registro)
    descritores = b"".join(
        struct.pack("<11sc4xBB14x", nome.encode("ascii"), b"C", tam, 0)
        for nome, tam in campos
    )
    corpo = b"".join(
        b" " + b"".join(v.encode("latin-1").ljust(tam) for v, (_, tam) in zip(reg, campos))
        for reg in registros
    )
    return header + descritores + b"\r" + corpo + b"\x1a"


@pytest.mark.skipif(_SEM_WHEEL, reason="datasus-dbc sem wheel para Python >= 3.13")
def test_bibliotecas_dbc_instaladas():
    import datasus_dbc
    import dbfread

    assert callable(datasus_dbc.decompress_bytes)
    assert hasattr(dbfread, "DBF")


@pytest.mark.skipif(_SEM_WHEEL, reason="datasus-dbc sem wheel para Python >= 3.13")
def test_dbc_to_df_le_registros(monkeypatch):
    import datasus_dbc

    dbf = _dbf_bytes(
        [("CAUSABAS", 4), ("LINHAA", 8)],
        [["I219", "I10"], ["J189", "J449"]],
    )
    # A descompressao em si e da lib; aqui so o DBF resultante importa
    monkeypatch.setattr(datasus_dbc, "decompress_bytes", lambda _: dbf)

    df = downloader._dbc_to_df(b"conteudo dbc")

    assert list(df.columns) == ["CAUSABAS", "LINHAA"]
    assert df["CAUSABAS"].tolist() == ["I219", "J189"]
    assert df["LINHAA"].tolist() == ["I10", "J449"]
