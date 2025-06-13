import pandas as pd
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
import streamlit as st

class Config:
    def __init__(self, openai_client, deepl_key, source_lang, google_credentials_dict):
        self.openai_client = openai_client
        self.DEEPL_API_KEY = deepl_key
        self.SOURCE_LANG = source_lang
        self.google_credentials_dict = google_credentials_dict

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

def translate_text(text, target_lang, config: Config):
    if not text or pd.isna(text):
        return ""
    url = "https://api.deepl.com/v2/translate"
    data = {
        "auth_key": config.DEEPL_API_KEY,
        "text": str(text),
        "source_lang": config.SOURCE_LANG,
        "target_lang": target_lang,
        "tag_handling": "html"
    }
    try:
        response = requests.post(url, data=data, timeout=30)
        response.raise_for_status()
        return response.json()["translations"][0]["text"]
    except Exception as e:
        print(f"[❌ DeepL] ({target_lang}) : {e}")
        return text

def get_communities_from_sheet():
    credentials = service_account.Credentials.from_service_account_info(
        dict(st.secrets["GOOGLE_CREDENTIALS_JSON"]),
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    service = build("sheets", "v4", credentials=credentials)
    result = service.spreadsheets().values().get(
        spreadsheetId="1HWgw3qhjGxaFE1gDFwymFHcPodt88hzXYvk1YPxLxWw",
        range="Question 7352!A2:D"
    ).execute()
    values = result.get("values", [])
    df = pd.DataFrame(values, columns=["Lang", "Community ID", "Name"])
    return df
    
def get_embedding(text, config: Config):
    if text in embedding_cache:
        return embedding_cache[text]
    response = client.embeddings.create(
        model=OPENAI_EMBED_MODEL,
        input=[text]
    )
    embedding = response.data[0].embedding
    embedding_cache[text] = embedding
    with open(EMBED_CACHE_FILE, "w") as f:
        json.dump(embedding_cache, f)
    return embedding

def evaluer_accroche_chatgpt(titre):
    try:
        prompt = f"""
Tu es un expert en marketing chrétien.

Note ce titre sur 5 pour sa capacité à faire cliquer un internaute catholique sur le site Hozana.

Critères :
- ✔️ Titre court (3–8 mots)
- ✔️ Clarté immédiate
- ✔️ Appel à l'action (implicite ou explicite)
- ✔️ Impact émotionnel
- ❌ Les titres vagues, trop longs ou peu engageants doivent recevoir une note basse.

Règles :
- 5 = exceptionnel
- 4 = très bon
- 3 = correct
- 2 ou moins = faible

Titre : « {titre} »

Réponds uniquement par un chiffre entre 1 et 5, sans commentaire.
"""
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        contenu = response.choices[0].message.content.strip()
        score = float(contenu.replace(",", "."))
        return min(max(score, 0), 5)
    except Exception as e:
        print(f"Erreur GPT : {e}")
        return 2.5

def suggest_ctas(article_title, lang="fr", config=None):
    df = get_communities_from_sheet()
    df = df[df["Lang"] == lang].copy()
    df["embedding"] = df["Name"].apply(lambda x: get_embedding(x, config))
    df["embedding_vec"] = df["embedding"].apply(np.array)
    article_embedding = get_embedding(article_title, config)
    embeddings_matrix = np.vstack(df["embedding_vec"].values)
    similarities = cosine_similarity([article_embedding], embeddings_matrix)[0]
    df["similarity"] = similarities
    top_df = df.sort_values("similarity", ascending=False).head(TOP_SEMANTIC).copy()
    top_df["accroche_score"] = top_df["Name"].apply(evaluer_accroche_chatgpt)
    top_df["accroche_score_norm"] = top_df["accroche_score"] / 5
    top_df["score_total"] = 0.8 * top_df["similarity"] + 0.2 * top_df["accroche_score_norm"]
    final_df = top_df.sort_values("score_total", ascending=False).head(TOP_FINAL)

    if final_df["score_total"].max() < 0.6:
        default_communities = {
            "fr": ("7714", "NEUVAINE IRRÉSISTIBLE de Padre Pio"),
            "en": ("7667", "A Prayer A Day"),
            "es": ("8601", "Novena a la Virgen de Guadalupe"),
            "pt": ("10222", "Novena de São Padre Pio"),
        }
        if lang in default_communities:
            default_id, default_name = default_communities[lang]
            default_row = pd.DataFrame([{
                "Community ID": default_id,
                "Name": default_name,
                "similarity": 0,
                "accroche_score": 5,
                "score_total": 1.0
            }])
            final_df = pd.concat([default_row, final_df], ignore_index=True)

    return final_df.sort_values("score_total", ascending=False).head(TOP_FINAL)

def remplacer_community_cards(text, lang, title):
    supported_langs = ["FR", "EN", "ES", "PT"]
    lang = lang.upper()

    pattern = re.compile(r"\[community-card\s+id\s*=\s*(\d+)\s*\]", flags=re.IGNORECASE)
    matches = list(pattern.finditer(text))
    print(f"🔍 {len(matches)} occurrences [community-card id=...] détectées.")

    if not matches:
        return text

    if lang not in supported_langs:
        print(f"🌍 Langue '{lang}' non supportée pour les cards — cards supprimées.")
        return pattern.sub('', text)

    print(f"\n🔎 Remplacement des community cards pour la langue : {lang} | Titre : {title}")
    top_communities = suggest_ctas(title, lang.lower(), config)

    if top_communities.empty:
        print("❌ Aucune communauté suggérée.")
        return text

    nouveaux_ids = top_communities["Community ID"].tolist()
    noms = top_communities["Name"].tolist()

    print("🎯 Communautés suggérées :")
    for i, (cid, name) in enumerate(zip(nouveaux_ids, noms), 1):
        print(f"  {i}. ID={cid} → {name}")

    def replacer(match):
        i = replacer.counter
        replacer.counter += 1
        if i < len(nouveaux_ids):
            new_id = nouveaux_ids[i]
            print(f"🔁 Remplacement : ID {match.group(1)} → {new_id}")
            return f"[community-card id={new_id}]"
        else:
            print(f"❌ Supprimé : trop de cards, pas assez de suggestions")
            return ''

    replacer.counter = 0
    text = pattern.sub(replacer, text)

    print(f"✅ Texte final après remplacement :\n{text[:500]}...\n")
    return text


def load_url_mapping(config: Config):
    import gspread
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_info(
        config.google_credentials_dict,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive"
        ]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key("1owYRrjYnW2DKQMJ5Pk2q-zY8IY1DP1lpZagXjJCrpDM")
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_records()

    mapping = {}
    for row in data:
        keys = {k.strip(): v.strip().rstrip("/") for k, v in row.items() if isinstance(v, str)}
        fr_url = keys.get("Article FR", "")
        if not fr_url:
            continue
        mapping[fr_url] = {
            "FR": keys.get("Article FR", ""),
            "EN": keys.get("Article EN", ""),
            "ES": keys.get("Article ES", ""),
            "PT": keys.get("Article PT", ""),
            "IT": keys.get("Article IT", ""),
            "PL": keys.get("Article PL", "")
        }

    return mapping


def resolve_translated_url(original_url, lang, url_mapping, translated_segments_cache, config: Config):
    base_url = "https://hozana.org"
    normalized_url = original_url.strip().rstrip("/")
    relative_path = normalized_url.replace(base_url, "")
    segments = [seg for seg in relative_path.strip("/").split("/") if seg]

    for i in range(len(segments), 0, -1):
        partial_url = f"{base_url}/{'/'.join(segments[:i])}"
        if partial_url in url_mapping and lang in url_mapping[partial_url] and url_mapping[partial_url][lang]:
            known_translation = url_mapping[partial_url][lang]
            translated_segments = known_translation.replace(base_url, "").strip("/").split("/")
            remaining_segments = segments[i:]
            for seg in remaining_segments:
                key = (seg, lang)
                if key in translated_segments_cache:
                    translated_slug = translated_segments_cache[key]
                else:
                    translated = translate_text(seg.replace("-", " "), lang, config)
                    translated = translated.replace(" ", "-")
                    translated_slug = slugify(translated)
                    translated_segments_cache[key] = translated_slug
                translated_segments.append(translated_slug)
            return f"{base_url}/{'/'.join(translated_segments)}"
    print(f"⚠️ Aucune correspondance trouvée pour : {original_url}")
    return ""

def refine_with_gpt(text, field_name, lang, title=""):
    if not text.strip():
        return text

    if field_name.lower() == "meta description":
        instructions = """
Tu es un rédacteur web expert. Tu vas recevoir une meta description d'article chrétien.
Ta mission :
- Rendre la description plus attractive, naturelle et claire
- Ne pas dépasser 160 caractères
- Ne pas reformuler si le texte est déjà bon et dans la limite
Langue cible : """ + lang.upper()
    elif field_name.lower() == "title":
        instructions = """
Tu es un expert en SEO chrétien. Voici un titre d'article.
Ta mission :
- Vérifie qu’il est clair, percutant, sans ponctuation inutile
- Ne dépasse pas 60 caractères
- Corrige uniquement s’il y a une erreur ou un problème de style
Langue cible : """ + lang.upper()
    else:
        return text  # champ inconnu

    prompt = f"{instructions}\n\nTexte : {text}"

    try:
        response = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        new_text = response.choices[0].message.content.strip()
        return new_text if new_text else text
    except Exception as e:
        print(f"[❌ GPT refine_with_gpt] Erreur : {e}")
        return text
    

def reformuler_cta_avec_gpt(html_bloc, replacement_name, replacement_url, lang):
    prompt = f"""
Tu es un rédacteur professionnel spécialisé dans les contenus chrétiens en ligne.

Tu vas recevoir un bloc de texte HTML qui contient une phrase avec un lien vers une communauté de prière. Cette communauté doit être remplacée par une autre (voir ci-dessous). Tu dois reformuler uniquement cette phrase pour :

✅ intégrer le **titre et le lien** de la nouvelle communauté
✅ respecter le **ton et le style** du paragraphe d'origine
✅ **éviter toute répétition** ou maladresse (ex. « priez une neuvaine à Neuvaine à ... »)
✅ conserver la **structure HTML** intacte autour du texte reformulé
✅ ne **modifier que la phrase contenant le lien**, pas le reste du paragraphe
✅ utiliser une tournure fluide et naturelle dans la langue **{lang.upper()}**

Nouvelle communauté à insérer :
- Titre : {replacement_name}
- URL : {replacement_url}

Langue cible : {lang.upper()}

Bloc HTML original :
{html_bloc}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[❌ GPT reformulation CTA] Erreur : {e}")
        return html_bloc


def replace_links_in_html(content, lang, url_mapping, translated_segments_cache, config: Config):
    def replace_href(match):
        href = match.group(1)
        anchor_text = match.group(2)
        full_match = match.group(0)

        if href.startswith("/"):
            full_url = "https://hozana.org" + href
        elif href.startswith("http"):
            full_url = href
        else:
            return full_match

        if "/communaute" in full_url or "/community" in full_url:
            supported_langs = ["fr", "en", "es", "pt"]
            if lang.lower() not in supported_langs:
                print(f"🌍 Langue non supportée pour communauté ({lang}) → lien supprimé.")
                return anchor_text

            print(f"\n🧩 Lien vers communauté détecté : {full_url}")
            top_communities = suggest_ctas(anchor_text, lang.lower(), config)

            if not top_communities.empty and top_communities["score_total"].max() >= 0.6:
                best = top_communities.iloc[0]
                best_id = best["Community ID"]
                best_name = best["Name"]

                url_by_lang = {
                    "fr": f"https://hozana.org/communaute/{best_id}",
                    "en": f"https://hozana.org/en/community/{best_id}",
                    "es": f"https://hozana.org/es/comunidad/{best_id}",
                    "pt": f"https://hozana.org/pt/comunidade/{best_id}"
                }

                new_url = url_by_lang[lang.lower()]
                return reformuler_cta_avec_gpt(full_match, best_name, new_url, lang)
            else:
                print("❌ Aucune correspondance suffisamment proche — lien supprimé.")
                return full_match.replace(f'<a href="{href}">{anchor_text}</a>', anchor_text)

        translated_url = resolve_translated_url(full_url, lang, url_mapping, translated_segments_cache, config)
        return f'<a href="{translated_url}">{anchor_text}</a>' if translated_url else anchor_text

    return re.sub(r'<a\s+href="([^"]+)">(.+?)</a>', replace_href, content)

def traiter_citations_avec_gpt(content, lang, config: Config):
    prompt = f"""... Tu es un assistant théologique et liturgique.

Tu reçois un texte HTML contenant un ou plusieurs extraits entre guillemets, en italique ou entre parenthèses. Ces extraits peuvent être :
- Une prière chrétienne (ex. : "Je vous salue Marie", "Notre Père")
- Un passage biblique (ex. : Matthieu 6,9-13)
- Un extrait du Catéchisme de l’Église catholique (ex. : "L’homme est un être religieux", CEC 27)
- Ou tout autre passage cité

🎯 Ta mission :
1. Parcoure tout le texte.
2. À chaque passage cité :
   - Si tu reconnais une version officielle connue dans la langue cible (ex. liturgie, Bible, catéchisme), **remplace le passage par cette version officielle complète et exacte**.
   - Si aucune version officielle n’existe, **traduis fidèlement le passage sans le reformuler**.
3. Ne modifie jamais un passage déjà correct.
4. Respecte **strictement le balisage HTML** autour de chaque citation (garde les <p>, <em>, etc.)

⚠️ Ne reformule jamais les extraits sacrés.
⚠️ Ne change pas les balises HTML.
⚠️ Ne remplace que les passages cités. Laisse tout le reste du texte inchangé.

🌍 Langues :
- **Français** : utiliser la version liturgique AELF ([aelf.org](https://www.aelf.org)), sinon la Bible de Jérusalem.
- **Anglais** : NABRE ([usccb.org](https://bible.usccb.org)) pour la liturgie, sinon RSV-CE.
- **Espagnol** : Biblia de la Conferencia Episcopal Española (BCEE), sinon Biblia de Jerusalén.
- **Portugais** : Bíblia da CNBB ([cnbb.org.br](https://www.cnbb.org.br)), sinon Bíblia de Jerusalém.
- **Italien** : La Bibbia CEI ([chiesacattolica.it](https://www.chiesacattolica.it/liturgia-del-giorno)), sinon Bibbia di Gerusalemme.
- **Polonais** : Biblia Tysiąclecia ([biblia.deon.pl](https://biblia.deon.pl)), sinon Biblia Paulistów.

Langue cible : {lang}
 ...""".replace("{lang}", lang.upper())
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt + "\n\nTexte HTML :\n" + content}],
            temperature=0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[❌ GPT - Citations] Erreur : {e}")
        return content

def reformuler_paragraphes_communautes(html, lang, config: Config):
    """
    Repère les paragraphes contenant des liens vers des communautés Hozana
    (toutes langues confondues) et les reformule avec GPT pour un style plus fluide.
    """
    from bs4 import BeautifulSoup

    # Expressions régulières pour toutes les langues
    community_url_pattern = re.compile(
        r"https://hozana\.org(/(en/community|es/comunidad|pt/comunidade|communaute))/\d+", re.IGNORECASE
    )

    soup = BeautifulSoup(html, "html.parser")
    for p in soup.find_all("p"):
        if p.find("a", href=community_url_pattern):
            original_text = str(p)

            prompt = f"""
Tu es rédacteur pour le site chrétien hozana.org. Voici un paragraphe en langue {lang}.
⚠️ Tu ne dois en aucun cas retraduire en français. Le texte doit rester strictement dans la langue cible.
Il contient des liens vers des communautés de prière. Ta tâche est de :

- Corriger et reformuler le texte pour le rendre fluide, naturel et engageant
- Garder un ton adapté au public chrétien (bienveillant, simple, jamais commercial)
- Conserver tous les liens HTML **intacts**
- Ne pas modifier la structure HTML du paragraphe (pas de division ou fusion)
- Améliorer uniquement la qualité rédactionnelle

Voici le paragraphe à améliorer :
{original_text}

Réécris uniquement le paragraphe corrigé.
"""

            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                new_html = response.choices[0].message.content.strip()
                p.replace_with(BeautifulSoup(new_html, "html.parser"))
            except Exception as e:
                print(f"[⚠️ GPT erreur reformulation communauté] {e}")
                continue

    return str(soup)



# === FONCTION D'INSERTION DES VERSETS OFFICIELS DANS LE TEXTE ===
def normalize_book_name(name):
    name = unicodedata.normalize("NFD", name)
    name = name.encode("ascii", "ignore").decode("utf-8")
    return name.lower().strip()

def insert_official_verses(html: str, bible_data: dict, lang: str) -> tuple[str, int]:
    import re
    count = 0  # compteur de versets insérés

    pattern = re.compile(r"\b\(?([A-ZÉa-zéèêîôûçàäëïöü\-]+)[ ,:]*(\d+)[ ,:]*(\d+)(?:-(\d+))?\)?")


    def replacer(match):
        nonlocal count
        book_abbr = match.group(1)
        chapter = match.group(2)
        start_verse = int(match.group(3))
        end_verse = int(match.group(4)) if match.group(4) else start_verse

        normalized_abbr = normalize_book_name(book_abbr)
        book_key = BOOK_ABBREVIATIONS.get(normalized_abbr, "")
        if not book_key:
            return match.group(0)

        # Majuscule initiale pour correspondre aux clés du JSON ("Genesis", pas "genesis")
        book_key = book_key.capitalize()

        try:
            verses = []
            for v in range(start_verse, end_verse + 1):
                verse_key = str(v).zfill(2)
                if (
                    book_key in bible_data and
                    str(chapter) in bible_data[book_key] and
                    verse_key in bible_data[book_key][str(chapter)]
                ):
                    verse_text = bible_data[book_key][str(chapter)][verse_key]
                    verses.append(verse_text)
                else:
                    print(f"⚠️ Verset manquant : {book_key} {chapter}:{verse_key}")
            
            if not verses:
                return match.group(0)  # aucun verset insérable

            official = " ".join(verses).strip()
            count += 1

            styled_annotation = (
                f'<div style="margin: 1em 0; padding: 1em; background-color: #f0fdfa; border-left: 5px solid #17a589; '
                f'font-family: Calibri, Helvetica, sans-serif, serif, EmojiFont; font-size: 16px; color: #117864;">'
                f'<strong style="color: #0e6655;">⚠️ Verset officiel :</strong><br>{official}'
                f'</div>'
            )

            return match.group(0) + " " + styled_annotation

        except Exception as e:
            print(f"⚠️ Verset introuvable : {book_key} {chapter}:{start_verse}-{end_verse} ({e})")
            return match.group(0)

    new_html = pattern.sub(replacer, html)
    return new_html, count

def traduire_articles_selectionnes(df_selection, langue, url_mapping, translated_segments_cache, client, bible_data_by_lang, config: Config):
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

        translated_url = resolve_translated_url(original_url, langue, url_mapping, translated_segments_cache, config)

        title = translate_text(title_src, langue, config)
        title = refine_with_gpt(title, "Title", langue)

        meta = translate_text(meta_src, langue, config)
        meta = refine_with_gpt(meta, "Meta Description", langue)

        content = translate_text(content_src, langue, config)
        content = replace_links_in_html(content, langue, url_mapping, translated_segments_cache, config)
        content = traiter_citations_avec_gpt(content, langue, config)
        content = remplacer_community_cards(content, langue, title, config)
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
