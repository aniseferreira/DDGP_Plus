# ddgp/morph.py — Enhanced morphological analyzer with noun/adjective recognition (Option B+)
# -*- coding: utf-8 -*-
"""
Comprehensive morphological analyzer for DDGP Plus (enhanced):
- Loads morph JSON paradigm data from ddgp/data/morph/
- Recognizes verb paradigms (as before) and also noun/adjective declensional endings
- Reconstructs candidate lemma for nouns/adjectives (nominative singular) using heuristic rules
- Returns dictionary with morphological features
"""

import os, json, unicodedata, re

BASE_DIR = os.path.dirname(__file__)
MORPH_DATA_DIR = os.path.join(BASE_DIR, "data", "morph")

def _load_json(name):
    path = os.path.join(MORPH_DATA_DIR, name)
    if not os.path.exists(path):
        # if file missing, return empty dict
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# load json tables if present (they may be simple mappings)
PRES_A = _load_json("endings_present_active.json")
PRES_M = _load_json("endings_present_middle.json")
IMP_A = _load_json("endings_imperfect_active.json")
FUT_A = _load_json("endings_future_active.json")
FUT_M = _load_json("endings_future_middle.json")
FUT_P = _load_json("endings_future_passive.json")
A1_A = _load_json("endings_aorist1_active.json")
A1_M = _load_json("endings_aorist1_middle.json")
A1_P = _load_json("endings_aorist1_passive.json")
PERF_A = _load_json("endings_perfect_active.json")
PERF_M = _load_json("endings_perfect_middle.json")
PARTS = _load_json("participles.json")
IRREG = _load_json("irregular_verbs.json")

# noun/adjective declension endings mapping: ending -> features
# We'll try to load if user provided file, else use built-in minimal table
DECL_FILE = os.path.join(MORPH_DATA_DIR, "declensions.json")
if os.path.exists(DECL_FILE):
    DECL = _load_json("declensions.json")
else:
    # Minimal declension table (common Classical endings) for nouns/adjectives (simplified)
    # keys are endings (in simplified form, without diacritics)
    DECL = {
        "ος": {"pos":"noun","case":"nom","number":"sg","gender":"masc"},
        "ου": {"pos":"noun","case":"gen","number":"sg","gender":"masc"},
        "ῳ": {"pos":"noun","case":"dat","number":"sg","gender":"masc"},
        "ον": {"pos":"noun","case":"acc","number":"sg","gender":"masc"},
        "οι": {"pos":"noun","case":"nom","number":"pl","gender":"masc"},
        "ων": {"pos":"noun","case":"gen","number":"pl","gender":"masc"},
        "οις": {"pos":"noun","case":"dat","number":"pl","gender":"masc"},
        "ους": {"pos":"noun","case":"acc","number":"pl","gender":"masc"},
        "α": {"pos":"noun","case":"nom","number":"sg","gender":"fem"},
        "ας": {"pos":"noun","case":"acc","number":"sg","gender":"fem"},
        "ης": {"pos":"noun","case":"nom","number":"sg","gender":"masc"},
        "ων_adj": {"pos":"adj","case":"gen","number":"pl","gender":"all"},
        # a few neuter patterns
        "ον_neut": {"pos":"noun","case":"nom","number":"sg","gender":"neut"},
        "α_neut": {"pos":"noun","case":"nom","number":"pl","gender":"neut"}
    }

def normalize(text):
    return unicodedata.normalize("NFC", text or "").strip()

def strip_diacritics(text):
    return "".join(ch for ch in unicodedata.normalize("NFD", text or "") if not unicodedata.combining(ch))

def simplify(text):
    return strip_diacritics(normalize(text)).lower()

# helper: match endings longest-first from a dict of endings
def match_endings_from_dict(simplified, endings_dict):
    matches = []
    for ending in sorted(endings_dict.keys(), key=len, reverse=True):
        end_s = simplify(ending)
        if simplified.endswith(end_s):
            info = dict(endings_dict[ending])
            info["_ending"] = ending
            info["_ending_s"] = end_s
            matches.append(info)
    return matches

