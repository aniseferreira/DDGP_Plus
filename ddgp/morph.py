# ddgp/morph.py
# -*- coding: utf-8 -*-
"""
Analisador morfológico leve para grego antigo (versão ajustada).
Melhorias:
- tenta formas sem diacríticos como fallback
- tenta remoção de terminações comuns com simplificação
- retorna campos de diagnóstico para facilitar debug
"""
from .utils import normalize_unicode, remove_diacritics, simplify

# sufíxos comuns (mantidos)
NOUN_SUFFIXES = ["ος","ου","ον","οι","ους","οις","ῳ","α","ας","η","ης","ῃ"]
VERB_SUFFIXES = ["ω","εις","ει","ομεν","ετε","ουσι","ειν","ε","ον","ες","εν"]
ADJ_SUFFIXES = ["ος","η","ον","οι","αι","α"]

def guess_pos(word):
    w = normalize_unicode(word)
    # tenta sem diacríticos primeiro
    wn = remove_diacritics(w)
    for suf in VERB_SUFFIXES:
        if w.endswith(suf) or wn.endswith(suf):
            return "verb"
    for suf in NOUN_SUFFIXES:
        if w.endswith(suf) or wn.endswith(suf):
            return "noun"
    for suf in ADJ_SUFFIXES:
        if w.endswith(suf) or wn.endswith(suf):
            return "adjective"
    return "unknown"

def guess_lemma(word):
    w = normalize_unicode(word)
    wn = remove_diacritics(w)

    # Helper to try a list of suffixes and produce a candidate lemma
    def try_suffixes(suffixes, lemma_ending):
        for suf in sorted(suffixes, key=len, reverse=True):
            if w.endswith(suf):
                stem = w[:-len(suf)]
                if stem:
                    return stem + lemma_ending
            if wn.endswith(suf):
                stem = wn[:-len(suf)]
                if stem:
                    return stem + lemma_ending
        return None

    # 1) tentar verbo -> lema com ω
    cand = try_suffixes(VERB_SUFFIXES, "ω")
    if cand:
        return normalize_unicode(cand)

    # 2) tentar substantivo -> lema com ος
    cand = try_suffixes(NOUN_SUFFIXES, "ος")
    if cand:
        return normalize_unicode(cand)

    # 3) tentar adjetivo -> lema com ος
    cand = try_suffixes(ADJ_SUFFIXES, "ος")
    if cand:
        return normalize_unicode(cand)

    # 4) fallback: forma sem diacríticos (lower)
    return simplify(w)

def extract_suffix(word):
    w = normalize_unicode(word)
    wn = remove_diacritics(w)
    for suf in sorted(VERB_SUFFIXES, key=len, reverse=True):
        if w.endswith(suf) or wn.endswith(suf):
            return suf
    for suf in sorted(NOUN_SUFFIXES, key=len, reverse=True):
        if w.endswith(suf) or wn.endswith(suf):
            return suf
    for suf in sorted(ADJ_SUFFIXES, key=len, reverse=True):
        if w.endswith(suf) or wn.endswith(suf):
            return suf
    return None

def analyze_word(word: str) -> dict:
    if not isinstance(word, str) or not word.strip():
        return {}

    original = word
    normalized = normalize_unicode(word)
    no_diac = remove_diacritics(normalized)
    pos = guess_pos(normalized)
    lemma = guess_lemma(normalized)
    suffix = extract_suffix(normalized)

    return {
        "input": original,
        "normalized": normalized,
        "no_diacritics": no_diac,
        "pos_guess": pos,
        "lemma_guess": lemma,
        "suffix": suffix,
        "diagnostic": {
            "simplified_input": simplify(original),
        }
    }
