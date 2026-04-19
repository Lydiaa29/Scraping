"""
Scraper pour dzexams.com - Version requests + BeautifulSoup
Le site retourne du HTML complet, pas besoin de Selenium/Playwright.

Installation :
    pip install requests beautifulsoup4 lxml
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
import base64
import re

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_URL    = "https://www.dzexams.com"
OUTPUT_FILE  = "dzexams_full.json"
DOWNLOAD_DIR = "downloads"
DELAY        = 0.5   # secondes entre requêtes (visiter les pages de détail prend du temps)

# Liste des niveaux à scraper
LEVELS = [
    "1ap", "2ap", "3ap", "4ap", "5ap",           # Primaire
    "1am", "2am", "3am", "4am", "bem",           # Moyen
    "1as", "2as", "3as", "bac"                   # Secondaire
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

session = requests.Session()
session.headers.update(HEADERS)


# ─── Utilitaire ───────────────────────────────────────────────────────────────

def get_soup(url: str) -> BeautifulSoup | None:
    print(f"    → {url}")
    try:
        r = session.get(url, timeout=15)
        r.raise_for_status()
        time.sleep(DELAY)
        soup = BeautifulSoup(r.text, "lxml")
        print(f"    ✓ {len(r.text)} octets")
        return soup
    except requests.RequestException as e:
        print(f"    ✗ Erreur : {e}")
        return None


def abs_url(href: str) -> str:
    return href if href.startswith("http") else BASE_URL + href


def enc(data_id: str) -> str:
    """Version Python de la fonction enc() du site dzexams.com"""
    try:
        # 1. Décodage Base64
        decoded = base64.b64decode(data_id).decode('latin-1')
        # 2. Soustraire 8 à chaque code de caractère
        result = "".join(chr(ord(c) - 8) for c in decoded)
        return result
    except Exception:
        return ""


def sanitize_filename(name: str) -> str:
    """Nettoie une chaîne pour l'utiliser comme nom de fichier/dossier"""
    # Remplace les retours à la ligne et espaces multiples par un seul espace
    name = re.sub(r'\s+', ' ', name)
    # Remplace les caractères interdits par des underscores
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    # Nettoyage final
    return name.strip()[:100]


def download_pdf(url: str, save_path: str) -> bool:
    """Télécharge un fichier PDF et le sauvegarde localement"""
    if os.path.exists(save_path):
        # On peut choisir de ne pas retélécharger
        return True

    try:
        # Créer les dossiers parents si nécessaire
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        print(f"      ⬇ Téléchargement... {os.path.basename(save_path)}")
        r = session.get(url, stream=True, timeout=30)
        r.raise_for_status()
        
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"      ✗ Erreur téléchargement : {e}")
        return False


# ─── Scraping matières d'un niveau ────────────────────────────────────────────

def scrape_matieres(level: str) -> list[dict]:
    url = f"{BASE_URL}/ar/{level}"
    print(f"\n[*] Niveau : {level.upper()} ({url})")
    soup = get_soup(url)
    if not soup:
        return []

    matieres = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        parts = [p for p in href.split("/") if p]
        # /ar/niveau/matiere → 3 segments
        if len(parts) == 3 and parts[:2] == ["ar", level]:
            url_mat = abs_url(href)
            if url_mat in seen:
                continue
            seen.add(url_mat)
            titre = a.get_text(strip=True)
            # Nombre de fichiers dans le bloc parent
            parent = a.find_parent()
            nb = ""
            if parent:
                txt = parent.get_text(" ", strip=True)
                if "عدد" in txt or "ملف" in txt:
                    nb = txt
            if titre:
                matieres.append({
                    "level": level,
                    "matiere": titre, 
                    "url": url_mat, 
                    "nb_fichiers": nb
                })

    print(f"    → {len(matieres)} matières trouvées")
    return matieres


# ─── Scraping filières ────────────────────────────────────────────────────────

def scrape_filieres(mat: dict) -> list[dict]:
    soup = get_soup(mat["url"])
    if not soup:
        return []

    filieres = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        url = abs_url(href)
        parts = [p for p in href.split("/") if p]
        # /ar/niveau/matiere/filiere → 4 segments
        level = mat.get("level", "")
        if (
            len(parts) == 4
            and parts[:2] == ["ar", level]
            and url not in seen
            and url != mat["url"]
        ):
            seen.add(url)
            titre = a.get_text(strip=True)
            if titre:
                filieres.append({"filiere": titre, "url": url, "matiere": mat["matiere"]})

    # Si aucune filière, la page liste directement les examens
    if not filieres:
        filieres.append({"filiere": mat["matiere"], "url": mat["url"], "matiere": mat["matiere"]})

    return filieres


# ─── Scraping examens/PDFs ────────────────────────────────────────────────────

