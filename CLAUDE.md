# epidemio-urbano

## Projeto
Sistema de vigilancia epidemiologica integrada com dados do SUS, SNIS e IBGE.
Detecta surtos, preve demanda por insumos e correlaciona doencas com infraestrutura urbana.

## Arquitetura
- `core/data/`: download e preprocessamento (SIM, SIH, InfoDengue, SNIS, IBGE)
- `core/surtos/`: deteccao de anomalias (CUSUM, z-score) e previsao (skforecast + LightGBM)
- `core/macrocid/`: grafo CID-CID, grupos MacroCID, matriz de co-ocorrencia
- `core/insumos/`: projecao de demanda por insumos por regiao de saude
- `core/geo/`: correlacao saneamento x incidencia, mapas coropletidos
- `core/viz/`: visualizacoes Plotly (force-directed, heatmap, series temporais)
- `app.py` + `pages/`: interface Streamlit de 4 paginas

## Convencoes
- Documentacao em portugues sem acentos (compatibilidade com encodings legados)
- Sem emojis no codigo ou documentacao
- Sem travessoes, hifens decorativos ou aspas tipograficas
- Download via cascata: cache parquet -> HTTP mirror -> FTP DataSUS
- Testes com pytest

## Dependencias principais
- skforecast + lightgbm: previsao de series temporais
- networkx + plotly: grafos interativos
- datasus-dbc + dbfread: descompressao DBC
- streamlit: interface web

## Fontes de dados
| Fonte | Sistema | Acesso |
|-------|---------|--------|
| SIM/DATASUS | Mortalidade | FTP + HTTP mirror |
| InfoDengue | Dengue/arboviroses | API REST publica |
| SNIS | Saneamento | CSV download |
| IBGE | Demografico + shapefile | API + GeoJSON |

## Limitacao importante
O modulo de insumos projeta DEMANDA com base em casos previstos.
Nao ha dados de estoque em tempo real no SUS publico.
