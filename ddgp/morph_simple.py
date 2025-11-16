# ddgp/morph_simple.py
# -*- coding: utf-8 -*-
"""
Morph Simple (pt-BR)
Versão simples, determinística e rápida do analisador morfológico.
- Carrega os paradigmas (JSON) em ddgp/data/morph/
- Reconhece formas verbais (tempos/vozes/pessoa/número)
  e nominais (caso/gênero/número) por correspondência de desinências.
- NÃO gera lista de candidatos — escolhe o melhor (maior sufixo que case).
- Retorna rótulos traduzidos para português (pt-BR), prontos para exibição no app.
"""

import os, json, unicodedata, re

BASE_DIR = os.path.dirname(__file__)
MORPH_DATA_DIR = os.path.join(BASE_DIR, "data", "morph")

def _load(name):
    path = os.path.join(MORPH_DATA_DIR, name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# Carregamento de paradigmas (esperados nos jsons)
PRES_A = _load("endings_present_active.json")
PRES_M = _load("endings_present_middle.json")
IMP_A  = _load("endings_imperfect_active.json")
FUT_A  = _load("endings_future_active.json")
FUT_M  = _load("endings_future_middle.json")
FUT_P  = _load("endings_future_passive.json")
A1_A   = _load("endings_aorist1_active.json")
A1_M   = _load("endings_aorist1_middle.json")
A1_P   = _load("endings_aorist1_passive.json")
PERF_A = _load("endings_perfect_active.json")
PERF_M = _load("endings_perfect_middle.json")
PARTS  = _load("participles.json")

# Declinações nominais (devem existir)
DECL1 = _load("endings_decl1.json") or {}
DECL2 = _load("endings_decl2.json") or {}
DECL3 = _load("endings_decl3.json") or {}
ART   = _load("article.json") or {}
PRON  = _load("pronouns.json") or {}
NUM   = _load("numerals.json") or {}

# Mapas para tradução para pt-BR
POS_MAP = {"verb":"verbo","noun":"substantivo","adj":"adjetivo","participle":"particípio","unknown":"desconhecido"}
TENSE_MAP = {"present":"presente","future":"futuro","aorist":"aoristo","perfect":"perfeito","imperfect":"imperfeito", None: None}
VOICE_MAP = {"active":"ativa","middle":"média","passive":"passiva", None: None}
CASE_MAP = {"nom":"nominativo","gen":"genitivo","dat":"dativo","acc":"acusativo", None: None}
GENDER_MAP = {"masc":"masculino","fem":"feminino","neut":"neutro", None: None}
NUMBER_MAP = {"sg":"singular","pl":"plural", None: None}
PERSON_MAP = {"1":"1ª","2":"2ª","3":"3ª", None: None}

# utilitários
def normalize(text):
    return unicodedata.normalize("NFC", text or "").strip()

def strip_diacritics(text):
    return "".join(ch for ch in unicodedata.normalize("NFD", text or "") if not unicodedata.combining(ch))

def simplify(text):
    return strip_diacritics(normalize(text)).lower()

# match longest ending from dict
def match_longest(simpl, endings_dict):
    best = None
    for ending, info in endings_dict.items():
        end_s = simplify(ending)
        if end_s and simpl.endswith(end_s):
            if best is None or len(end_s) > len(best[0]):
                best = (end_s, info, ending)
    return best  # (ending_simplified, info, original_ending)

# principal função de análise (determinística)
def morph_analyze_simple(word):
    w = normalize(word)
    s = simplify(w)
    out = {
        "entrada": word,
        "normalizado": w,
        "simplificado": s,
        "pos": None,
        "tempo": None,
        "voz": None,
        "pessoa": None,
        "numero": None,
        "caso": None,
        "genero": None,
        "lema": None,
        "notas": []
    }

    if not s:
        return out

    # 0. artigos/pronomes/numerais (lookup exato)
    for d in (ART, PRON, NUM):
        for form, info in d.items():
            if simplify(form) == s:
                out["pos"] = POS_MAP.get(info.get("pos","noun"), "substantivo")
                out["caso"] = CASE_MAP.get(info.get("case"))
                out["genero"] = GENDER_MAP.get(info.get("gender"))
                out["numero"] = NUMBER_MAP.get(info.get("number"))
                out["lema"] = info.get("lemma", form)
                out["notas"].append("art/pron/num_exact")
                return out

    # 1. Particípio
    part = match_longest(s, PARTS)
    if part:
        end_s, info, orig = part
        out["pos"] = POS_MAP["participle"]
        out["tempo"] = TENSE_MAP.get(info.get("tense"))
        out["voz"] = VOICE_MAP.get(info.get("voice"))
        stem = s[:-len(end_s)] if end_s else s
        out["lema"] = reconstruct_lemma_nominal(stem, prefer_verb=True)
        out["notas"].append(f"participle_end:{orig}")
        return out

    # 2. Verbos: prioridade de paradigmas (futuros, aoristos, perfeito, imperfeito, presente)
    verb_parads = [FUT_M, FUT_A, FUT_P, A1_A, A1_M, A1_P, PERF_M, PERF_A, IMP_A, PRES_M, PRES_A]
    for pd in verb_parads:
        m = match_longest(s, pd)
        if m:
            end_s, info, orig = m
            out["pos"] = POS_MAP["verb"]
            # info may be dict or string: try to extract fields if dict
            if isinstance(info, dict):
                tempo = info.get("tense") or None
                out["tempo"] = TENSE_MAP.get(tempo, None) or (TENSE_MAP.get("future") if "fut" in info.get("code","") else None)
                out["voz"] = VOICE_MAP.get(info.get("voice"))
                out["pessoa"] = PERSON_MAP.get(str(info.get("person"))) if info.get("person") else None
                out["numero"] = NUMBER_MAP.get(info.get("number"))
            else:
                # if info is a code string like '1sg_fut_act', attempt parse
                code = str(info)
                if "fut" in code:
                    out["tempo"] = TENSE_MAP.get("future")
                elif "aor" in code:
                    out["tempo"] = TENSE_MAP.get("aorist")
                elif "perf" in code:
                    out["tempo"] = TENSE_MAP.get("perfect")
                elif "imp" in code:
                    out["tempo"] = TENSE_MAP.get("imperfect")
                elif "pres" in code:
                    out["tempo"] = TENSE_MAP.get("present")
                if "act" in code:
                    out["voz"] = VOICE_MAP.get("active")
                if "mid" in code or "med" in code:
                    out["voz"] = VOICE_MAP.get("middle")
                if "pass" in code:
                    out["voz"] = VOICE_MAP.get("passive")
                # person/number
                if "1sg" in code:
                    out["pessoa"] = PERSON_MAP["1"]; out["numero"]=NUMBER_MAP["sg"]
                elif "2sg" in code:
                    out["pessoa"] = PERSON_MAP["2"]; out["numero"]=NUMBER_MAP["sg"]
                elif "3sg" in code:
                    out["pessoa"] = PERSON_MAP["3"]; out["numero"]=NUMBER_MAP["sg"]
                elif "1pl" in code:
                    out["pessoa"] = PERSON_MAP["1"]; out["numero"]=NUMBER_MAP["pl"]
                elif "2pl" in code:
                    out["pessoa"] = PERSON_MAP["2"]; out["numero"]=NUMBER_MAP["pl"]
                elif "3pl" in code:
                    out["pessoa"] = PERSON_MAP["3"]; out["numero"]=NUMBER_MAP["pl"]

            # reconstruct lemma (stem + ω)
            stem = s[:-len(end_s)] if end_s else s
            out["lema"] = reconstruct_lemma_verb(stem)
            out["notas"].append(f"verb_end:{orig}")
            return out

    # 3. Nomes/adjetivos (declinações) – verificar as 3 declinações e adjetivos
    for nd in (DECL2, DECL1, DECL3):
        m = match_longest(s, nd)
        if m:
            end_s, info, orig = m
            out["pos"] = POS_MAP.get(info.get("pos","noun"))
            out["caso"] = CASE_MAP.get(info.get("case"))
            out["genero"] = GENDER_MAP.get(info.get("gender"))
            out["numero"] = NUMBER_MAP.get(info.get("number"))
            stem = s[:-len(end_s)] if end_s else s
            out["lema"] = reconstruct_lemma_nominal(stem, info)
            out["notas"].append(f"declension_end:{orig}")
            return out

    # 4. fallback: se contém caracteres gregos, devolve simplificado como lema
    if re.search(r'[\u0370-\u03FF\u1F00-\u1FFF]', s):
        out["pos"] = POS_MAP["unknown"]
        out["lema"] = strip_diacritics(s)
        out["notas"].append("fallback_lema")
    return out

# helpers to reconstruct lemmas
def reconstruct_lemma_verb(stem_s):
    # basic heuristic: stem + ω
    return strip_diacritics(stem_s) + "ω"

def reconstruct_lemma_nominal(stem_s, info=None, prefer_verb=False):
    # heuristic: prefer masculine -ος for many nouns; if info suggests neuter, use -ον; if feminine, -α
    st = strip_diacritics(stem_s)
    if prefer_verb:
        return st + "ω"
    if info and info.get("gender") == "neut":
        return st + "ον"
    if info and info.get("gender") == "fem":
        return st + "α"
    # default masculine nominative -ος
    return st + "ος"
