# epidemio-urbano

## Projeto
Sistema de vigilancia epidemiologica integrada com dados do SUS, SNIS e IBGE.
Detecta surtos, preve demanda por insumos e correlaciona doencas com infraestrutura urbana.
App Streamlit publico (demo) com 5 paginas + home.

## Arquitetura
- `core/data/`: download e preprocessamento (SIM, InfoDengue, SINAN sintetico, SNIS, IBGE municipios)
- `core/surtos/`: deteccao de anomalias (CUSUM, z-score) e previsao (skforecast + LightGBM)
- `core/macrocid/`: grafo CID-CID, grupos MacroCID, matriz de co-ocorrencia
- `core/insumos/`: projecao de demanda por insumos por regiao de saude
- `core/geo/`: correlacao saneamento x incidencia
- `core/viz/`: design system (`theme.py`) + Plotly timeseries e grafos
- `app.py` + `pages/01..05_*.py`: interface Streamlit

## Convencoes de codigo
- Docstrings e comentarios em portugues sem acentos (encoding legado)
- Sem emojis no codigo; emojis so em `page_icon` do Streamlit
- Sem travessoes, hifens decorativos ou aspas tipograficas
- Testes com pytest

## Padroes de UI (Streamlit)
- Design system em `core/viz/theme.py`: inject(), badge(), footer(), sidebar_back(),
  module_card(), empty_state()
- Paleta: --sus-blue #0047bb, --sus-green #009c3b, fundo #f8fafc
- Todas as sub-paginas: initial_sidebar_state="expanded", sidebar_back() no topo
- Sidebar fixa (sem botao de colapso): 4 seletores CSS no theme.py
- Padrao de carregamento: estado vazio + botao "Analisar" -> session_state -> dados
  - Chaves de session_state: surtos_ok/cfg, insumos_ok/cfg, mapa_ok/cfg,
    macrocid_ok/cfg, urbano_ok/cfg
  - Mudar filtro nao recarrega; usuario precisa clicar "Analisar" novamente

## Fontes de dados e roteamento
| Fonte | Sistema | Acesso | Modulo |
|-------|---------|--------|--------|
| InfoDengue | Dengue/arboviroses | API REST publica | `core/data/infodengue.py` |
| SINAN sintetico | Gastrointestinais, respiratorias | Gerador local | `core/data/sinan.py` |
| SIM/DATASUS | Mortalidade (CID-CID) | FTP (falha no Cloud) | `core/data/sim.py` |
| SNIS | Saneamento basico | CSV manual | `core/data/snis.py` |
| IBGE municipios | 5.570 municipios | API publica + cache | `core/data/municipios.py` |

Roteamento em `fetch_city()`:
- `{"dengue","chikungunya","zika"}` -> InfoDengue REST API (dados reais)
- Demais doencas -> `sinan.generate()` (sintetico com sazonalidade)

9 doencas suportadas: dengue, chikungunya, zika, diarreia_aguda, hepatite_a,
leptospirose, febre_tifoide, influenza_a, srag

## Municipios brasileiros (IBGE)
`core/data/municipios.py`:
- `load()` -> DataFrame com nome, uf, geocode (5.570 municipios)
- `display_options()` -> dict {"Nome (UF)": "geocode"} para multiselect
- `default_capitals()` -> lista de nomes das 5 capitais para default
- Cache local em `data/cache/municipios_ibge.json` (TTL: arquivo existe)
- Fallback automatico: 27 capitais hardcoded se API IBGE indisponivel
- Municipios sem coordenada em `_COORDS_FIXAS` (page 05) aparecem no
  centro do Brasil - issue conhecida, ver TODO

## Streamlit Cloud
- `datasus_dbc` e `dbfread` NAO tem wheel para Linux: usar sempre dentro de
  `try/except ModuleNotFoundError` e retornar `pd.DataFrame()` no except
- `data/cache/` esta no .gitignore; cache e recriado em runtime
- Mapa usa `carto-positron` do Plotly (sem token Mapbox)

## Limitacoes conhecidas e documentadas
- Insumos: projeta DEMANDA, nao estoque real (sem API de estoque SUS publica)
- SINAN: dados reais em DBC/FTP, incompativel com Streamlit Cloud; usar sintetico
- SNIS: atraso de 1-2 anos; usar como indicador estrutural, nao operacional
- SIM/DATASUS (pagina MacroCID): pode falhar no Streamlit Cloud por FTP

## Dependencias principais
- skforecast + lightgbm: previsao de series temporais
- networkx + plotly: grafos interativos
- streamlit: interface web
- requests: InfoDengue API + IBGE API
