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

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_URL    = "https://www.dzexams.com"
BAC_URL     = "https://www.dzexams.com/ar/bac"
OUTPUT_FILE = "dzexams_bac.json"
DELAY       = 1.0   # secondes entre requêtes

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


# ─── Scraping matières du BAC ─────────────────────────────────────────────────

def scrape_matieres() -> list[dict]:
    print(f"\n[*] BAC : {BAC_URL}")
    soup = get_soup(BAC_URL)
    if not soup:
        return []

    matieres = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        parts = [p for p in href.split("/") if p]
        # /ar/bac/matiere → 3 segments
        if len(parts) == 3 and parts[:2] == ["ar", "bac"]:
            url = abs_url(href)
            if url in seen:
                continue
            seen.add(url)
            titre = a.get_text(strip=True)
            # Nombre de fichiers dans le bloc parent
            parent = a.find_parent()
            nb = ""
            if parent:
                txt = parent.get_text(" ", strip=True)
                if "عدد" in txt or "ملف" in txt:
                    nb = txt
            if titre:
                matieres.append({"matiere": titre, "url": url, "nb_fichiers": nb})

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
        # /ar/bac/matiere/filiere → 4 segments
        if (
            len(parts) == 4
            and parts[:2] == ["ar", "bac"]
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

def scrape_examens(fil: dict) -> list[dict]:
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
        data_id = item["data-id"]
        slug = enc(data_id)
        if not slug: continue

        # Déterminer le préfixe selon la classe CSS
        prefix = "/ar/annales/" # par défaut
        classes = item.get("class", [])
        for cls, pfx in routes.items():
            if cls in classes:
                prefix = pfx
                break
        
        url = abs_url(prefix + slug)
        if url in seen: continue
        seen.add(url)

        # Extraction du titre
        titre_el = item.find(class_="sujet-title")
        titre = titre_el.get_text(strip=True) if titre_el else "Sans titre"
        
        # Extraction de l'année (souvent dans meta-item)
        annee = None
        meta_items = item.find_all(class_="meta-item")
        for mi in meta_items:
            txt = mi.get_text(strip=True)
            if txt.isdigit() and 1900 < int(txt) < 2100:
                annee = int(txt)
                break
        
        # Si on n'a pas trouvé l'année, on cherche dans le titre
        if not annee:
            for w in titre.replace("-", " ").split():
                if w.isdigit() and 1900 < int(w) < 2100:
                    annee = int(w)
                    break

        # Visiter la page de détail pour trouver le PDF réel
        print(f"        • [Page] {titre[:40]}...")
        pdf_url = None
        detail_soup = get_soup(url)
        if detail_soup:
            # Chercher un lien direct vers un PDF
            pdf_link = detail_soup.find("a", href=lambda h: h and h.endswith(".pdf"))
            if pdf_link:
                pdf_url = abs_url(pdf_link["href"])
        
        examens.append({
            "titre":   titre,
            "url_page": url,
            "url_pdf":  pdf_url,
            "annee":   annee,
            "filiere": fil["filiere"],
            "matiere": fil["matiere"],
        })

    return examens


# ─── Main ─────────────────────────────────────────────────────────────────────

def main(
    max_matieres: int | None = 3,
    max_filieres: int | None = 3,
) -> list[dict]:

    all_data: list[dict] = []

    # 1. Matières
    matieres = scrape_matieres()
    if not matieres:
        print("❌ Aucune matière trouvée.")
        return all_data

    for mat in (matieres[:max_matieres] if max_matieres else matieres):
        print(f"\n[Matière] {mat['matiere']}")

        # 2. Filières
        filieres = scrape_filieres(mat)
        print(f"    → {len(filieres)} filières")

        for fil in (filieres[:max_filieres] if max_filieres else filieres):
            print(f"  [Filière] {fil['filiere']}")

            # 3. Examens / PDFs
            examens = scrape_examens(fil)
            print(f"      → {len(examens)} examens")
            for e in examens:
                print(f"        • [{e.get('annee','?')}] {e['titre'][:55]}")

            all_data.extend(examens)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {len(all_data)} examens → '{OUTPUT_FILE}'")
    return all_data


if __name__ == "__main__":
    main(
        max_matieres=3,   # None = toutes les matières
        max_filieres=3,   # None = toutes les filières
    )