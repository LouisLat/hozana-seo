import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Accueil Hozana Tools", layout="centered")

# Appliquer un style plus épuré et espacé
st.markdown("""
    <style>
    .main {
        padding-top: 3rem;
    }
    .title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #555;
        margin-bottom: 2rem;
    }
    .module-card {
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        background-color: #f9f9f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        padding: 0.75rem;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Titre et sous-titre
st.markdown('<div class="title">🛠️ Outils Hozana</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Bienvenue sur la plateforme d’outils internes Hozana.<br>Choisissez un module pour commencer :</div>', unsafe_allow_html=True)

# Dictionnaire des modules disponibles
modules = {
    "Traduction multilingue d’articles": "1_Traduction_articles",
    "Publication d’articles traduits": "2_Publication_articles",
    # Ajouter d'autres outils ici
}

# Choix de l'utilisateur dans une carte
with st.container():
    st.markdown('<div class="module-card">', unsafe_allow_html=True)

    choix = st.selectbox("📂 Sélectionnez un outil :", list(modules.keys()))

    if modules[choix]:
        st.markdown(f"#### 👉 Lancer le module : **{choix}**")
        st.page_link(f"pages/{modules[choix]}.py", label="🚀 Ouvrir", icon="🚀")
    else:
        st.info("Ce module n’est pas encore disponible.")

    st.markdown('</div>', unsafe_allow_html=True)
