"""Baixa dados SIM e InfoDengue para um estado/ano completo."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data import downloader
from core.data.infodengue import fetch_city, DISEASES
from core.data.ibge import municipios


def main():
    parser = argparse.ArgumentParser(description="Baixa dados epidemiologicos para um estado/ano")
    parser.add_argument("--state", default="RJ", help="Sigla do estado (ex: RJ)")
    parser.add_argument("--year", type=int, default=2022, help="Ano")
    parser.add_argument("--infodengue", action="store_true", help="Baixar InfoDengue para todos os municipios do estado")
    args = parser.parse_args()

    print(f"Baixando SIM {args.state} {args.year}...")
    try:
        df = downloader.fetch(args.state, args.year, progress_callback=lambda p, m: print(f"  {m}"))
        print(f"  SIM: {len(df):,} registros")
    except Exception as e:
        print(f"  Erro SIM: {e}")

    if args.infodengue:
        print(f"\nBaixando InfoDengue para municipios de {args.state}...")
        muns = municipios(uf=args.state)
        print(f"  {len(muns)} municipios encontrados")

        for doenca in DISEASES:
            print(f"  Doenca: {doenca}")
            for _, row in muns.head(20).iterrows():
                try:
                    df = fetch_city(row["codigo"], doenca, 2020, 2024)
                    if not df.empty:
                        print(f"    {row['nome']}: {len(df)} semanas")
                except Exception:
                    pass


if __name__ == "__main__":
    main()
