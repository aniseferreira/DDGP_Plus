import streamlit as st

# ============================================================
# Configuração da página
# ============================================================

st.set_page_config(
    page_title="DDGP Plus",
    layout="wide"
)

st.title("DDGP Plus")
st.caption("Consulta lexical independente com análise morfológica auxiliar")

# ============================================================
# Utilidades
# ============================================================

def normalize_input(text: str) -> str:
    """
    Normalização mínima:
    - remove espaços
    - converte para minúsculas
    - NÃO força diacríticos
    """
    return text.strip().lower()


# ============================================================
# BLOCO A — Consulta ao DDGP (núcleo)
# ============================================================

def lookup_ddgp(query: str):
    """
    Consulta ao DDGP.

    REQUISITOS:
    - aceitar forma flexionada ou truncada
    - nunca lançar exceção fatal
    - retornar lista (possivelmente vazia)

    Estrutura esperada:
    [
        {
            "lemma_display": "λύω",
            "pos": "verbo",
            "entry_html": "<b>λύω</b> ... verbete completo ..."
        },
        {
            "lemma_display": "λύσις, -εως",
            "pos": "substantivo",
            "entry_html": "<b>λύσις</b> ... verbete completo ..."
        }
    ]
    """
    # TODO: substituir pela consulta real ao DDGP
    return []


# ============================================================
# BLOCO B — Morfologia (auxiliar, independente)
# ============================================================

def extract_morph_features(word: str):
    """
    Extração de lema e feições morfológicas (UD / Morph_Raw).

    Retorno esperado (exemplo):
    {
        "upos": "VERB",
        "lemma": "λυω",
        "features": {
            "Tense": "Pres",
            "Mood": "Ind",
            "Voice": "Act",
            "Person": "1",
            "Number": "Sing"
        }
    }

    Pode retornar None ou dados parciais.
    """
    # TODO: integrar Morph_Raw / UD real
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
# Interface — DOIS CAMPOS DE CONSULTA
# ============================================================

st.header("Consulta")

col_input_ddgp, col_input_morph = st.columns(2)

with col_input_ddgp:
    query_ddgp = st.text_input(
        "📘 Consulta ao DDGP",
        placeholder="Forma completa ou truncada (ex.: λύω, λυ, παθ)"
    )

with col_input_morph:
    query_morph = st.text_input(
        "🧩 Análise morfológica",
        placeholder="Forma a analisar (ex.: λύει, λόγου)"
    )

st.divider()

# ============================================================
# Resultados
# ============================================================

col_ddgp, col_morph = st.columns(2)

# ----------------------------
# BLOCO A — DDGP
# ----------------------------
with col_ddgp:
    st.subheader("📘 Resultados do DDGP")

    if query_ddgp:
        norm_ddgp = normalize_input(query_ddgp)
        try:
            entries = lookup_ddgp(norm_ddgp)
        except Exception:
            entries = []

        if not entries:
            st.info("Nenhum verbete encontrado.")
        else:
            for entry in entries:
                st.markdown(entry["entry_html"], unsafe_allow_html=True)
                st.divider()
    else:
        st.caption("Digite uma forma para consultar o DDGP.")

# ----------------------------
# BLOCO B — Morfologia
# ----------------------------
with col_morph:
    st.subheader("🧩 Análise morfológica (auxiliar)")

    if query_morph:
        norm_morph = normalize_input(query_morph)
        try:
            analysis = extract_morph_features(norm_morph)
        except Exception:
            analysis = None

        if not analysis:
            st.caption("Análise morfológica indisponível ou inconclusiva.")
        else:
            translated = translate_features(analysis)

            for key, value in translated.items():
                st.write(f"**{key}:** {value}")

            if "lemma" in analysis:
                st.caption(f"Lema candidato: {analysis['lemma']}")
    else:
        st.caption("Digite uma forma para análise morfológica.")
