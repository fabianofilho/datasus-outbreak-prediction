"""Design system: mesmas cores e tipografia do datasus-ai-search.

Paleta:
  --sus-blue  : #0047bb
  --sus-green : #009c3b
  fundo body  : #f8fafc
  texto       : #1e293b
  cards       : branco com borda #e2e8f0
"""

from __future__ import annotations

import streamlit as st

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:ital@1&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20,300,0,0');

:root {
  --sus-blue   : #0047bb;
  --sus-green  : #009c3b;
  --slate-50   : #f8fafc;
  --slate-100  : #f1f5f9;
  --slate-200  : #e2e8f0;
  --slate-400  : #94a3b8;
  --slate-500  : #64748b;
  --slate-700  : #334155;
  --slate-900  : #0f172a;
  --text       : #1e293b;
  --alert-red  : #e74c3c;
  --alert-yellow: #f39c12;
  --alert-green : #2ecc71;
}

* { box-sizing: border-box; }

html, body, [class*="css"] {
  font-family: 'Inter', system-ui, sans-serif !important;
  color: var(--text);
}

/* fundo geral */
.stApp {
  background-color: var(--slate-50) !important;
}

/* bloco principal: menos padding topo */
.block-container {
  padding-top: 1.5rem !important;
  padding-bottom: 3rem !important;
  max-width: 1100px !important;
}

/* --- Header personalizado --- */
.sus-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 0 18px 0;
  border-bottom: 1px solid var(--slate-200);
  margin-bottom: 1.5rem;
}
.sus-header-icon {
  width: 36px; height: 36px;
  background: var(--sus-blue);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.sus-header-icon svg { color: white; width: 20px; height: 20px; }
.sus-header-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--slate-900);
  line-height: 1.2;
  letter-spacing: -0.01em;
}
.sus-header-sub {
  font-size: 0.65rem;
  font-weight: 500;
  color: var(--slate-400);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.sus-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--sus-green);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 0.5rem;
}

/* --- Cards genericos --- */
.sus-card {
  background: #ffffff;
  border: 1px solid var(--slate-200);
  border-radius: 12px;
  padding: 1.25rem 1.5rem;
  margin-bottom: 1rem;
  animation: fadeIn 0.35s ease-in-out;
}
.sus-card-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--slate-500);
  text-transform: uppercase;
  letter-spacing: 0.07em;
  margin-bottom: 0.5rem;
}

/* --- Cards de modulo (navegacao home) --- */
.sus-module-card {
  background: #ffffff;
  border: 1px solid var(--slate-200);
  border-radius: 10px;
  padding: 1.1rem 1.25rem 0.9rem;
  margin-bottom: 0.25rem;
  min-height: 140px;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  transition: border-color 0.12s, box-shadow 0.12s;
  animation: fadeIn 0.35s ease-in-out;
}
.sus-module-card:hover {
  border-color: var(--sus-blue);
  box-shadow: 0 2px 8px rgba(0,71,187,0.08);
}
.sus-module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.sus-module-icon {
  width: 32px; height: 32px;
  background: #eff6ff;
  border-radius: 7px;
  display: flex; align-items: center; justify-content: center;
}
.sus-module-icon .material-symbols-outlined {
  font-size: 1.1rem;
  color: var(--sus-blue);
  font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 20;
}
.sus-module-source {
  font-size: 0.6rem;
  font-weight: 600;
  color: var(--slate-400);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  background: var(--slate-100);
  padding: 2px 7px;
  border-radius: 4px;
}
.sus-module-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--slate-900);
  line-height: 1.3;
}
.sus-module-desc {
  font-size: 0.72rem;
  color: var(--slate-500);
  line-height: 1.45;
  flex: 1;
}

/* page_link estilizado como botao de modulo */
.sus-module-link a {
  display: inline-flex !important;
  align-items: center;
  gap: 4px;
  font-size: 0.72rem !important;
  font-weight: 600 !important;
  color: var(--sus-blue) !important;
  text-decoration: none !important;
  padding: 4px 0 !important;
  border: none !important;
  background: transparent !important;
  transition: opacity 0.12s;
}
.sus-module-link a:hover { opacity: 0.7; }

