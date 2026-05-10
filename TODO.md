# TODO, epidemio-urbano

App Streamlit de vigilancia epidemiologica integrada: surtos, grafos CID-CID, demanda por insumos e correlacao saneamento x doencas. Demo publica com dados reais (InfoDengue) e sinteticos (SINAN/SIVEP).

---

## STATUS ATUAL DO ROADMAP

### Concluido e commitado

- [x] **Design system e home** (commit `54fa2fa`)
  - Card grid de navegacao na home sem sidebar (padrao datasus-ai-prediction)
  - CSS injetado via `core/viz/theme.py`: cores, tipografia Inter, sidebar fixa
  - Favicon SVG + emoji 🦠 em todas as paginas

- [x] **Pagina 5: Mapa de Surtos** (commit `a3511f3`)
  - `scatter_mapbox` Plotly com `carto-positron` (sem token Mapbox)
  - Nivel de alerta por z-score rolante, tamanho da bolha proporcional a casos
  - KPIs: cidades monitoradas, alertas vermelho/amarelo/verde

- [x] **Expansao de doencas: gastrointestinais e respiratorias** (commit `934fa3c`)
  - Novo `core/data/sinan.py`: gerador sintetico com sazonalidade brasileira real
  - 9 doencas totais: dengue, chikungunya, zika, diarreia_aguda, hepatite_a,
    leptospirose, febre_tifoide, influenza_a, srag
  - Roteamento automatico em `fetch_city()`: arboviroses -> InfoDengue API,
    demais -> sinan.generate()
  - `DISEASE_GROUPS`, `DISEASE_LABELS`, `DISEASE_CID` para UI e mapeamento insumos

- [x] **Fixes de producao** (commits `da6f231`, `b597bfa`)
  - `downloader.py`: `datasus_dbc` e `dbfread` com try/except ModuleNotFoundError
    (incompativeis com Streamlit Cloud)
  - Acentuacao portuguesa corrigida em todos os arquivos
  - Sidebar fixa (4 seletores CSS para cobrir versoes do Streamlit)

- [x] **Load on demand + busca livre de municipios** (commit `144b140`)
  - Novo `core/data/municipios.py`: busca 5.570 municipios via API IBGE,
    cache local em `data/cache/municipios_ibge.json`, fallback para capitais
  - Todas as paginas: estado vazio inicial + botao "Analisar" explicitio
  - Estado persiste em `st.session_state` por pagina (chaves: surtos_ok,
    insumos_ok, mapa_ok, macrocid_ok, urbano_ok)
  - `empty_state()` adicionado ao design system com card dashed

### EM PROGRESSO (nada parado no meio)

Nada em progresso. Repo limpo, todos os commits pushados.

### PROXIMOS PASSOS NA ORDEM

- [ ] **Coordenadas para municipios sem lat/lon fixo**
  - Municipios selecionados que nao estao em `_COORDS_FIXAS` aparecem
    todos no centro do Brasil no mapa de surtos
  - Como resolver: adicionar chamada a API IBGE de malhas municipais
    (`/api/v3/malhas/municipios/{geocode}?formato=application/json`)
    com cache, ou baixar CSV de centroides do IBGE e bundlar em `data/static/`
  - Referencia: `pages/05_mapa_surtos.py`, dict `_COORDS_FIXAS` (linha ~35)

- [ ] **Streamlit Cloud deploy**
  - Configurar `secrets.toml` ou variaveis de ambiente se necessario
  - Testar `requirements.txt` no ambiente Linux (sem datasus-dbc)
  - URL atual: nao deployado ainda

- [ ] **Dados reais SNIS para pagina 04 (Mapa Urbano)**
  - Sem CSV SNIS, a pagina exibe dados sinteticos
  - Baixar em: http://app4.mdr.gov.br/serieHistorica/
  - Salvar em `data/static/snis_<ano>.csv`
  - `core/data/snis.py` ja sabe ler o formato

- [ ] **Testes unitarios** (`pytest tests/`)
  - `core/data/sinan.py`: testar sazonalidade e determinismo do seed
  - `core/data/municipios.py`: testar fallback quando API IBGE indisponivel
  - `core/surtos/detector.py`: testar z-score e classificacao verde/amarelo/vermelho

- [ ] **Grafo CID-CID com dados reais**
  - Pagina 02 depende do SIM/DATASUS via FTP, que pode falhar no Streamlit Cloud
  - Alternativa: gerar grafos sinteticos como o SINAN, ou pre-processar e
    bundlar parquets por estado/ano no repo

---

## INFRA

- **Cache de dados**: `data/cache/` para parquets InfoDengue e JSON IBGE
  municipios. Ja no .gitignore (nao subir dados brutos).
- **Streamlit Cloud**: `datasus_dbc` e `dbfread` com lazy import protegido
  por try/except. Resto do requirements.txt compativel com Linux.
- **API IBGE municipios**: `https://servicodados.ibge.gov.br/api/v1/localidades/municipios`
  - Sem autenticacao, timeout 15s, cache persistente em disco
  - Fallback automatico para lista de 27 capitais

## HISTORICO

Sessao 1 (2026-05-10): Criacao do repo a partir de ideias de Joao Maia.
Reuso de `datasus-ai-graphs` (grafo CID) e `dengue-timeseries-skforecast`
(previsao LightGBM). App de 5 paginas funcional com demo.

Sessao 2 (2026-05-10, continuacao): Expansao de doencas, mapa de surtos,
redesign da sidebar, favicon, acentos, sidebar fixa, load on demand e
busca livre de todos os municipios brasileiros.
