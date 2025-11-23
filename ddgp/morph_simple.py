# ddgp/morph_simple.py
# -*- coding: utf-8 -*-
"""
Analisador Morfológico Simplificado para Grego Antigo.
Prioridade corrigida: Verbos antes de Nomes para resolver a ambiguidade de -ω.
"""

import os, json, unicodedata, re

# Define o caminho base
BASE_DIR = os.path.dirname(__file__)
MORPH_DATA_DIR = os.path.join(BASE_DIR, "data", "morph")

# --- Utilidades de Carregamento ---
def _load(name):
    """Carrega um arquivo JSON de dados morfológicos."""
    path = os.path.join(MORPH_DATA_DIR, name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    print(f"ATENÇÃO: Arquivo de dados não encontrado: {path}") 
    return {}

# --- Carregamento das Tabelas ---
PRES_A = _load("endings_present_active.json") or {}
PRES_M = _load("endings_present_middle.json") or {}
IMP_A  = _load("endings_imperfect_active.json") or {}
FUT_A  = _load("endings_future_active.json") or {}
FUT_M  = _load("endings_future_middle.json") or {}
FUT_P  = _load("endings_future_passive.json") or {}
A1_A   = _load("endings_aorist1_active.json") or {}
A1_M   = _load("endings_aorist1_middle.json") or {}
A1_P   = _load("endings_aorist1_passive.json") or {}
PERF_A = _load("endings_perfect_active.json") or {}
PERF_M = _load("endings_perfect_middle.json") or {}
PARTS  = _load("participles.json") or {}

DECL1 = _load("endings_decl1.json") or {}
DECL2 = _load("endings_decl2.json") or {}
DECL3 = _load("endings_decl3.json") or {}
ART   = _load("article.json") or {}
PRON  = _load("pronouns.json") or {}
NUM   = _load("numerals.json") or {}

# Mapeamento de Stems Irregulares
IRREGULAR_STEMS = _load("irregular_stems.json") or {}

# --- Dicionários de Tradução ---
POS_MAP    = {"verb":"verbo","noun":"substantivo","adj":"adjetivo","participle":"particípio","unknown":"desconhecido"}
TENSE_MAP  = {"present":"presente","future":"futuro","aorist":"aoristo","perfect":"perfeito","imperfect":"imperfeito",None:None}
VOICE_MAP  = {"active":"ativa","middle":"média","passive":"passiva",None:None}
CASE_MAP   = {"nom":"nominativo","gen":"genitivo","dat":"dativo","acc":"acusativo",None:None}
GENDER_MAP = {"masc":"masculino","fem":"feminino","neut":"neutro",None:None}
NUMBER_MAP = {"sg":"singular","pl":"plural",None:None}
PERSON_MAP = {"1":"1ª","2":"2ª","3":"3ª",None:None} 

# --- Funções de Utilidade ---
def normalize(t): return unicodedata.normalize("NFC", t or "").strip()
def strip_diacritics(t): return "".join(ch for ch in unicodedata.normalize("NFD", t or "") if not unicodedata.combining(ch))
def simplify(t): return strip_diacritics(normalize(t)).lower()

def match_longest(simpl, endings_dict):
    best = None
    for ending, info in endings_dict.items():
        end_s = simplify(ending)
        if end_s and simpl.endswith(end_s):
            if best is None or len(end_s) > len(best[0]):
                best = (end_s, info, ending)
    return best

def info_get(info, key):
    # Lógica para extrair informações de dicionários ou strings de código
    if isinstance(info, dict):
        return info.get(key)
    
    if isinstance(info, str):
        code = info
        
        if key == "tense":
            if "fut" in code: return "future"
            if "aor" in code: return "aorist"
            if "perf" in code: return "perfect"
            if "imp" in code: return "imperfect"
            if "pres" in code: return "present"
        
        if key == "voice":
            if "pass" in code: return "passive"
            if "mid" in code or "med" in code: return "middle"
            if "act" in code: return "active"
        
        if key == "person":
            m = re.search(r"([123])(?:sg|pl)", code)
            if m: return m.group(1)

        if key == "number":
            if "pl" in code: return "pl"
            if "sg" in code: return "sg"

    return None

# --- Funções de Reconstrução de Lema ---
def reconstruct_lemma_verb(stem): 
    """Tenta reconstruir o lema do presente para verbos regulares (stem + ω)."""
    # A reconstrução deve ser sem acento (strip_diacritics) para corresponder à chave do DDGP
    return strip_diacritics(stem) + "ω"

def reconstruct_lemma_nominal(stem, info=None):
    """Tenta reconstruir o lema para substantivos/adjetivos."""
    st = strip_diacritics(stem)
    # A reconstrução deve ser sem acento
    if isinstance(info, dict):
        g = info.get("gender")
        if g == "neut": return st + "ος" 
        if g == "fem":  return st + "η"
    return st + "ος" 

# --- Função Principal de Análise ---
def morph_analyze_simple(word):
    w = normalize(word)
    s = simplify(w)

    out = {
        "entrada": word, "normalizado": w, "simplificado": s,
        "pos": None, "tempo": None, "voz": None,
        "pessoa": None, "numero": None,
        "caso": None, "genero": None,
        "lema": None, "notas": []
    }

    if not s:
        return out

    # 1. Artigos / pronomes / numerais (Lookup exato)
    for d in (ART, PRON, NUM):
        for form, info in d.items():
            if simplify(form) == s:
                out["pos"]    = POS_MAP.get(info.get("pos","noun"))
                out["caso"]   = CASE_MAP.get(info.get("case"))
                out["genero"] = GENDER_MAP.get(info.get("gender"))
                out["numero"] = NUMBER_MAP.get(info.get("number"))
                out["lema"]   = info.get("lemma", form)
                out["notas"].append("lookup_exato")
                return out

    # 2. Particípio
    part = match_longest(s, PARTS)
    if part:
        end_s, info, original = part
        out["pos"] = "particípio"
        out["tempo"] = TENSE_MAP.get(info_get(info, "tense"))
        out["voz"]   = VOICE_MAP.get(info_get(info, "voice"))
        stem = s[:-len(end_s)] if end_s else s
        out["lema"] = reconstruct_lemma_nominal(stem) 
        out["notas"].append(f"participle_end:{original}")
        return out

    # 3. Verbos (PRIORIDADE ALTA: Corrigindo 'φερω' e outras formas verbais ambíguas)
    for pd in [PRES_A, PRES_M, IMP_A, FUT_M, FUT_A, FUT_P, A1_A, A1_M, A1_P, PERF_M, PERF_A]:
        m = match_longest(s, pd)
        if m:
            end_s, info, original = m
            out["pos"]    = "verbo"
            out["tempo"] = TENSE_MAP.get(info_get(info, "tense"))
            out["voz"]    = VOICE_MAP.get(info_get(info, "voice"))
            out["pessoa"] = PERSON_MAP.get(info_get(info, "person"))
            out["numero"] = NUMBER_MAP.get(info_get(info, "number"))
            
            # Cálculo do Stem
            stem = s[:-len(end_s)] if end_s else s
            stem_s = strip_diacritics(stem)
            
            # Lógica de lematização com CORREÇÃO para irregulares
            if stem_s in IRREGULAR_STEMS:
                out["lema"] = IRREGULAR_STEMS[stem_s]
                out["notas"].append(f"lema_override:{stem_s}->{out['lema']}")
            else:
                out["lema"] = reconstruct_lemma_verb(stem)
            
            out["notas"].append(f"verb_end:{original}")
            return out


    # 4. Nomes e adjetivos (PRIORIDADE BAIXA: Resolve 'παθη' após falhar como verbo)
    for nd in (DECL3, DECL2, DECL1): 
        m = match_longest(s, nd)
        if m:
            end_s, info, original = m
            out["pos"]    = "substantivo" 
            out["caso"]   = CASE_MAP.get(info.get("case"))
            out["genero"] = GENDER_MAP.get(info.get("gender"))
            out["numero"] = NUMBER_MAP.get(info.get("number"))
            
            # Reconstrução do lema nominal
            stem = s[:-len(end_s)] if end_s else s
            out["lema"] = reconstruct_lemma_nominal(stem, info)
            out["notas"].append(f"declension_end:{original}")
            return out

    # 5. Fallback para Desconhecido
    out["pos"] = "desconhecido"
    out["lema"] = strip_diacritics(s) 
    out["notas"].append("fallback")
    return out
