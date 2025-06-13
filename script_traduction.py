import pandas as pdMore actions
import time

# Importe ici toutes tes fonctions utiles depuis ton script principal
import pandas as pd
import numpy as np
import requests
import time
import re
import unicodedata
import json
import os
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
from googleapiclient.discovery import build


# === CONFIG RECO COMMUNAUTÉS ===
SHEET_ID = "1HWgw3qhjGxaFE1gDFwymFHcPodt88hzXYvk1YPxLxWw"
SHEET_RANGE = "Question 7352!A2:D"
OPENAI_EMBED_MODEL = "text-embedding-3-small"
TOP_SEMANTIC = 20
TOP_FINAL = 10
EMBED_CACHE_FILE = "embedding_cache.json"

if os.path.exists(EMBED_CACHE_FILE):
    with open(EMBED_CACHE_FILE, "r") as f:
        embedding_cache = json.load(f)
else:
    embedding_cache = {}

BIBLE_FILES = {
    "fr": "bible-fr.json",
    "en": "bible-en.json",
    "es": "bible-es.json",
    "it": "bible-it.json",
    "pl": "bible-pl.json"
}

bible_data_by_lang = {}
for lang_code, file_path in BIBLE_FILES.items():
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            bible_data_by_lang[lang_code] = json.load(f)
    except Exception as e:
        print(f"[⚠️ ERREUR] Chargement de {file_path} : {e}")
        bible_data_by_lang[lang_code] = {}


# === TABLE DES ABRÉVIATIONS BIBLIQUES ===
BOOK_ABBREVIATIONS = {
    # FR
    "genese": "genesis",
    "exode": "exodus",
    "levitique": "leviticus",
    "nombres": "numbers",
    "deuteronome": "deuteronomy",
    "juges": "judges",
    "psaumes": "psalms",
    "proverbes": "proverbs",
    "cantique": "songofsongs",
    "sagesse": "wisdom",
    "siracide": "sirach",
    "isaie": "isaiah",
    "jeremie": "jeremiah",
    "lamentations": "lamentations",
    "ezechiel": "ezekiel",
    "matthieu": "matthew",
    "marc": "mark",
    "luc": "luke",
    "jean": "john",
    "actes": "acts",
    "romains": "romans",
    "galates": "galatians",
    "ephesiens": "ephesians",
    "philippiens": "philippians",
    "colossiens": "colossians",
    "1thessaloniciens": "1thessalonians",
    "2thessaloniciens": "2thessalonians",
    "1timothee": "1timothy",
    "2timothee": "2timothy",
    "tite": "titus",
    "philemon": "philemon",
    "hebreux": "hebrews",
    "jacques": "james",
    "1pierre": "1peter",
    "2pierre": "2peter",
    "1jean": "1john",
    "2jean": "2john",
    "3jean": "3john",
    "judas": "jude",
    "apocalypse": "revelation",

    # ES
    "génesis": "genesis",
    "éxodo": "exodus",
    "deuteronomio": "deuteronomy",
    "josué": "joshua",
    "jueces": "judges",
    "salmos": "psalms",
    "proverbios": "proverbs",
    "eclesiastico": "sirach",
    "sabiduria": "wisdom",
    "isaias": "isaiah",
    "jeremias": "jeremiah",
    "mateo": "matthew",
    "marcos": "mark",
    "lucas": "luke",
    "juan": "john",
    "hechos": "acts",
    "romanos": "romans",
    "1corintios": "1corinthians",
    "2corintios": "2corinthians",
    "galatas": "galatians",
    "efesios": "ephesians",
    "filipenses": "philippians",
    "colosenses": "colossians",
    "1tesalonicenses": "1thessalonians",
    "2tesalonicenses": "2thessalonians",
    "1timoteo": "1timothy",
    "2timoteo": "2timothy",
    "filemon": "philemon",
    "hebreos": "hebrews",
    "santiago": "james",
    "1pedro": "1peter",
    "2pedro": "2peter",
    "1juan": "1john",
    "2juan": "2john",
    "3juan": "3john",
    "judas": "jude",
    "apocalipsis": "revelation",

    # PT
    "gênesis": "genesis",
    "êxodo": "exodus",
    "levítico": "leviticus",
    "números": "numbers",
    "deuteronômio": "deuteronomy",
    "juízes": "judges",
    "provérbios": "proverbs",
    "sabedoria": "wisdom",
    "eclesiástico": "sirach",
    "isaías": "isaiah",
    "jeremias": "jeremiah",
    "lamentações": "lamentations",
    "ezequiel": "ezekiel",
    "daniel": "daniel",
    "mateus": "matthew",
    "marcos": "mark",
    "lucas": "luke",
    "joão": "john",
    "atos": "acts",
    "romanos": "romans",
    "1coríntios": "1corinthians",
    "2coríntios": "2corinthians",
    "gálatas": "galatians",
    "efésios": "ephesians",
    "filipenses": "philippians",
    "colossenses": "colossians",
    "1tessalonicenses": "1thessalonians",
    "2tessalonicenses": "2thessalonians",
    "1timóteo": "1timothy",
    "2timóteo": "2timothy",
    "tito": "titus",
    "filêmon": "philemon",
    "hebreus": "hebrews",
    "tiago": "james",
    "1pedro": "1peter",
    "2pedro": "2peter",
    "1joão": "1john",
    "2joão": "2john",
    "3joão": "3john",
    "apocalipse": "revelation",

    # IT
    "genesi": "genesis",
    "esodo": "exodus",
    "levitico": "leviticus",
    "numeri": "numbers",
    "deuteronomio": "deuteronomy",
    "giudici": "judges",
    "salmi": "psalms",
    "proverbi": "proverbs",
    "ecclesiaste": "ecclesiastes",
    "cantico": "songofsongs",
    "sapienza": "wisdom",
    "ecclesiastico": "sirach",
    "isaia": "isaiah",
    "geremia": "jeremiah",
    "lamentazioni": "lamentations",
    "ezecchiele": "ezekiel",
    "daniele": "daniel",
    "matteo": "matthew",
    "marco": "mark",
    "giovanni": "john",
    "atti": "acts",
    "romani": "romans",
    "1corinzi": "1corinthians",
    "2corinzi": "2corinthians",
    "galati": "galatians",
    "efesini": "ephesians",
    "filippesi": "philippians",
    "colossesi": "colossians",
    "1tessalonicesi": "1thessalonians",
    "2tessalonicesi": "2thessalonians",
    "1timoteo": "1timothy",
    "2timoteo": "2timothy",
    "filemone": "philemon",
    "ebrei": "hebrews",
    "giacomo": "james",
    "1pietro": "1peter",
    "2pietro": "2peter",
    "1giovanni": "1john",
    "2giovanni": "2john",
    "3giovanni": "3john",
    "giuda": "jude",
    "apocalisse": "revelation",

    # PL
    "genezis": "genesis",
    "exodo": "exodus",
    "liczb": "numbers",
    "powtórzonego prawa": "deuteronomy",
    "sędziów": "judges",
    "psalmów": "psalms",
    "przysłów": "proverbs",
    "kohleta": "ecclesiastes",
    "pieśń nad pieśniami": "songofsongs",
    "mądrości": "wisdom",
    "syracha": "sirach",
    "izajasza": "isaiah",
    "jeremiasza": "jeremiah",
    "lamentacje": "lamentations",
    "ezekiela": "ezekiel",
    "daniela": "daniel",
    "mateusza": "matthew",
    "marka": "mark",
    "łukasza": "luke",
    "jan": "john",
    "dzieje": "acts",
    "rzymian": "romans",
    "1koryntian": "1corinthians",
    "2koryntian": "2corinthians",
    "galatów": "galatians",
    "efezjan": "ephesians",
    "filipian": "philippians",
    "kolosan": "colossians",
    "1tesaloniczan": "1thessalonians",
    "2tesaloniczan": "2thessalonians",
    "1timoteusza": "1timothy",
    "2timoteusza": "2timothy",
    "tytusa": "titus",
    "filemona": "philemon",
    "hebrajczyków": "hebrews",
    "jakuba": "james",
    "1piotra": "1peter",
    "2piotra": "2peter",
    "1jana": "1john",
    "2jana": "2john",
    "3jana": "3john",
    "judy": "jude",
    "apokalipsy": "revelation"
}


