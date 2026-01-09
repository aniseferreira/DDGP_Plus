import streamlit as st

# ============================================================
# Configuração da página
# ============================================================

st.set_page_config(
    page_title="DDGP Plus",
    layout="wide"
)

st.title("DDGP Plus")
st.caption("Análise morfológica em contexto e consulta lexical independente")

# ============================================================
# Utilidades
# ============================================================

def normalize_input(text: str) -> str:
    """
    Normalização mínima:
    - remove espaços laterais
    - converte para minúsculas
    """
    return text.strip().lower()


# ============================================================
# BLOCO B — Morfologia (WIC, auxiliar)
# ============================================================

def extract_morph_features_from_context(sentence: str):
    """
    Extração de lema e feições morfológicas a partir de FRASE (WIC).

    Espera-se integração com pipeline UD / Morph_Raw.

    Retorno esperado (exemplo):
    {
        "token": "λύει",
        "upos": "VERB",
        "lemma": "λυω",
        "features": {
            "Tense": "Pres",
            "Mood": "Ind",
            "Voice": "Act",
            "Person": "3",
            "Number": "Sing"
        }
    }
    """
    # TODO: integrar pipeline UD real
    return None


# ============================================================
# Tradução UD → Português filológico
# ============================================================

def translate_features(analysis: dict):
    labels = {
        "upos": {
            "NOUN": "substantivo",
            "VERB": "verbo",
            "ADJ": "adjetivo",
            "PRON": "pronome",
            "ADV": "advérbio",
            "NUM": "numeral"
        },
        "Case": {
            "Nom": "nominativo",
            "Gen": "genitivo",
            "Dat": "dativo",
            "Acc": "acusativo",
            "Voc": "vocativo"
        },
        "Number": {
            "Sing": "singular",
            "Plur": "plural",
            "Dual": "dual"
        },
        "Gender": {
            "Masc": "masculino",
            "Fem": "feminino",
            "Neut": "neutro"
        },
        "Tense": {
            "Pres": "presente",
            "Imp": "imperfeito",
            "Fut": "futuro",
            "Aor": "aoristo",
            "Perf": "perfeito",
            "Pqp": "mais-que-perfeito"
        },
        "Mood": {
            "Ind": "indicativo",
            "Sub": "subjuntivo",
            "Opt": "optativo",
            "Imp": "imperativo",
            "Inf": "infinitivo",
            "Part": "particípio"
        },
        "Voice": {
            "Act": "ativa",
            "Mid": "média",
            "Pass": "passiva"
        }
    }

    output = {}

    if "upos" in analysis:
        output["Classe"] = labels["upos"].get(
            analysis["upos"], analysis["upos"]
        )

    for feat, value in analysis.get("features", {}).items():
        if feat in labels:
            output[feat] = labels[feat].get(value, value)
        else:
            output[feat] = value

    return output


# ============================================================
# BLOCO A — Consulta ao DDGP (núcleo)
# ============================================================

def lookup_ddgp(query: str):
    """
    Consulta ao DDGP (independente da morfologia).

    Retorno esperado:
    [
        {
            "lemma_display": "λύω",
            "pos": "verbo",
            "entry_html": "<b>λύω</b> ... verbete completo ..."
        }
    ]
    """
    # TODO: integrar backend real do DDGP
    return []


# ============================================================
# Interface — ORDEM: MORFOLOGIA → DDGP
# ============================================================

st.header("🧩 Análise morfológica em contexto (WIC)")

wic_sentence = st.text_input(
    "Insira uma frase curta contendo o vocábulo:",
    placeholder="ex.: λύει τὸν δεσμόν"
)

st.caption(
    "A análise morfológica depende do contexto fornecido."
)

st.divider()

st.header("📘 Consulta ao DDGP")

ddgp_query = st.text_input(
    "Forma a consultar no dicionário:",
    placeholder="ex.: λύω, λυ, παθ"
)

st.divider()

# ============================================================
# Resultados
# ============================================================

col_morph, col_ddgp = st.columns(2)

# ----------------------------
# MORFOLOGIA
# ----------------------------
with col_morph:
    st.subheader("🧩 Resultado morfológico")

    if wic_sentence:
        try:
            analysis = extract_morph_features_from_context(wic_sentence)
        except Exception:
            analysis = None

        if not analysis:
            st.caption("Análise morfológica indisponível ou inconclusiva.")
        else:
            if "token" in analysis:
                st.write(f"**Forma analisada:** {analysis['token']}")

            translated = translate_features(analysis)
            for key, value in translated.items():
                st.write(f"**{key}:** {value}")

            if "lemma" in analysis:
                st.caption(f"Lema candidato: {analysis['lemma']}")
    else:
        st.caption("Digite uma frase para análise morfológica.")

# ----------------------------
# DDGP
# ----------------------------
with col_ddgp:
    st.subheader("📘 Resultados do DDGP")

    if ddgp_query:
        norm_ddgp = normalize_input(ddgp_query)
        