# reconstruct noun/adjective lemma (nom. sg.) from stem + heuristic suffix
def reconstruct_nom_sg_from_stem(stem_s, match_info):
    # common heuristic: if match gen plural 'ων', lemma often ends with 'ος' (masculine)
    case = match_info.get("case")
    gender = match_info.get("gender")
    if case == "gen" and match_info.get("number") == "pl":
        if gender == "masc" or gender == "all" or gender is None:
            return stem_s + "ος"
        if gender == "neut":
            return stem_s + "ον"
    # gen sg 'ου' -> nominative often 'ος' or 'ης' depending; default to 'ος'
    if case == "gen" and match_info.get("number") == "sg":
        if gender == "masc" or gender is None:
            return stem_s + "ος"
    # accusative plural 'ους' -> nominative 'ος'
    if match_info.get("case") == "acc" and match_info.get("number") == "pl":
        return stem_s + "ος"
    # fallback: return stem + 'ος'
    return stem_s + "ος"

# Reconstruct verb lemma naive
def reconstruct_verb_lemma(stem_s):
    return stem_s + "ω"

# combine paradigms for verbs as earlier
VERB_PARADIGMS = [FUT_M, FUT_A, FUT_P, A1_A, A1_M, A1_P, PERF_M, PERF_A, IMP_A, PRES_M, PRES_A]

def morph_analyze(word):
    w = normalize(word)
    s = simplify(w)
    result = {"input": word, "normalized": w, "simplified": s, "pos": None, "tense": None, "mood": None, "voice": None, "person": None, "number": None, "case": None, "gender": None, "lemma": None, "notes": []}

    if not s:
        return result

    # 0. irregular verbs lookup
    for key, val in IRREG.items():
        if s.startswith(simplify(key)):
            result.update({"pos":"verb","lemma": val if isinstance(val,str) else val.get("lemma")})
            result["notes"].append("irregular")
            return result

    # 1. try noun/adjective declension matches (longest endings first)
    decl_matches = match_endings_from_dict(s, DECL)
    if decl_matches:
        best = decl_matches[0]
        result["pos"] = best.get("pos")
        result["case"] = best.get("case")
        result["number"] = best.get("number")
        result["gender"] = best.get("gender")
        # compute stem (remove ending)
        stem_s = s[:-len(best.get("_ending_s"))] if best.get("_ending_s") else s
        # reconstruct lemma (nominative singular heuristic)
        result["lemma"] = reconstruct_nom_sg_from_stem(stem_s, best)
        result["notes"].append("declension_matched:"+best.get("_ending"))
        return result

    # 2. participles
    part_cands = match_endings_from_dict(s, PARTS)
    if part_cands:
        best = part_cands[0]
        result.update({"pos":"participle","tense":best.get("tense"),"voice":best.get("voice")})
        stem_s = s[:-len(best.get("_ending_s"))] if best.get("_ending_s") else s
        result["lemma"] = reconstruct_verb_lemma(stem_s)
        result["notes"].append("participle_matched:"+best.get("_ending"))
        return result

    # 3. verbs: try paradigms in priority order
    for pd in VERB_PARADIGMS:
        cand = match_endings_from_dict(s, pd)
        if cand:
            best = cand[0]
            result["pos"] = "verb"
            result["tense"] = best.get("tense")
            result["voice"] = best.get("voice")
            # person/number if available
            if best.get("person"):
                result["person"] = best.get("person")
            if best.get("number"):
                result["number"] = best.get("number")
            stem_s = s[:-len(best.get("_ending_s"))] if best.get("_ending_s") else s
            result["lemma"] = reconstruct_verb_lemma(stem_s)
            result["notes"].append("verb_matched:"+best.get("_ending"))
            return result

    # 4. fallback: if looks Greek, propose stripped form as lemma
    if re.search(r'[\u0370-\u03FF\u1F00-\u1FFF]', s):
        result["lemma"] = strip_diacritics(s)
        result["pos"] = "unknown"
        result["notes"].append("fallback_lemma")
    return result
