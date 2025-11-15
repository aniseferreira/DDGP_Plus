# -*- coding: utf-8 -*-
"""
Analisador morfológico leve para grego antigo.
- Não usa Stanza.
- Baseado em normalização e heurísticas simples.
- Útil para complementar o lookup lexical do DDGP.

Retorna um dicionário com:
- palavra original
- forma normalizada
- forma sem diacríticos
- possíveis sufixos reconhecidos
- possível lema (heurístico)
- categoria provável (POS)
"""

from .utils import normalize_unicode, remove_diacritics, simplify

# ------------------------------------------------------------
# Sufixos muito comuns (simplificado)
# ------------------------------------------------------------

NOUN_SUFFIXES = [
    "ος", "ου", "ον", "οι", "ους", "οις", "ῳ", "α", "ας", "η", "ης", "ῃ"
]

VERB_SUFFIXES = [
    "ω", "εις", "ει", "ομεν", "ετε", "ουσι", "ειν", "ε", "ον", "ες", "εν"
]

ADJ_SUFFIXES = [
    "ος", "η", "ον", "οι", "αι", "α"
]


# ------------------------------------------------------------
# Funções de reconhecimento simples
# ------------------------------------------------------------

def guess_pos(word):
    """
    Heurística simples de categoria gramatical.
    """
    w = normalize_unicode(word)

    for suf in VERB_SUFFIXES:
        if w.endswith(suf):
            return "verb"

    for suf in NOUN_SUFFIXES:
        if w.endswith(suf):
            return "noun"

    for suf in ADJ_SUFFIXES:
        if w.endswith(suf):
            return "adjective"

    return "unknown"


def guess_lemma(word):
    """
    Heurística ultra simples para lemma:
    - remove sufixos comuns
    - retorna forma mais curta possível
    """
    w = normalize_unicode(word)

    # Tenta verbos primeiro
    for suf in sorted(VERB_SUFFIXES, key=len, reverse=True):
        if w.endswith(suf):
            stem = w[: -len(suf)]
            if stem:
                return stem + "ω"   # lema verbal típico
            return w

    # Tenta substantivos
    for suf in sorted(NOUN_SUFFIXES, key=len, reverse=True):
        if w.endswith(suf):
            stem = w[: -len(suf)]
            if stem:
                return stem + "ος"  # lema nominal típico
            return w

    # Tenta adjetivos
    for suf in sorted(ADJ_SUFFIXES, key=len, reverse=True):
        if w.endswith(suf):
            stem = w[: -len(suf)]
            if stem:
                return stem + "ος"
            return w

    return w  # fallback: lema = palavra


def extract_suffix(word):
    """
    Retorna o sufixo mais provável.
    """
    w = normalize_unicode(word)

    for suf in sorted(VERB_SUFFIXES, key=len, reverse=True):
        if w.endswith(suf):
            return suf

    for suf in sorted(NOUN_SUFFIXES, key=len, reverse=True):
        if w.endswith(suf):
            return suf

    for suf in sorted(ADJ_SUFFIXES, key=len, reverse=True):
        if w.endswith(suf):
            return suf

    return None


# ------------------------------------------------------------
# Função principal
# ------------------------------------------------------------

def analyze_word(word: str) -> dict:
    """
    Analisa uma palavra em grego antigo e retorna
    um dicionário com os dados encontrados.
    """
    if not isinstance(word, str) or not word.strip():
        return {}

    original = word
    normalized = normalize_unicode(word)
    nodiac = remove_diacritics(normalized)

    pos = guess_pos(normalized)
    lemma = guess_lemma(normalized)
    suf = extract_suffix(normalized)

    return {
        "input": original,
        "normalized": normalized,
        "no_diacritics": nodiac,
        "pos_guess": pos,
        "lemma_guess": lemma,
        "suffix": suf,
    }