/* esconde o nav automatico do Streamlit na sidebar */
[data-testid="stSidebarNav"] { display: none !important; }

/* --- Metricas --- */
div[data-testid="metric-container"] {
  background: #ffffff;
  border: 1px solid var(--slate-200);
  border-radius: 12px;
  padding: 1rem 1.25rem !important;
}
div[data-testid="metric-container"] label {
  font-size: 0.7rem !important;
  font-weight: 600 !important;
  color: var(--slate-500) !important;
  text-transform: uppercase;
  letter-spacing: 0.07em;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-size: 1.6rem !important;
  font-weight: 700 !important;
  color: var(--slate-900) !important;
}

/* --- Alertas de nivel --- */
.alert-vermelho {
  border-left: 4px solid var(--alert-red);
  background: #fff5f5;
  border-radius: 0 8px 8px 0;
  padding: 0.75rem 1rem;
  margin: 0.25rem 0;
  animation: fadeIn 0.35s ease-in-out;
}
.alert-amarelo {
  border-left: 4px solid var(--alert-yellow);
  background: #fffbf0;
  border-radius: 0 8px 8px 0;
  padding: 0.75rem 1rem;
  margin: 0.25rem 0;
}
.alert-verde {
  border-left: 4px solid var(--alert-green);
  background: #f0fff4;
  border-radius: 0 8px 8px 0;
  padding: 0.75rem 1rem;
  margin: 0.25rem 0;
}

/* --- Sidebar fixa (sem botao de colapsar) --- */
[data-testid="stSidebar"] {
  background-color: #ffffff !important;
  border-right: 1px solid var(--slate-200) !important;
}
[data-testid="collapsedControl"]          { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
button[data-testid="baseButton-headerNoPadding"] { display: none !important; }
section[data-testid="stSidebar"] > div > div > div > button { display: none !important; }
[data-testid="stSidebar"] .block-container {
  padding-top: 1.5rem !important;
  max-width: 100% !important;
}
[data-testid="stSidebarContent"] h2,
[data-testid="stSidebarContent"] h3 {
  font-size: 0.7rem !important;
  font-weight: 700 !important;
  color: var(--slate-400) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
}

/* link "voltar" na sidebar */
.sus-back-link a {
  font-size: 0.75rem !important;
  font-weight: 500 !important;
  color: var(--slate-500) !important;
  text-decoration: none !important;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 0 12px;
  border-bottom: 1px solid var(--slate-200);
  margin-bottom: 1rem;
}
.sus-back-link a:hover { color: var(--sus-blue) !important; }

/* --- Botoes --- */
.stButton button {
  border-radius: 8px !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
  border: 1px solid var(--slate-200) !important;
  color: var(--slate-700) !important;
  background: #ffffff !important;
  transition: all 0.15s !important;
}
.stButton button:hover {
  border-color: var(--slate-400) !important;
  color: var(--slate-900) !important;
}

/* --- Tabs --- */
.stTabs [data-baseweb="tab-list"] {
  gap: 0 !important;
  border-bottom: 1px solid var(--slate-200) !important;
  background: transparent !important;
}
.stTabs [data-baseweb="tab"] {
  font-size: 0.8rem !important;
  font-weight: 500 !important;
  color: var(--slate-500) !important;
  border-radius: 0 !important;
  padding: 0.5rem 1rem !important;
}
.stTabs [aria-selected="true"] {
  color: var(--sus-blue) !important;
  border-bottom: 2px solid var(--sus-blue) !important;
  font-weight: 600 !important;
}

/* --- Selectbox e inputs --- */
.stSelectbox div[data-baseweb="select"] > div {
  border-radius: 8px !important;
  border-color: var(--slate-200) !important;
  font-size: 0.875rem !important;
}

/* --- Divider --- */
hr {
  border: none !important;
  border-top: 1px solid var(--slate-200) !important;
  margin: 1.5rem 0 !important;
}

/* --- Dataframe --- */
.stDataFrame {
  border: 1px solid var(--slate-200) !important;
  border-radius: 10px !important;
  overflow: hidden;
}

/* --- Footer --- */
.sus-footer {
  margin-top: 3rem;
  padding: 1.25rem 0;
  border-top: 1px solid var(--slate-200);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.sus-footer-left {
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--slate-400);
  text-transform: uppercase;
  letter-spacing: 0.12em;
}
.sus-footer-right {
  font-size: 0.65rem;
  color: var(--slate-400);
}

/* --- Animacao fade-in --- */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* --- Scrollbar fina --- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background-color: var(--slate-200); border-radius: 3px; }