def scrape_examens(fil: dict, mat: dict) -> list[dict]:
    soup = get_soup(fil["url"])
    if not soup:
        return []

    examens = []
    seen: set[str] = set()

    # Mappage des classes vers les préfixes d'URL (selon app.04.js)
    routes = {
        'btn-item-sujet': '/ar/sujets/',
        'btn-item-document': '/ar/documents/',
        'btn-item-annale': '/ar/annales/',
    }

    # On cherche les éléments avec data-id
    items = soup.find_all(attrs={"data-id": True})
    print(f"      → {len(items)} items trouvés avec data-id")

    for item in items:
        data_id = item.get("data-id")
        if not data_id or not isinstance(data_id, str):
            continue
            
        slug = enc(data_id)
        if not slug: continue

        # Extraction de l'année via l'attribut data-year du parent (div.item)
        annee = None
        parent_item = item.find_parent(class_="item")
        if parent_item and parent_item.has_attr("data-year"):
            val = parent_item["data-year"]
            if isinstance(val, str) and val.isdigit():
                annee = int(val)
            elif isinstance(val, list) and len(val) > 0 and str(val[0]).isdigit():
                annee = int(str(val[0]))
        
        # Déterminer le préfixe selon la classe CSS
        prefix = "/ar/annales/" # par défaut
        item_classes = item.get("class")
        # Si on ne trouve pas l'année dans l'attribut, on tente meta-item
        if not annee:
            meta_items = item.find_all(class_="meta-item")
            for mi in meta_items:
                txt = mi.get_text(strip=True)
                if txt.isdigit() and 1900 < int(txt) < 2100:
                    annee = int(txt)
                    break
        
        # Si on n'a pas trouvé l'année, on cherche dans le titre
        if not annee:
            titre_el = item.find(class_="sujet-title")
            titre = titre_el.get_text(strip=True) if titre_el else "Sans titre"
            for w in titre.replace("-", " ").split():
                if w.isdigit() and 1900 < int(w) < 2100:
                    annee = int(w)
                    break
        else:
            titre_el = item.find(class_="sujet-title")
            titre = titre_el.get_text(strip=True) if titre_el else "Sans titre"
        
        if isinstance(item_classes, list):
            for cls, pfx in routes.items():
                if cls in item_classes:
                    prefix = pfx
                    break
        
        url = abs_url(prefix + str(slug))
        if url in seen: continue
        seen.add(url)

        # Visiter la page de détail pour trouver le PDF réel
        print(f"        • [Page] {titre[:40]}...")
        pdf_url = None
        detail_soup = get_soup(url)
        if detail_soup:
            # Chercher un lien direct vers un PDF (on assure un retour booléen pour le filtre)
            pdf_link = detail_soup.find("a", href=lambda h: bool(h and str(h).endswith(".pdf")))
            if pdf_link and isinstance(pdf_link, dict) and "href" in pdf_link:
                pdf_url = abs_url(str(pdf_link["href"]))
            elif pdf_link and hasattr(pdf_link, "get"):
                href = pdf_link.get("href")
                if href:
                    pdf_url = abs_url(str(href))
        
        # Téléchargement effectif si on a le PDF
        local_path = None
        if pdf_url:
            folder = os.path.join(
                DOWNLOAD_DIR,
                sanitize_filename(mat.get("level", "inconnu")),
                sanitize_filename(fil["matiere"]),
                sanitize_filename(fil["filiere"])
            )
            filename = f"{annee or '0000'}_{sanitize_filename(titre)}.pdf"
            local_path = os.path.join(folder, filename)
            download_pdf(pdf_url, local_path)

        examens.append({
            "titre":    titre,
            "url_page": url,
            "url_pdf":  pdf_url,
            "path":     local_path,
            "annee":    annee,
            "filiere":  fil["filiere"],
            "matiere":  fil["matiere"],
            "level":    mat.get("level"),
        })

    return examens


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(
    target_levels: list[str] | None = None,
    max_matieres: int | None = None,
    max_filieres: int | None = None,
) -> list[dict]:

    all_data: list[dict] = []
    levels_to_scrape = target_levels or LEVELS

    for level in levels_to_scrape:
        # 1. Matières
        matieres = scrape_matieres(level)
        if not matieres:
            continue

        for mat in (matieres[:max_matieres] if max_matieres else matieres):
            print(f"\n  [Matière] {mat['matiere']}")

            # 2. Filières
            filieres = scrape_filieres(mat)
            print(f"      → {len(filieres)} filières")

            for fil in (filieres[:max_filieres] if max_filieres else filieres):
                print(f"    [Filière] {fil['filiere']}")

                # 3. Examens / PDFs
                examens = scrape_examens(fil, mat)
                print(f"        → {len(examens)} examens")
                for e in examens:
                    year_label = f"[{e['annee']}]" if e['annee'] else "[?]"
                    print(f"          • {year_label} {e['titre'][:55]}")

                all_data.extend(examens)

        # Sauvegarde intermédiaire après chaque niveau
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Total : {len(all_data)} examens → '{OUTPUT_FILE}'")
    return all_data


if __name__ == "__main__":
    # Pour scraper TOUT : main()
    # Pour tester un petit bout : main(target_levels=["5ap"], max_matieres=2)
    main()