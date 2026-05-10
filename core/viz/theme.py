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

/* --- Cards --- */
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

/* --- Sidebar --- */
[data-testid="stSidebar"] {
  background-color: #ffffff !important;
  border-right: 1px solid var(--slate-200) !important;
}
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
      Saude <span style="color:#94a3b8;font-weight:400">·</span> {subtitle}
    </div>
    <div class="sus-header-sub">Vigilancia Epidemiologica · DATASUS</div>
  </div>
</div>
"""

_FOOTER_HTML = """
<div class="sus-footer">
  <span class="sus-footer-left">Saude · {label} · dados publicos SUS</span>
  <span class="sus-footer-right">InfoDengue · SIM/DATASUS · SNIS · IBGE</span>
</div>
"""


def inject(subtitle: str = "Outbreak Prediction", footer_label: str = "V1.0") -> None:
    """Injeta CSS e renderiza header/footer do design system."""
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)
    st.markdown(_HEADER_HTML.format(subtitle=subtitle), unsafe_allow_html=True)


def footer(label: str = "V1.0") -> None:
    st.markdown(_FOOTER_HTML.format(label=label), unsafe_allow_html=True)


def card(content_html: str, title: str = "") -> None:
    title_html = f'<div class="sus-card-title">{title}</div>' if title else ""
    st.markdown(f'<div class="sus-card">{title_html}{content_html}</div>', unsafe_allow_html=True)


def badge(text: str) -> None:
    st.markdown(f'<div class="sus-badge">-- {text}</div>', unsafe_allow_html=True)