/* esconde elementos Streamlit desnecessarios */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
"""

_HEADER_HTML = """
<div class="sus-header">
  <div class="sus-header-icon">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
         stroke-linecap="round" stroke-linejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>
  </div>
  <div>
    <div class="sus-header-title">
      Saúde <span style="color:#94a3b8;font-weight:400">·</span> {subtitle}
    </div>
    <div class="sus-header-sub">Vigilância Epidemiológica · DATASUS</div>
  </div>
</div>
"""

_FOOTER_HTML = """
<div class="sus-footer">
  <span class="sus-footer-left">Saúde · {label} · dados públicos SUS</span>
  <span class="sus-footer-right">InfoDengue · SIM/DATASUS · SNIS · IBGE</span>
</div>
"""

_FAVICON_LINK = (
    '<link rel="shortcut icon" href="data:image/svg+xml,'
    "%3Csvg%20xmlns%3D'http%3A//www.w3.org/2000/svg'%20viewBox%3D'0%200%2032%2032'%3E"
    "%3Crect%20width%3D'32'%20height%3D'32'%20rx%3D'6'%20fill%3D'%230047bb'/%3E"
    "%3Cpolyline%20points%3D'3%2C16%208%2C16%2011%2C8%2014%2C24%2017%2C12%2020%2C20%2023%2C16%2029%2C16'"
    "%20fill%3D'none'%20stroke%3D'white'%20stroke-width%3D'2.5'"
    "%20stroke-linecap%3D'round'%20stroke-linejoin%3D'round'/%3E%3C/svg%3E"
    '">'
)


def inject(subtitle: str = "Outbreak Prediction", footer_label: str = "V1.0") -> None:
    """Injeta CSS, favicon e renderiza header do design system."""
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)
    st.markdown(_FAVICON_LINK, unsafe_allow_html=True)
    st.markdown(_HEADER_HTML.format(subtitle=subtitle), unsafe_allow_html=True)


def sidebar_back() -> None:
    """Renderiza link 'Inicio' no topo da sidebar das sub-paginas."""
    st.markdown(
        '<div class="sus-back-link">'
        '<a href="/" target="_self">&#8592; Início</a>'
        "</div>",
        unsafe_allow_html=True,
    )


def module_card(icon: str, name: str, desc: str, source: str) -> None:
    """Renderiza card de modulo (sem botao - use st.page_link abaixo)."""
    st.markdown(
        f"""<div class="sus-module-card">
  <div class="sus-module-header">
    <div class="sus-module-icon">
      <span class="material-symbols-outlined">{icon}</span>
    </div>
    <span class="sus-module-source">{source}</span>
  </div>
  <div class="sus-module-name">{name}</div>
  <div class="sus-module-desc">{desc}</div>
</div>""",
        unsafe_allow_html=True,
    )


def footer(label: str = "V1.0") -> None:
    st.markdown(_FOOTER_HTML.format(label=label), unsafe_allow_html=True)


def card(content_html: str, title: str = "") -> None:
    title_html = f'<div class="sus-card-title">{title}</div>' if title else ""
    st.markdown(f'<div class="sus-card">{title_html}{content_html}</div>', unsafe_allow_html=True)


def badge(text: str) -> None:
    st.markdown(f'<div class="sus-badge">{text}</div>', unsafe_allow_html=True)
