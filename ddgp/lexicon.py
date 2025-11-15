# ddgp/lexicon.py
# -*- coding: utf-8 -*-
"""
Loader e lookup do léxico DDGP 3.x (versão tolerante).
- Se o arquivo não existir, retorna lista vazia e não trava o app.
- Exibe mensagens de erro controladas.
- Busca exata, sem diacríticos e em forms/lemma.
- Função suggest_similar para fallback.
"""

import json
import os
import logging

from .utils import normalize_unicode, remove_diacritics, simplify, fuzzy_suggestions

LOG = logging.getLogger(__name__)

LEXICON_PATH = os.path.join(os.path.dirname(__file__), "data", "ddgp3x_entry.json")

_LEXICON = None

def load_lexicon(path: str = LEXICON_PATH) -> list:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Lexicon file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected lexicon JSON to be a list of entries")
    return data

def get_lexicon():
    global _LEXICON
    if _LEXICON is None:
        try:
            _LEXICON = load_lexicon()
        except Exception as e:
            LOG.exception("Could not load lexicon")
            _LEXICON = []
    return _LEXICON

def lookup_lexicon(word: str) -> list:
    """
    Returns list of matching entries. If lexicon missing, returns [].
    """
    if not word or not isinstance(word, str):
        return []

    lex = get_lexicon()
    if not lex:
        # no lexicon loaded — return empty list
        return []

    w_norm = normalize_unicode(word)
    w_simp = simplify(w_norm)

    matches = []
    for entry in lex:
        if not isinstance(entry, dict):
            continue
        # check lemma
        lemma = entry.get("lemma", "")
        if isinstance(lemma, str) and simplify(lemma) == w_simp:
            matches.append(entry)
            continue
        # check forms
        forms = entry.get("forms", [])
        if isinstance(forms, list):
            for form in forms:
                if isinstance(form, str) and simplify(form) == w_simp:
                    matches.append(entry)
                    break
        # also, some lexica might have "orth" or "form" keys
        orth = entry.get("orth") or entry.get("form")
        if isinstance(orth, str) and simplify(orth) == w_simp:
            matches.append(entry)
            continue

    return matches

def suggest_similar(word: str, max_items=5) -> list:
    lex = get_lexicon()
    if not lex:
        return []
    lemmas = [entry.get("lemma", "") for entry in lex if isinstance(entry, dict)]
    return fuzzy_suggestions(word, lemmas, max_suggestions=max_items)
