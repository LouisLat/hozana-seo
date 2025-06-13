import streamlit as st
import pandas as pd
import json
import time
from script_traduction import traduire_articles_selectionnes
from google.oauth2 import service_account
from googleapiclient.discovery import build
from openai import OpenAI
import base64
from script_traduction import Config, traduire_articles_selectionnes, load_url_mapping
from openai import OpenAI


# === CONFIG ===
SHEET_ID = "1HWgw3qhjGxaFE1gDFwymFHcPodt88hzXYvk1YPxLxWw"
GOOGLE_CREDENTIALS_DICT = dict(st.secrets["GOOGLE_CREDENTIALS_JSON"])

config = Config(
    openai_client=OpenAI(api_key=st.secrets["api"]["OPENAI_API_KEY"]),
    deepl_key=st.secrets["api"]["DEEPL_API_KEY"],
    source_lang="FR",
    google_credentials_dict=GOOGLE_CREDENTIALS_DICT
)
SHEET_RANGE = "Question 7364!A1:ZZ"
DEEPL_API_KEY = st.secrets["api"]["DEEPL_API_KEY"]
OPENAI_API_KEY = st.secrets["api"]["OPENAI_API_KEY"]
GOOGLE_CREDENTIALS_DICT = dict(st.secrets["GOOGLE_CREDENTIALS_JSON"])
client = OpenAI(api_key=OPENAI_API_KEY)

BIBLE_FILES = {
    "fr": "bible-fr.json",
    "en": "bible-en.json",
    "es": "bible-es.json",
    "it": "bible-it.json",
    "pl": "bible-pl.json"
}

# Chargement des bibles
bible_data_by_lang = {}
for lang_code, file_path in BIBLE_FILES.items():
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            bible_data_by_lang[lang_code] = json.load(f)
    except:
        bible_data_by_lang[lang_code] = {}

# === Lecture Google Sheet
@st.cache_data
def get_articles_sheet():
    credentials = service_account.Credentials.from_service_account_info(
        dict(st.secrets["GOOGLE_CREDENTIALS_JSON"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=credentials)
    result = service.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=SHEET_RANGE).execute()
    values = result.get("values", [])
    if not values:
        return pd.DataFrame()
    max_len = max(len(row) for row in values)
    values_uniform = [row + [''] * (max_len - len(row)) for row in values]
    columns = values_uniform[0]
    data = values_uniform[1:]
    df = pd.DataFrame(data, columns=columns)
    content_cols = [col for col in df.columns if col.startswith("Content_Part")]
    if content_cols:
        df["Content"] = df[content_cols].fillna('').agg(''.join, axis=1)
    return df

# === UI Streamlit ===
st.set_page_config(page_title="Traduction articles Hozana", layout="wide")

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
        .section-title {
            font-weight: 600;
            font-size: 1.1rem;
            margin-top: 2rem;
        }
        .st-do {
            max-width: none !important;
            white-space: normal !important;
            overflow-wrap: anywhere !important;
        }
        .stMultiSelect > div {
            max-height: 150px;
            overflow-y: auto;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">Traduction multilingue d’articles Hozana</div>', unsafe_allow_html=True)

df = get_articles_sheet()
urls = df["Complete URL"].dropna().unique().tolist()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown('<div class="section-title">1. Choisissez les URLs à traduire</div>', unsafe_allow_html=True)
    selected_urls = st.multiselect("", urls)

with col2:
    st.markdown('<div class="section-title">2. Choisissez les langues cibles</div>', unsafe_allow_html=True)
    selected_langs = st.multiselect("", ["EN", "ES", "PT", "IT", "PL"], default=["EN"])

if selected_urls:
    st.markdown('<div class="section-title">Articles sélectionnés :</div>', unsafe_allow_html=True)
    for url in selected_urls:
        st.markdown(f"- [{url}]({url})")

st.markdown("---")

if st.button("Traduire maintenant"):
    if not selected_urls or not selected_langs:
        st.warning("Merci de sélectionner au moins une URL et une langue.")
    else:
        with st.spinner("⏳ Traduction en cours, veuillez patienter..."):
            df_selection = df[df["Complete URL"].isin(selected_urls)].copy()
            url_mapping = load_url_mapping(config)
            translated_segments_cache = {}
            total = len(selected_langs) * len(df_selection)
            progress = st.empty()

            rows = []
            step = 0

            for lang in selected_langs:
                output_df = traduire_articles_selectionnes(
                    df_selection,
                    lang,
                    url_mapping,
                    translated_segments_cache,
                    config
                )
                rows.append(output_df)
                step += len(df_selection)
                percent = step / total
                progress.progress(percent, text=f"{int(percent * 100)}% - Traduction {lang} terminée")

            final_df = pd.concat(rows, ignore_index=True)
            file_name = f"articles_traduits_{int(time.time())}.xlsx"
            final_df.to_excel(file_name, index=False)

            with open(file_name, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:application/octet-stream;base64,{b64}" download="{file_name}">⬇️ Télécharger le fichier traduit</a>'
                st.markdown(href, unsafe_allow_html=True)

            st.success("✅ Traduction terminée avec succès.")
