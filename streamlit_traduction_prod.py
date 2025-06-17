import streamlit as st
import os

# Configuration de la page
st.set_page_config(page_title="Accueil Hozana Tools", layout="wide")

# Style cohérent avec les autres outils
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
        .section-title {
            font-weight: 600;
            font-size: 1.1rem;
            margin-top: 2rem;
        }
        .tool-card {
            padding: 1.25rem;
            border-radius: 1rem;
            background-color: #f9f9f9;
            box-shadow: 0 1px 4px rgba(0,0,0,0.05);
            margin-bottom: 1rem;
        }
        .stButton>button {
            width: 100%;
            padding: 0.75rem;
            font-weight: bold;
            border-radius: 0.75rem;
        }
    </style>
""", unsafe_allow_html=True)

# Titre et sous-titre
st.markdown('<div class="title">🛠️ Outils Hozana</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Bienvenue sur la plateforme interne des outils Hozana.<br>Choisissez un module à ouvrir :</div>', unsafe_allow_html=True)

# Dictionnaire des modules
modules = {
    "🌍 Traduction multilingue d’articles": "1_Traduction_articles",
    "📝 Publication d’articles traduits": "2_Publication_articles",
    # Ajouter d'autres outils ici
}

# Interface
for label, page_script in modules.items():
    with st.container():
        st.markdown(f'<div class="tool-card"><strong>{label}</strong><br><br>', unsafe_allow_html=True)
        st.page_link(f"pages/{page_script}.py", label="🚀 Ouvrir ce module", icon="arrow-right-circle")
        st.markdown('</div>', unsafe_allow_html=True)