# === UTILS ===
def slugify(text):
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = re.sub(r'[^a-zA-Z0-9/-]', '', text)
    text = re.sub(r'[-]+', '-', text)
    return text.lower().strip("-/")

def translate_text(text, target_lang):
    if not text or pd.isna(text):
        return ""
    url = "https://api.deepl.com/v2/translate"
    data = {
        "auth_key": DEEPL_API_KEY,
        "text": str(text),
        "source_lang": SOURCE_LANG,
        "target_lang": target_lang,
@@ -765,52 +765,52 @@
    new_html = pattern.sub(replacer, html)
    return new_html, count

def traduire_articles_selectionnes(df_selection, langue, url_mapping, translated_segments_cache, client, bible_data_by_lang):
    from script_traduction import (
        translate_text,
        resolve_translated_url,
        refine_with_gpt,
        replace_links_in_html,
        traiter_citations_avec_gpt,
        remplacer_community_cards,
        reformuler_paragraphes_communautes,
        insert_official_verses,
    )

    rows = []
    for _, row in df_selection.iterrows():
        original_url = row.get("Complete URL", "").strip().rstrip("/")
        title_src = row.get("Title", "")
        meta_src = row.get("Meta Title", "")
        content_src = row.get("Content", "")

        if not original_url:
            continue

        translated_url = resolve_translated_url(original_url, langue, url_mapping, translated_segments_cache)

        title = translate_text(title_src, langue)
        title = refine_with_gpt(title, "Title", langue)

        meta = translate_text(meta_src, langue)
        meta = refine_with_gpt(meta, "Meta Description", langue)

        content = translate_text(content_src, langue)
        content = replace_links_in_html(content, langue, url_mapping, translated_segments_cache)
        content = traiter_citations_avec_gpt(content, langue, client)
        content = remplacer_community_cards(content, langue, title)
        content = reformuler_paragraphes_communautes(content, langue)
        content, _ = insert_official_verses(content, bible_data_by_lang.get(langue.lower(), {}), langue.lower())

        translated_row = {
            "Original URL": original_url,
            "URL": translated_url,
            "Langue": langue,
            "Title": title,
            "Meta Description": meta,
            "Content": content
        }
        rows.append(translated_row)
        time.sleep(1)

    return pd.DataFrame(rows)
