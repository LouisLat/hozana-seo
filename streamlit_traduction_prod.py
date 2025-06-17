import streamlit as st

# Configuration de la page
st.set_page_config(page_title="Accueil Hozana Tools", layout="centered")

# Titre de la page
st.title("🛠️ Outils Hozana")

st.markdown("Bienvenue sur la plateforme d’outils internes Hozana. Choisissez un module pour commencer :")

# Dictionnaire des modules disponibles
modules = {
    "Traduction multilingue d’articles": "1_Traduction_articles",
    "Traduction multilingue d’articles": "2_Publication_articles"  # correspond au nom de ton fichier sans .py
    # Tu peux ajouter d'autres modules ici
}

# Choix de l'utilisateur
choix = st.selectbox("Sélectionnez un outil :", list(modules.keys()))

# Affichage du bouton pour accéder au module
if modules[choix]:
    st.markdown(f"👉 Cliquez ci-dessous pour ouvrir **{choix}** :")
    st.page_link(f"pages/{modules[choix]}.py", label="Lancer", icon="🚀")
else:
    st.info("Ce module n’est pas encore disponible.")
