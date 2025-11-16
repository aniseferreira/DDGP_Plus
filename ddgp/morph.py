# -*- coding: utf-8 -*-
"""
DDGP Plus — módulo morfológico leve
------------------------------------
Objetivo:
- Normalizar forma
- Remover diacríticos
- Detectar tempo verbal e pessoa com heurísticas simples
- Estimar lema a partir de sufixos típicos
- Retornar JSON amigável para o app
"""

import unicodedata
from ddgp.lexicon import lookup_lemma, simplify


# ---------------------------------------------------------
# Utilitários
# ---------------------------------------------------------

def normalize(s: str) -> str:
    return unicodedata.normalize("NFC", s or "").strip()

def strip_diacritics(s: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", s)
        if not unicodedata.combining(ch)
    )

def simplify_greek(s: str) -> str:
    return strip_diacritics(normalize(s)).lower()


# ---------------------------------------------------------
# Regras leves para verbos gregos
# ---------------------------------------------------------

# Futuros típicos: -σω, -σομαι, -σετε, -σομεν ...
FUTURE_SUFFIXES = [
    "σω", "σομαι", "σεις", "σει", "σομεν", "σετε", "σουσι",
    "σονται", "σουμεν", "σεων"
]

# Aoristos sigmáticos: -σα, -σας, -σε, -σαμεν, -σατε, -σαν
AORIST_SUFFIXES = [
    "σα", "σας", "σε", "σαμεν", "σατε", "σαν"
]

# Perfeito: presença de reduplicação ou -κα
PERFECT_SUFFIXES = ["κα", "κας", "κε", "καμεν", "κατε", "κασι"]

# Presente típico: terminações finais comuns
PRESENT_SUFFIXES = [
    "ω", "εις", "ει", "ομεν", "ετε", "ουσι",
    "ομαι", "ῃ", "εται", "ομεθα", "εσθε", "ονται"
]

# Pessoas e número
PERSON_NUMBER = {
    "ω":           ("1", "sg"),
    "ομεν":        ("1", "pl"),
    "μεν":         ("1", "pl"),
    "εις":         ("2", "sg"),
    "ετε":         ("2", "pl"),
    "ει":          ("3", "sg"),
    "ουσι":        ("3", "pl"),
    "ονται":       ("3", "pl")
}


def guess_verb_analysis(word_s: str):
    """Heurísticas simples para analisar verbos."""

    # 1) Futuro
    for suf in sorted(FUTURE_SUFFIXES, key=len, reverse=True):
        if word_s.endswith(suf):
            return {
                "pos": "verb",
                "tense": "future",
                "voice": "active",
                "person_number": PERSON_NUMBER.get(suf, None),
                "stem": word_s[:-len(suf)] if len(word_s) > len(suf) else word_s
            }

    # 2) Aoristo
    for suf in sorted(AORIST_SUFFIXES, key=len, reverse=True):
        if word_s.endswith(suf):
            return {
                "pos": "verb",
                "tense": "aorist",
                "voice": "active",
                "person_number": PERSON_NUMBER.get(suf, None),
                "stem": word_s[:-len(suf)]
            }

    # 3) Perfeito
    for suf in sorted(PERFECT_SUFFIXES, key=len, reverse=True):
        if word_s.endswith(suf):
            return {
                "pos": "verb",
                "tense": "perfect",
                "voice": "active",
                "stem": word_s[:-len(suf)]
            }

    # 4) Presente
    for suf in sorted(PRESENT_SUFFIXES, key=len, reverse=True):
        if word_s.endswith(suf):
            return {
                "pos": "verb",
                "tense": "present",
                "voice": "active",
                "person_number": PERSON_NUMBER.get(suf, None),
                "stem": word_s[:-len(suf)]
            }

    return None


# ---------------------------------------------------------
# Estimativa de lema
# ---------------------------------------------------------

def guess_lemma_from_stem(stem: str):
    """
    Tenta reconstruir o lema verbal no infinitivo "ω".
    Ex: stem = 'βουλευ' → lema = 'βουλευω'
    """
    if not stem:
        return None

    lemma_candidate = stem + "ω"
    return lemma_candidate


# ---------------------------------------------------------
# Função principal
# ---------------------------------------------------------

def morph_analyze(word: str):
    """
    Análise morfológica leve.
    Retorna dict:
    {
        input: "",
        normalized: "",
        simplified: "",
        pos: "",
        tense: "",
        lemma: "",
        person: "",
        number: ""
    }
    """

    w_norm = normalize(word)
    w_s = simplify_greek(w_norm)

    result = {
        "input": word,
        "normalized": w_norm,
        "simplified": w_s,
        "pos": None,
        "tense": None,
        "lemma": None,
        "person": None,
        "number": None
    }

    # 1) Tenta análises verbais
    verb_info = guess_verb_analysis(w_s)
    if verb_info:
        result["pos"] = "verb"
        result["tense"] = verb_info.get("tense")

        stem = verb_info["stem"]
        lemma_candidate = guess_lemma_from_stem(stem)

        # 2) Verifica se o lema existe no dicionário
        if lemma_candidate:
            lemma_id = lookup_lemma(lemma_candidate)
            if lemma_id:
                result["lemma"] = lemma_candidate
            else:
                # fallback: assume lemma_candidate mesmo assim
                result["lemma"] = lemma_candidate

        pn = verb_info.get("person_number")
        if pn:
            result["person"], result["number"] = pn

        return result

    # 3) Se não é verbo, ainda tentamos lema literal
    lemma_direct = lookup_lemma(w_s)
    if lemma_direct:
        result["pos"] = "unknown"
        result["lemma"] = w_s
        return result

    return result
