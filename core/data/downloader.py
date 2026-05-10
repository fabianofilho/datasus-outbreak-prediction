"""DataSUS SIM downloader with local parquet cache.

Download strategy (tried in order):
1. Cache hit        -> load parquet from disk, skip download.
2. HTTP mirror      -> DigitalOcean CDN mirror of DataSUS FTP (fast, no auth).
3. Direct FTP       -> ftp.datasus.gov.br with passive mode.
4. Error            -> raise DownloadError with instructions.

DBC decompression uses `datasus-dbc` (pure Python / pre-compiled wheel,
works on Windows without a C compiler).

Verified filename pattern (from FTP inspection):
  SIM -> /dissemin/publicos/SIM/CID10/DORES/DO{state}{year}.dbc (annual per state)
"""

from __future__ import annotations

import ftplib
import io
import tempfile
from pathlib import Path

import pandas as pd
import requests

_local_dir = Path(__file__).parent.parent.parent / "data" / "raw"
_tmp_dir = Path("/tmp/datasus_graphs_raw")
try:
    _local_dir.mkdir(parents=True, exist_ok=True)
    RAW_DIR = _local_dir
except (PermissionError, OSError):
    _tmp_dir.mkdir(parents=True, exist_ok=True)
    RAW_DIR = _tmp_dir

STATES = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO",
]

FTP_HOST = "ftp.datasus.gov.br"
HTTP_MIRROR = "https://datasus-ftp-mirror.nyc3.cdn.digitaloceanspaces.com"

FTP_PATH = "/dissemin/publicos/SIM/CID10/DORES/"
HTTP_PATH = "SIM/CID10/DORES/"


class DownloadError(Exception):
    """Raised when automatic download failed."""
    def __init__(self, state: str, year: int, reason: str = ""):
        self.state = state
        self.year = year
        self.reason = reason
        super().__init__(
            f"Nao foi possivel baixar SIM {state} {year}. {reason}"
        )


# -- Cache -------------------------------------------------------------------

def _cache_path(state: str, year: int) -> Path:
    return RAW_DIR / f"sim_{state.upper()}_{year}.parquet"


def _save(df: pd.DataFrame, state: str, year: int) -> pd.DataFrame:
    df.to_parquet(_cache_path(state, year), index=False)
    return df


# -- Filename helpers --------------------------------------------------------

def _filename(state: str, year: int) -> str:
    return f"DO{state.upper()}{year}.dbc"


def _name_variants(name: str) -> list[str]:
    return list(dict.fromkeys([name, name.upper(), name.lower()]))


# -- DBC -> DataFrame -------------------------------------------------------

def _dbc_to_df(dbc_bytes: bytes) -> pd.DataFrame:
    """Decompress DBC bytes -> DataFrame via datasus-dbc + dbfread."""
    from datasus_dbc import decompress_bytes
    import dbfread

    dbf_bytes = decompress_bytes(dbc_bytes)
    with tempfile.NamedTemporaryFile(suffix=".dbf", delete=False) as f:
        f.write(dbf_bytes)
        tmp = Path(f.name)
    try:
        records = list(dbfread.DBF(str(tmp), encoding="latin-1"))
        return pd.DataFrame(records)
    finally:
        tmp.unlink(missing_ok=True)


# -- HTTP fetch --------------------------------------------------------------

def _http_get(filename: str) -> bytes | None:
    for variant in _name_variants(filename):
        url = f"{HTTP_MIRROR}/{HTTP_PATH}{variant}"
        try:
            resp = requests.get(url, timeout=120, stream=True)
            if resp.status_code == 200:
                return resp.content
        except Exception:
            continue
    return None


# -- FTP fetch ---------------------------------------------------------------

def _ftp_get(filename: str) -> bytes | None:
    try:
        with ftplib.FTP(FTP_HOST, timeout=60) as ftp:
            ftp.login()
            ftp.set_pasv(True)
            for variant in _name_variants(filename):
                buf = io.BytesIO()
                try:
                    ftp.retrbinary(f"RETR {FTP_PATH}{variant}", buf.write)
                    return buf.getvalue()
                except ftplib.error_perm:
                    continue
    except Exception:
        pass
    return None


# -- Public API --------------------------------------------------------------

def fetch(
    state: str,
    year: int,
    progress_callback=None,
) -> pd.DataFrame:
    """Download SIM data for a state/year with cache and fallback."""
    cache = _cache_path(state, year)

    # 0. Cache hit
    if cache.exists():
        if progress_callback:
            progress_callback(1.0, f"SIM {state} {year} (cache local)")
        return pd.read_parquet(cache)

    errors = []
    fname = _filename(state, year)

    # 1. HTTP mirror
    if progress_callback:
        progress_callback(0.2, f"SIM {state} {year}: mirror HTTP...")
    raw = _http_get(fname)
    if raw:
        try:
            df = _dbc_to_df(raw)
            if len(df) > 0:
                if progress_callback:
                    progress_callback(1.0, f"SIM {state} {year} via HTTP")
                return _save(df, state, year)
        except Exception as e:
            errors.append(f"HTTP decompression: {e}")
    else:
        errors.append("mirror HTTP falhou")

    # 2. FTP direto
    if progress_callback:
        progress_callback(0.5, f"SIM {state} {year}: FTP DataSUS...")
    raw = _ftp_get(fname)
    if raw:
        try:
            df = _dbc_to_df(raw)
            if len(df) > 0:
                if progress_callback:
                    progress_callback(1.0, f"SIM {state} {year} via FTP")
                return _save(df, state, year)
        except Exception as e:
            errors.append(f"FTP decompression: {e}")
    else:
        errors.append("FTP DataSUS falhou")

    raise DownloadError(state, year, reason=" | ".join(errors))


def fetch_multi(
    states: list[str],
    years: list[int],
    progress_callback=None,
) -> pd.DataFrame:
    """Download SIM data for multiple states/years."""
    dfs = []
    total = len(states) * len(years)
    for i, (state, year) in enumerate((s, y) for s in states for y in years):
        def cb(pct, msg, _i=i, _t=total):
            if progress_callback:
                progress_callback((_i + pct) / _t, msg)
        dfs.append(fetch(state, year, cb))
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def cached_files() -> list[str]:
    """List cached parquet files."""
    return [p.name for p in RAW_DIR.glob("*.parquet")]
