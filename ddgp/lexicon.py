# -*- coding: utf-8 -*-
"""
Módulo lexicon.py
Carrega o léxico DDGP 3.x a partir do arquivo JSON local
e fornece uma função de lookup sem diacríticos e com sugestões fuzzy.
"""

import json
import os

from .utils import normalize_unicode, remove_diacritics, simplify, fuzzy_suggestions

# Caminho padrão do arquivo JSON lexical
LEXICON_PATH = os.path.join(
    os.path.dirname(__file__), "data", "ddgp3x_entry.json"
)


# ------------------------------------------------------------
# Carregamento do léxico
# ------------------------------------------------------------

def load_lexicon(path: str = LEXICON_PATH) -> list:
    """
    Carrega o arquivo ddgp3x_entry.json e retorna uma lista de entradas.
    Cada entrada deve ser um dicionário.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Arquivo léxico não encontrado em: {path}\n"
            "Certifique-se de colocar ddgp3x_entry.json em ddgp/data/"
        )

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("O léxico deve ser uma lista de entradas JSON.")

    return data


# Cache simples em memória
_LEXICON = None


def get_lexicon():
    global _LEXICON
    if _LEXICON is None:
        _LEXICON = load_lexicon()
    return _LEXICON


# ------------------------------------------------------------
# Função principal de consulta
# ------------------------------------------------------------

def lookup_lexicon(word: str) -> list:
    """
    Procura uma palavra no léxico DDGP 3.x.

    Fluxo:
    - normaliza (NFC)
    - remove diacríticos
    - tenta match em `lemma`
    - tenta match em `forms`
    - retorna todas as entradas que combinem

    Se nada for encontrado, retorna [] e pode sugerir candidatos via fuzzy_suggestions.
    """
    if not word or not isinstance(word, str):
        return []

    lex = get_lexicon()

    w_norm = normalize_unicode(word)
    w_simp = simplify(w_norm)  # lower + remove diacríticos

    matches = []

    for entry in lex:
        # Cada entrada deve ser dict; se não for, ignora
        if not isinstance(entry, dict):
            continue

        # -----------------------------
        # 1. Tentativa de match por lemma
        # -----------------------------
        lemma = entry.get("lemma", "")
        if isinstance(lemma, str):
            if simplify(lemma) == w_simp:
                matches.append(entry)
                continue

        # -----------------------------
        # 2. Tentativa por forms
        # -----------------------------
        forms = entry.get("forms", [])
        if isinstance(forms, list):
            for form in forms:
                if isinstance(form, str) and simplify(form) == w_simp:
                    matches.append(entry)
                    break

    return matches


# ------------------------------------------------------------
# Sugestões quando nada é encontrado
# ------------------------------------------------------------

def suggest_similar(word: str, max_items=5) -> list:
    """
    Sugere palavras semelhantes baseadas em distancia Levenshtein
    nos lemas do léxico.
    """
    lex = get_lexicon()
    lemmas = [entry.get("lemma", "") for entry in lex if isinstance(entry, dict)]
    return fuzzy_suggestions(word, lemmas, max_suggestions=max_items)
