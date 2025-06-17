import streamlit as st
import pandas as pd
import tempfile
import os
import time
import re
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Config page ---
st.set_page_config(page_title="Publication Admin Hozana", layout="wide")

# --- Design harmonisé ---
st.markdown("""
    <style>
        html, body {
            font-family: 'Segoe UI', sans-serif;
        }
        .block-container {
            padding-top: 2rem;
        }
        .title {
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        .section-title {
            font-size: 1.1rem;
            font-weight: 600;
            margin-top: 1.5rem;
            margin-bottom: 0.5rem;
        }
        .tool-card {
            padding: 1.25rem;
            border-radius: 1rem;
            background-color: #f9f9f9;
            box-shadow: 0 1px 4px rgba(0,0,0,0.05);
            margin-bottom: 1.5rem;
        }
        .stButton>button {
            width: 100%;
            padding: 0.75rem;
            font-weight: bold;
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

st.markdown('<div class="title">Publication automatique d\'articles Hozana</div>', unsafe_allow_html=True)

# Variables globales
driver = None
excel_path = None

# === OUTILS SLUGS & URL ===
def extraire_segments(url):
    if pd.isna(url): return []
    try:
        parsed = urlparse(url if url.startswith("http") else f"https://{url.lstrip('/')}")
        return [s for s in parsed.path.strip("/").split("/") if s]
    except: return []

def calcul_profondeur(url):
    segments = extraire_segments(url)
    return len(segments) - 1 if segments else 0

def trouver_url_parent(url):
    segments = extraire_segments(url)
    return "https://hozana.org" if len(segments) <= 1 else "https://hozana.org/" + "/".join(segments[:-1])

def extraire_slug_depuis_url(url):
    try:
        path = urlparse(url).path
        segments = [s for s in path.strip("/").split("/") if s]
        if segments and segments[0] in ["fr", "en", "es", "pt", "de", "it"]:
            segments = segments[1:]
        return "/" + "/".join(segments) if segments else "/"
    except: return None

# === Nettoyage ===
def nettoyer_fichier_excel(path):
    df = pd.read_excel(path)
    df["profondeur"] = df["URL"].apply(calcul_profondeur)
    df["url parent"] = df["URL"].apply(trouver_url_parent)
    df.to_excel(path, index=False)
    return df

# === Récupérer les IDs existants ===
def collecter_ids_dans_page_guides(driver, langue):
    driver.get(f"https://admin.hozana.org/{langue}/guides")
    time.sleep(3)
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    for link in driver.find_elements(By.XPATH, "//a[contains(@href, '#collapseGroup')]"):
        try: driver.execute_script("arguments[0].click();", link); time.sleep(0.2)
        except: pass

    slug_to_id = {}
    rows = driver.find_elements(By.XPATH, "//tr")
    for row in rows:
        try:
            tds = row.find_elements(By.XPATH, ".//td")
            if len(tds) >= 2:
                slug_texte = tds[1].text.strip()
                if slug_texte:
                    lien = row.find_element(By.XPATH, ".//a[contains(@href, '?parent=')]")
                    href = lien.get_attribute("href")
                    match = re.search(r'parent=(\d+)', href)
                    if match:
                        numero = match.group(1)
                        slug_to_id[slug_texte] = numero
        except:
            continue
    return slug_to_id

# === Publication ===
def publier_article(driver, url, title, slug, meta, content):
    try:
        driver.get(url)
        time.sleep(4)
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//input[contains(@id, 'title')]"))).send_keys(title)
        driver.find_element(By.XPATH, "//input[contains(@id, 'slug')]").send_keys(slug)
        WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, "guide_form_metaDescription"))).send_keys(meta)
        editor = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.fr-element.fr-view[contenteditable='true']")))
        driver.execute_script("""
            arguments[0].focus();
            document.execCommand('selectAll', false, null);
            document.execCommand('insertHTML', false, arguments[1]);
        """, editor, content)
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, "guide_form[saveAsDraft]"))).click()
        time.sleep(6)
        return True
    except Exception as e:
        return False

# === Boucle principale SANS étape manuelle ===
def lancer_publication(driver, path):
    df = nettoyer_fichier_excel(path)
    df["ID parent"] = df.get("ID parent", None)
    df["Admin publication url"] = df.get("Admin publication url", None)
    df["Statut publication"] = df.get("Statut publication", "Non publié")
    df["Slug"] = df["URL"].apply(lambda u: extraire_slug_depuis_url(u).split("/")[-1] if pd.notna(u) else "")

    langues = df["Langue"].dropna().unique()
    slug_par_langue = {lang.lower(): collecter_ids_dans_page_guides(driver, lang.lower()) for lang in langues}

    profondeur = 1
    total_a_publier = len(df[df["Admin publication url"].isna()])
    nb_publies = 0
    progress_bar = st.progress(0)
    progress_text = st.empty()

    while True:
        for idx, row in df.iterrows():
            lang = str(row.get("Langue", "fr")).lower()
            if row.get("profondeur") != profondeur or pd.notna(row.get("Admin publication url")):
                continue
            slug_parent = extraire_slug_depuis_url(row.get("url parent"))
            for s, idp in slug_par_langue[lang].items():
                if s.strip().lower().rstrip("/") == slug_parent.strip().lower().rstrip("/"):
                    df.at[idx, "ID parent"] = idp
                    df.at[idx, "Admin publication url"] = f"https://admin.hozana.org/{lang}/guide?parent={idp}"
                    break

        df.to_excel(path, index=False)

        lignes_a_traiter = df[(df["profondeur"] == profondeur) & (df["Admin publication url"].notna())]

        for i, (idx, row) in enumerate(lignes_a_traiter.iterrows(), start=1):
            url = row.get("Admin publication url")
            if not url or pd.isna(url): continue
            st.write(f"📄 Publication article {idx+1} : {row['Title']}")
            success = publier_article(
                driver, url,
                row.get("Title", ""),
                row.get("Slug", ""),
                row.get("Meta Description", ""),
                row.get("Content", "")
            )
            if success:
                df.at[idx, "Statut publication"] = "Publié ✅"
            else:
                df.at[idx, "Statut publication"] = "Erreur ❌"

            nb_publies += 1
            percent = int((nb_publies / total_a_publier) * 100) if total_a_publier else 100
            progress_bar.progress(min(percent, 100))
            progress_text.text(f"{percent}% des articles publiés ({nb_publies}/{total_a_publier})")
            df.to_excel(path, index=False)

        profondeur += 1
        if not any(df["Admin publication url"].isna()):
            break

    progress_bar.empty()
    progress_text.text("✅ Publication terminée.")
    return path

# === Interface Streamlit ===

uploaded_file = st.file_uploader("📁 Importez votre fichier Excel", type="xlsx")
if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(uploaded_file.getvalue())
        excel_path = tmp.name
    st.success("Fichier chargé avec succès.")

    if st.button("🔐 Connexion Admin (ouvrir le navigateur)"):
        driver = webdriver.Chrome()
        driver.get("https://admin.hozana.org/login")
        st.session_state["driver"] = driver
        st.info("Connectez-vous dans le navigateur, puis revenez ici.")

    if "driver" in st.session_state and st.button("🚀 Lancer la publication"):
        with st.spinner("Publication en cours..."):
            driver = st.session_state["driver"]
            path_final = lancer_publication(driver, excel_path)
            with open(path_final, "rb") as f:
                st.download_button("📥 Télécharger le fichier mis à jour", data=f, file_name="publication_finale.xlsx")
            st.success("Publication terminée.")
            driver.quit()
