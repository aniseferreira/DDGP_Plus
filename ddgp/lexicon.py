# ddgp/lexicon.py
# -*- coding: utf-8 -*-

import json
import os

from .utils import normalize_unicode, remove_diacritics, simplify, fuzzy_suggestions

LEXICON_PATH = os.path.join(os.path.dirname(__file__), "data", "ddgp3x_entry.json")

_LEXICON = None


# ------------------------------------------------------------
# Carregamento
# ------------------------------------------------------------
def load_lexicon(path=LEXICON_PATH):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def get_lexicon():
    global _LEXICON
    if _LEXICON is None:
        try:
            _LEXICON = load_lexicon()
        except:
            _LEXICON = []
    return _LEXICON


# ------------------------------------------------------------
# Limpeza de gword → lema puro
# ------------------------------------------------------------
def extract_clean_lemma(gword: str) -> str:
    """
    Extrai o LEMA do campo gword.
    - pega o primeiro elemento antes de vírgula
    - remove espaços extras
    - normaliza Unicode
    - remove diacríticos para comparação
    """
    if not isinstance(gword, str):
        return ""

    # exemplo: "Α, α (ἄλφα) (τό)"
    # lema = primeiro item antes da vírgula
    raw = gword.split(",")[0].strip()

    # normalizar
    raw = normalize_unicode(raw)

    return simplify(raw)  # remove diacríticos e põe em lower()


# ------------------------------------------------------------
# FUNÇÃO PRINCIPAL DE LOOKUP
# ------------------------------------------------------------
def lookup_lexicon(lemma: str):
    """
    Procura o LEMA no JSON DDGP.

    IMPORTANTE:
    - DDGP3x NÃO contém formas flexionadas.
    - A busca deve ser feita APENAS pelo lema.
    """
    lex = get_lexicon()
    if not lex:
        return []

    lemma_clean = simplify(lemma)

    matches = []

    for entry in lex:
        gword = entry.get("gword", "")
        gword_clean = extract_clean_lemma(gword)

        if gword_clean == lemma_clean:
            matches.append(entry)

    return matches


# ------------------------------------------------------------
# Sugestões fuzzy de lemas próximos
# ------------------------------------------------------------
def suggest_similar(lemma: str, max_items=5):
    lex = get_lexicon()
    if not lex:
        return []

    lemmas = [extract_clean_lemma(e.get("gword", "")) for e in lex]

    return fuzzy_suggestions(lemma, lemmas, max_suggestions=max_items)
