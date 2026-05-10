# epidemio-urbano

Sistema de vigilancia epidemiologica integrada com dados publicos do SUS, SNIS e IBGE.

Detecta surtos, preve demanda por insumos e correlaciona doencas com infraestrutura urbana.

## Funcionalidades

- **Vigilancia de surtos**: z-score rolling + CUSUM + previsao LightGBM (4 semanas)
- **Grafo MacroCID**: rede de co-ocorrencia entre grupos de CIDs do SIM/DATASUS
- **Planejamento de insumos**: projecao de demanda por medicamentos por regiao
- **Mapa urbano**: correlacao cobertura de saneamento x incidencia de doencas

## Fontes de dados

| Fonte | Dados | Acesso |
|-------|-------|--------|
| SIM/DATASUS | Mortalidade por CID-10 e municipio | HTTP mirror / FTP |
| InfoDengue | Casos semanais de dengue/chikungunya/zika | API REST publica |
| SNIS | Cobertura de agua e esgoto por municipio | CSV download anual |
| IBGE | Demografico + shapefile de municipios | API + GeoJSON |

## Instalacao

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estrutura

```
epidemio-urbano/
├── app.py                   # Home: KPIs e mapa resumo de alertas
├── pages/
│   ├── 01_surtos.py         # Vigilancia: serie temporal + previsao
│   ├── 02_macrocid.py       # Grafo CID-CID e heatmap de co-ocorrencia
│   ├── 03_insumos.py        # Demanda projetada de insumos
│   └── 04_mapa_urbano.py    # Saneamento x incidencia de doencas
├── core/
│   ├── data/                # Downloaders: SIM, InfoDengue, SNIS, IBGE
│   ├── surtos/              # Detector (z-score, CUSUM) + Forecaster (LightGBM)
│   ├── macrocid/            # Grupos MacroCID, grafo CID-CID, co-ocorrencia
│   ├── insumos/             # Mapeamento CID->insumos + projecao de demanda
│   ├── geo/                 # Correlacao saneamento + mapas
│   └── viz/                 # Plotly: grafos, series temporais
├── data/
│   └── static/
│       ├── macrocid_groups.json  # Grupos clinicos de CIDs
│       └── cid_insumos.json      # Mapeamento CID -> insumos (PCDT/MS)
└── scripts/
    ├── download_all.py      # Baixa dados de um estado/ano
    └── build_cache.py       # Pre-processa e salva parquets
```

## MacroCID: grupos clinicos

| Grupo | CIDs | Relacao com saneamento |
|-------|------|----------------------|
| veiculacao_hidrica | A00-A09, A15-A19 | Alta - transmissao fecal-oral |
| vetorial | A90-A99, B50-B54 | Media - criadouros em agua parada |
| respiratorio | J09-J18, U07 | Baixa direta |
| cardiovascular_metabolico | I10-I15, E11-E14 | Via IDH e urbanizacao |
| violencia_trauma | V-W-X | Indireta |
| materno_infantil | O14-O15, P07 | Alta - acesso a agua potavel |

## Dados de saneamento (SNIS)

Para usar a pagina de Mapa Urbano com dados reais:

1. Acesse http://app4.mdr.gov.br/serieHistorica/
2. Baixe a serie historica completa (CSV)
3. Salve em `data/static/snis_<ano>.csv`

Os dados tem atraso de 1-2 anos. Use como indicador estrutural de vulnerabilidade,
nao para monitoramento em tempo real.

## Limitacao importante

O modulo de insumos projeta **demanda estimada** com base em previsoes epidemiologicas.
Nao ha dados de estoque em tempo real disponiveis publicamente no SUS.
O output deve ser interpretado como estimativa de necessidade, nao de deficit.

## Origem do projeto

Surgiu de uma conversa sobre usar dados epidemiologicos para planejamento urbano:
prever surtos antes que virem crise, mapear doencas relacionadas a saneamento,
e planejar o deslocamento de medicamentos com antecedencia.

Construido sobre `datasus-ai-graphs` (grafos CID/SIM) e `dengue-timeseries-skforecast` (previsao).
