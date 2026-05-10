# datasus-outbreak-prediction

Sistema de vigilancia epidemiologica integrada com dados publicos do SUS, SNIS e IBGE.

**App online:** [datasus-outbreak-prediction.streamlit.app](https://datasus-outbreak-prediction.streamlit.app)

---

## O problema

Surtos de doenca costumam ser identificados depois que ja se espalharam. Medicamentos chegam atrasados. Municipios com saneamento precario concentram doencas que seriam evitaveis. Nao ha uma visao integrada que conecte epidemiologia, infraestrutura urbana e planejamento de insumos.

Este projeto tenta responder: **e possivel prever onde um surto vai acontecer antes que vire crise?**

## O que o sistema faz

### Vigilancia de surtos
Monitora casos semanais de dengue, chikungunya e zika por municipio usando dados do InfoDengue. Detecta anomalias com z-score rolling e CUSUM, classifica nivel de alerta (verde, amarelo, vermelho) e projeta os proximos 4 semanas com LightGBM.

### Grafo MacroCID
Constroi uma rede de co-ocorrencia entre codigos CID-10 a partir dos dados de mortalidade do SIM/DATASUS. Agrupa CIDs em macrogrupos clinicos (doencas hidricas, vetoriais, respiratorias) e visualiza quais doencas tendem a aparecer juntas nas cadeias causais de obito.

### Planejamento de insumos
A partir das previsoes de casos, estima a demanda de medicamentos e insumos por municipio para os proximos 30 dias. Baseado nos Protocolos Clinicos do Ministerio da Saude (PCDT/MS).

### Mapa urbano: saneamento x doencas
Correlaciona cobertura de esgoto e agua (SNIS) com incidencia de doencas de veiculacao hidrica por municipio. Identifica os municipios de maior risco estrutural: baixo saneamento combinado com alta incidencia.

## Fontes de dados

| Fonte | Dados | Acesso |
|-------|-------|--------|
| InfoDengue | Casos semanais de dengue/chikungunya/zika | API REST publica |
| SIM/DATASUS | Mortalidade por CID-10 e municipio | HTTP mirror / FTP |
| SNIS | Cobertura de agua e esgoto por municipio | CSV download anual |
| IBGE | Dados demograficos e shapefile de municipios | API + GeoJSON |

## Instalacao local

```bash
git clone https://github.com/fabianofilho/datasus-outbreak-prediction
cd datasus-outbreak-prediction
pip install -r requirements.txt
streamlit run app.py
```

## Estrutura

```
datasus-outbreak-prediction/
├── app.py                   # Home: KPIs e resumo de alertas
├── pages/
│   ├── 01_surtos.py         # Serie temporal + previsao 4 semanas
│   ├── 02_macrocid.py       # Grafo CID-CID e heatmap de co-ocorrencia
│   ├── 03_insumos.py        # Demanda projetada de medicamentos
│   └── 04_mapa_urbano.py    # Saneamento x incidencia de doencas
├── core/
│   ├── data/                # Downloaders: SIM, InfoDengue, SNIS, IBGE
│   ├── surtos/              # Detector (z-score, CUSUM) + Forecaster (LightGBM)
│   ├── macrocid/            # Grupos MacroCID, grafo CID-CID, co-ocorrencia
│   ├── insumos/             # Mapeamento CID->insumos + projecao de demanda
│   ├── geo/                 # Correlacao saneamento + mapas
│   └── viz/                 # Plotly: grafos, series temporais
└── data/static/
    ├── macrocid_groups.json  # Grupos clinicos de CIDs
    └── cid_insumos.json      # Mapeamento CID -> insumos (PCDT/MS)
```

## MacroCID: grupos clinicos

| Grupo | CIDs principais | Relacao com saneamento |
|-------|----------------|------------------------|
| veiculacao_hidrica | A00-A09, A15-A19 | Alta - transmissao fecal-oral |
| vetorial | A90-A99, B50-B54 | Media - criadouros em agua parada |
| respiratorio | J09-J18, U07 | Baixa direta |
| cardiovascular_metabolico | I10-I15, E11-E14 | Via IDH e urbanizacao |
| violencia_trauma | V-W-X | Indireta |
| materno_infantil | O14-O15, P07 | Alta - acesso a agua potavel |

## Limitacoes

- O modulo de insumos projeta **demanda estimada**, nao estoque atual. Nao ha dados de estoque em tempo real no SUS publico.
- Dados SNIS tem atraso de 1-2 anos. Use como indicador estrutural de vulnerabilidade, nao de monitoramento em tempo real.
- O app online usa capitais como demo. Para analise completa de um estado, use `scripts/download_all.py` localmente.
- A pagina de Grafo MacroCID requer download dos arquivos DBC do DATASUS, que pode ser lento dependendo do ambiente.

## Origem

Nasceu de uma conversa sobre usar dados epidemiologicos para planejamento urbano: prever surtos antes que virem crise, mapear doencas relacionadas a saneamento e planejar o deslocamento de medicamentos com antecedencia.

Construido sobre [`datasus-ai-graphs`](https://github.com/fabianofilho/datasus-ai-graphs) e [`dengue-timeseries-skforecast`](https://github.com/fabianofilho/dengue-timeseries-skforecast).
