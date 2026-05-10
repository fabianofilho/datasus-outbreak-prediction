"""ICD-10 chapter catalog with labels in Portuguese and colors."""

from __future__ import annotations

CHAPTERS = {
    "A": {"label": "Doencas infecciosas e parasitarias", "color": "#e6194b"},
    "B": {"label": "Doencas infecciosas e parasitarias", "color": "#e6194b"},
    "C": {"label": "Neoplasias", "color": "#3cb44b"},
    "D": {"label": "Neoplasias / Doencas do sangue", "color": "#4363d8"},
    "E": {"label": "Doencas endocrinas e metabolicas", "color": "#f58231"},
    "F": {"label": "Transtornos mentais", "color": "#911eb4"},
    "G": {"label": "Doencas do sistema nervoso", "color": "#42d4f4"},
    "H": {"label": "Doencas do olho e ouvido", "color": "#f032e6"},
    "I": {"label": "Doencas do aparelho circulatorio", "color": "#dc143c"},
    "J": {"label": "Doencas do aparelho respiratorio", "color": "#469990"},
    "K": {"label": "Doencas do aparelho digestivo", "color": "#9a6324"},
    "L": {"label": "Doencas da pele", "color": "#800000"},
    "M": {"label": "Doencas do sistema osteomuscular", "color": "#aaffc3"},
    "N": {"label": "Doencas do aparelho geniturinario", "color": "#ffd8b1"},
    "O": {"label": "Gravidez, parto e puerperio", "color": "#000075"},
    "P": {"label": "Afeccoes perinatais", "color": "#a9a9a9"},
    "Q": {"label": "Malformacoes congenitas", "color": "#ffe119"},
    "R": {"label": "Sintomas e sinais mal definidos", "color": "#bfef45"},
    "S": {"label": "Lesoes e causas externas", "color": "#fabebe"},
    "T": {"label": "Lesoes e causas externas", "color": "#fabebe"},
    "V": {"label": "Causas externas de morbidade", "color": "#e6beff"},
    "W": {"label": "Causas externas de morbidade", "color": "#e6beff"},
    "X": {"label": "Causas externas de morbidade", "color": "#e6beff"},
    "Y": {"label": "Causas externas de morbidade", "color": "#e6beff"},
    "Z": {"label": "Fatores que influenciam o estado de saude", "color": "#808000"},
    "U": {"label": "Codigos para propositos especiais", "color": "#cccccc"},
}


def chapter_letter(code: str) -> str:
    """Extract chapter letter from ICD-10 code."""
    if code and len(code) >= 1:
        return code[0].upper()
    return ""


def chapter_label(code: str) -> str:
    """Get Portuguese label for an ICD-10 code's chapter."""
    letter = chapter_letter(code)
    return CHAPTERS.get(letter, {}).get("label", "Desconhecido")


def chapter_color(code: str) -> str:
    """Get color hex for an ICD-10 code's chapter."""
    letter = chapter_letter(code)
    return CHAPTERS.get(letter, {}).get("color", "#999999")


def code_display(code: str) -> str:
    """Format code for display: 'I219' -> 'I21.9', 'J18' -> 'J18'."""
    code = code.upper()
    if len(code) == 4:
        return f"{code[:3]}.{code[3]}"
    return code
