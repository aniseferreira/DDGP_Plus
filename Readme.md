📘 DDGP_Plus — Morfologia & Léxico para Grego Antigo (DDGP 3.x)

DDGP_Plus é uma aplicação em Streamlit para consulta morfossintática simples e lookup lexical utilizando o léxico DDGP 3.x (ddgp3x_entry.json).

O objetivo é fornecer uma interface leve, rápida e prática para:

-  buscar lemas e formas flexionadas

-  analisar palavras com ou sem diacríticos

-  realizar consultas sem dependências pesadas (sem Stanza)

-  exibir resultados estruturados em JSON

🚀 Funcionalidades

📝 Entrada de uma única palavra em grego antigo

🔤 Normalização Unicode (NFC)

🔎 Análise morfológica simples, baseada em heurísticas:

- lema aproximado

- categoria provável

- sufixo reconhecido

📚 Consulta ao léxico DDGP 3.x

- busca por lemma

- busca por formas flexionadas

- busca sem diacríticos

💡 Sugestões aproximadas (fuzzy) quando nada é encontrado

💻 Interface totalmente baseada em Streamlit
 
DDGP_plus/
│── app.py
│── README.md
│── requirements.txt
│── .gitignore
│
│── ddgp/
│    ├── __init__.py
│    ├── utils.py
│    ├── morph.py
│    ├── lexicon.py
│    └── data/
│         └── ddgp3x_entry.json   ← arquivo lexical DDGP 3.x
│
└── tests/
     ├── test_morph.py
     └── test_lexicon.py `

