import streamlit as st
import os

# Configuration de la page
st.set_page_config(page_title="Accueil Hozana Tools", layout="wide")

# Style harmonisé
st.markdown("""
    <style>
        html, body {
            font-family: 'Segoe UI', sans-serif;
        }
        .block-container {
            padding-top: 2rem;
        }
        .title {
            font-size: 2.4rem;
            font-weight: 700;
            margin-bottom: 1.5rem;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }
        .tool-card {
            padding: 1.5rem;
            border-radius: 1rem;
            background-color: #f4f4f4;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            margin-bottom: 1.25rem;
        }
        .stButton>button {
            width: 100%;
            padding: 0.75rem;
            font-weight: 600;
            font-size: 1rem;
            color: white;
            background-color: #3366cc;
            border-radius: 0.5rem;
            border: none;
        }
        .stButton>button:hover {
            background-color: #254e9b;
        }
    </style>
""", unsafe_allow_html=True)

# Titre
st.markdown('<div class="title">Outils Hozana</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Bienvenue sur la plateforme interne des outils Hozana. Choisissez un module à ouvrir :</div>', unsafe_allow_html=True)

# Dictionnaire des modules
modules = {
    "Traduction multilingue d’articles": "1_Traduction_articles",
    "Publication d’articles traduits": "2_Publication_articles",
    # Ajouter d'autres outils ici
}

# Interface
for label, page_script in modules.items():
    with st.container():
        st.markdown(f'<div class="tool-card"><strong>{label}</strong><br><br>', unsafe_allow_html=True)
        if st.button(f"Ouvrir le module : {label}", key=label):
            st.switch_page(f"pages/{page_script}.py")
        st.markdown('</div>', unsafe_allow_html=True)
