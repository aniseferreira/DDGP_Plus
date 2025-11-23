
# ddgp/morph_simple.py — Morpheus-enabled wrapper with deterministic fallback
# -*- coding: utf-8 -*-
"""
Morph Simple (pt-BR) — versão híbrida.
- Tenta usar Morpheus / CLTK se disponível para reconhecer formas irregulares (recomendado).
- Se Morpheus não estiver disponível, usa o analisador determinístico por tabelas (fallback).
Esta versão preserva a interface `morph_analyze_simple(word)` usada pelo app.py.
"""

import os, json, unicodedata, re, sys
from pathlib import Path

BASE_DIR = os.path.dirname(__file__)
MORPH_DATA_DIR = os.path.join(BASE_DIR, "data", "morph")

def _load(name):
    path = os.path.join(MORPH_DATA_DIR, name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

# --- load tables (same as previous deterministic analyzer) ---
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

# maps
POS_MAP    = {"verb":"verbo","noun":"substantivo","adj":"adjetivo","participle":"particípio","unknown":"desconhecido"}
TENSE_MAP  = {"present":"presente","future":"futuro","aorist":"aoristo","perfect":"perfeito","imperfect":"imperfeito",None:None}
VOICE_MAP  = {"active":"ativa","middle":"média","passive":"passiva",None:None}
CASE_MAP   = {"nom":"nominativo","gen":"genitivo","dat":"dativo","acc":"acusativo",None:None}
GENDER_MAP = {"masc":"masculino","fem":"feminino","neut":"neutro",None:None}
NUMBER_MAP = {"sg":"singular","pl":"plural",None:None}
PERSON_MAP = {"1":"1ª","2":"2ª","3":"3ª",None:None}

# utils
def normalize(t): return unicodedata.normalize("NFC", (t or "")).strip()
def strip_diacritics(t): return "".join(ch for ch in unicodedata.normalize("NFD", (t or "")) if not unicodedata.combining(ch))
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

def reconstruct_lemma_verb(stem):   return strip_diacritics(stem) + "ω"
def reconstruct_lemma_nominal(stem, info=None):
    st = strip_diacritics(stem)
    if isinstance(info, dict):
        g = info.get("gender")
        if g == "neut": return st + "ον"
        if g == "fem":  return st + "α"
    return st + "ος"

# --- Deterministic analyzer copied from your previous file (used as fallback) ---
def deterministic_analyze(word):
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
    # Articles/pronouns/numerals
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
    # Participle
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
    # Verbs by table
    for pd in [FUT_M, FUT_A, FUT_P, A1_A, A1_M, A1_P, PERF_M, PERF_A, IMP_A, PRES_M, PRES_A]:
        m = match_longest(s, pd)
        if m:
            end_s, info, original = m
            out["pos"]   = "verbo"
            out["tempo"] = TENSE_MAP.get(info_get(info, "tense"))
            out["voz"]   = VOICE_MAP.get(info_get(info, "voice"))
            out["pessoa"] = PERSON_MAP.get(info_get(info, "person"))
            out["numero"] = NUMBER_MAP.get(info_get(info, "number"))
            stem = s[:-len(end_s)] if end_s else s
            out["lema"] = reconstruct_lemma_verb(stem)
            out["notas"].append(f"verb_end:{original}")
            return out
    # Nouns/adjectives
    for nd in (DECL2, DECL1, DECL3):
        m = match_longest(s, nd)
        if m:
            end_s, info, original = m
            out["pos"]    = "substantivo"
            out["caso"]   = CASE_MAP.get(info.get("case"))
            out["genero"] = GENDER_MAP.get(info.get("gender"))
            out["numero"] = NUMBER_MAP.get(info.get("number"))
            stem = s[:-len(end_s)] if end_s else s
            out["lema"] = reconstruct_lemma_nominal(stem, info)
            out["notas"].append(f"declension_end:{original}")
            return out
    out["pos"] = "desconhecido"
    out["lema"] = strip_diacritics(s)
    out["notas"].append("fallback")
    return out

# --- MORPHEUS/CLTK integration (best-effort) ---
MORPHEUS_AVAILABLE = False
_MORPHEUS = None
_MORPHEUS_NAME = None

# Try a few import patterns for CLTK / Morpheus wrappers
_import_errors = []
try:
    # CLTK new-style NLP (v1+) might provide a pipeline with lemmatizer; try to import NLP
    from cltk import NLP
    try:
        _nlp = NLP(language="grc")
        # Some CLTK versions require pipeline initialization; we will rely on cltk to lazily download models if needed.
        MORPHEUS_AVAILABLE = True
        _MORPHEUS = _nlp
        _MORPHEUS_NAME = "cltk.NLP"
    except Exception as e:
        _import_errors.append(("cltk.NLP", str(e)))
except Exception as e:
    _import_errors.append(("cltk.NLP-import", str(e)))

# Try older Morpheus wrappers (community variants)
if not MORPHEUS_AVAILABLE:
    try:
        from cltk.morphology.morpheus import Morpheus
        _MORPHEUS = Morpheus()
        MORPHEUS_AVAILABLE = True
        _MORPHEUS_NAME = "cltk.morphology.morpheus.Morpheus"
    except Exception as e:
        _import_errors.append(("cltk.morphology.morpheus", str(e)))

# Generic Perseus Morpheus python wrapper (if installed separately)
if not MORPHEUS_AVAILABLE:
    try:
        from morpheus import Morpheus as PerseusMorpheus
        _MORPHEUS = PerseusMorpheus()
        MORPHEUS_AVAILABLE = True
        _MORPHEUS_NAME = "morpheus.Morpheus"
    except Exception as e:
        _import_errors.append(("morpheus", str(e)))

# Helper to parse morpheus outputs generically
def _parse_morpheus_output(raw):
    """
    Accepts several possible raw output formats and returns a normalized dict:
    {
      'entrada': original,
      'normalizado': normalized,
      'simplificado': simplified,
      'pos': 'verbo'|'substantivo'|...,
      'tempo': ...,
      'voz': ...,
      'pessoa': ...,
      'numero': ...,
      'caso': ...,
      'genero': ...,
      'lema': ...,
      'notas': [...]
    }
    This function implements heuristics for common Morpheus/CLTK outputs.
    """
    # default skeleton
    out = {
        "entrada": None, "normalizado": None, "simplificado": None,
        "pos": None, "tempo": None, "voz": None,
        "pessoa": None, "numero": None,
        "caso": None, "genero": None,
        "lema": None, "notas": []
    }

    if not raw:
        return out

    # If raw is a list of analyses, pick the first reasonable one
    if isinstance(raw, (list, tuple)) and raw:
        candidate = raw[0]
    else:
        candidate = raw

    # Candidate might be a dict-like object
    # Try to access common keys
    lemma = None
    pos = None
    features = {}
    if isinstance(candidate, dict):
        lemma = candidate.get("lemma") or candidate.get("lex") or candidate.get("stem")
        pos = candidate.get("pos") or candidate.get("partOfSpeech") or candidate.get("cat")
        features = candidate.get("analysis") or candidate.get("features") or candidate.get("tags") or {}
    elif isinstance(candidate, str):
        # example string formats exist; attempt to parse tokens
        # e.g. "τύχη, n, gen, sg, ... , lemma: τύχη"
        parts = [p.strip() for p in re.split(r"[;,]", candidate) if p.strip()]
        # find a token that looks like lemma (contains greek letters)
        for p in parts:
            if re.search(r"[\u0370-\u03FF]", p):
                lemma = lemma or p
        # try to infer pos from tokens
        for p in parts:
            lp = p.lower()
            if lp.startswith("n") or "noun" in lp: pos = pos or "noun"
            if lp.startswith("v") or "verb" in lp: pos = pos or "verb"
            if "aor" in lp or "pres" in lp or "perf" in lp: features.setdefault("tense", lp)
    # heuristics mapping
    out["lema"] = lemma
    out["pos"] = POS_MAP.get(pos, pos) if pos else None
    # map features if present
    tense = None
    voice = None
    person = None
    number = None
    case = None
    gender = None
    if isinstance(features, dict):
        # keys may vary; handle common names
        tense = features.get("tense") or features.get("TENSE") or features.get("t")
        voice = features.get("voice") or features.get("VOICE")
        person = features.get("person") or features.get("PERSON")
        number = features.get("number") or features.get("NUMBER")
        case = features.get("case") or features.get("CASE")
        gender = features.get("gender") or features.get("GENDER")
    elif isinstance(features, (list, tuple)):
        for f in features:
            if isinstance(f, str):
                lf = f.lower()
                if "aor" in lf: tense = "aorist"
                if "pres" in lf: tense = "present"
                if "perf" in lf: tense = "perfect"
                if "pass" in lf: voice = "passive"
                if "mid" in lf: voice = "middle"
                if "act" in lf: voice = "active"
                if "sg" in lf: number = "sg"
                if "pl" in lf: number = "pl"
    out["tempo"] = TENSE_MAP.get(tense, tense)
    out["voz"] = VOICE_MAP.get(voice, voice)
    out["pessoa"] = PERSON_MAP.get(str(person)) if person else None
    out["numero"] = NUMBER_MAP.get(number, number)
    out["caso"] = CASE_MAP.get(case, case)
    out["genero"] = GENDER_MAP.get(gender, gender)
    if out["lema"]:
        out["lema"] = strip_diacritics(out["lema"])
    out["notas"].append("morpheus" if MORPHEUS_AVAILABLE else "deterministic")
    return out

def morpheus_analyze(word):
    """
    Try to analyze using whatever Morpheus-like wrapper we found.
    The function returns a normalized dict or None on failure.
    """
    w = normalize(word)
    if not w:
        return None
    if not MORPHEUS_AVAILABLE or _MORPHEUS is None:
        return None
    try:
        # CLTK NLP object: try to create a pipeline tokenization/lemmatization call
        if _MORPHEUS_NAME == "cltk.NLP":
            # Use a small pipeline to analyze single token
            try:
                doc = _MORPHEUS.pipeline(text=w, steps=["tokenize","lemmatize","pos"])
            except Exception:
                # different CLTK versions use .pipeline as method of NLP
                doc = _MORPHEUS.pipeline(text=w)
            # doc.tokens or doc['tokens'] may be present
            analyses = []
            # navigate doc structure heuristically
            tokens = None
            if hasattr(doc, "tokens"):
                tokens = doc.tokens
            elif isinstance(doc, dict) and "tokens" in doc:
                tokens = doc["tokens"]
            if tokens:
                for t in tokens:
                    if t.get("text") and strip_diacritics(t.get("text")) == strip_diacritics(w):
                        # build a candidate dict
                        cand = {}
                        cand["lemma"] = t.get("lemma") or t.get("lemma_string') if isinstance(t.get('lemma'), str) else None
                        cand["pos"] = t.get("upos") or t.get("pos")
                        cand["features"] = t.get("feats") or t.get("features")
                        analyses.append(cand)
            # if nothing matched, fallback to doc's lemmatizer output
            if not analyses:
                # try simple lemmatize
                try:
                    lem = _MORPHEUS.lemmatize(w)
                    analyses = lem if isinstance(lem, (list,tuple)) else [lem]
                except Exception:
                    analyses = []
            return _parse_morpheus_output(analyses)
        else:
            # For other wrappers we attempt .analyze or .parse or .lemmatize
            if hasattr(_MORPHEUS, "analyze"):
                raw = _MORPHEUS.analyze(w)
            elif hasattr(_MORPHEUS, "parse"):
                raw = _MORPHEUS.parse(w)
            elif hasattr(_MORPHEUS, "lemmatize"):
                raw = _MORPHEUS.lemmatize(w)
            else:
                raw = None
            return _parse_morpheus_output(raw)
    except Exception as e:
        # don't raise; let fallback handle it
        return None

# --- Public API: morph_analyze_simple uses morpheus first, then deterministic fallback ---
def morph_analyze_simple(word):
    # Try morpheus first
    res = None
    try:
        res = morpheus_analyze(word)
    except Exception:
        res = None
    if res:
        # Ensure "entrada", "normalizado", "simplificado" set
        res["entrada"] = res.get("entrada") or word
        res["normalizado"] = res.get("normalizado") or normalize(word)
        res["simplificado"] = res.get("simplificado") or simplify(res.get("normalizado") or word)
        return res
    # Fallback deterministic
    return deterministic_analyze(word)
