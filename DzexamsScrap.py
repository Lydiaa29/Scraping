"""
Scraper pour dzexams.com
Extrait les examens scolaires algériens (BEM, BAC, 5ème, etc.)

Dépendances :
    pip install requests beautifulsoup4 lxml
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import os
from urllib.parse import urljoin, urlparse

# ─── Configuration ────────────────────────────────────────────────────────────

BASE_URL = "https://www.dzexams.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-DZ,fr;q=0.9,ar;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
}

DELAY       = 2.0   # secondes entre chaque requête
TIMEOUT     = 20    # timeout par requête (secondes)
MAX_RETRIES = 3     # tentatives en cas d'échec

OUTPUT_FILE = "dzexams_data.json"
PDF_DIR     = "pdfs"


# ─── Session partagée ─────────────────────────────────────────────────────────

session = requests.Session()
session.headers.update(HEADERS)


# ─── Fonctions utilitaires ────────────────────────────────────────────────────

def get_page(url: str) -> BeautifulSoup | None:
    """Télécharge une page avec retry et retourne un BeautifulSoup."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"    → GET {url}  (tentative {attempt}/{MAX_RETRIES})")
            resp = session.get(url, timeout=TIMEOUT)
            resp.raise_for_status()
            print(f"    ✓ HTTP {resp.status_code}  ({len(resp.content)} octets)")
            time.sleep(DELAY)
            return BeautifulSoup(resp.text, "lxml")
        except requests.exceptions.Timeout:
            print(f"    [TIMEOUT] tentative {attempt}")
        except requests.exceptions.ConnectionError as e:
            print(f"    [CONNEXION REFUSÉE] {e}")
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response is not None else 0
            print(f"    [HTTP ERREUR] {e}")
            if code in (403, 429):
                wait = 10 * attempt
                print(f"    ⏳ Anti-bot détecté, attente {wait}s …")
                time.sleep(wait)
        except requests.RequestException as e:
            print(f"    [ERREUR] {e}")

        time.sleep(DELAY * attempt)  # backoff

    print(f"    ✗ Abandon après {MAX_RETRIES} tentatives : {url}")
    return None


def absolute_url(href: str) -> str:
    """Convertit un lien relatif en URL absolue."""
    return urljoin(BASE_URL, href)


# ─── Scraping de la page d'accueil ────────────────────────────────────────────

def scrape_homepage() -> list[dict]:
    """
    Récupère les catégories / niveaux scolaires depuis la page d'accueil.
    Retourne une liste de dicts {title, url}.
    """
    print(f"\n[*] Page d'accueil : {BASE_URL}")
    soup = get_page(BASE_URL)
    if not soup:
        print("[!] Impossible d'atteindre la page d'accueil.")
        return []

    categories: list[dict] = []

    for a in soup.find_all("a", href=True):
        href = str(a["href"])
        full_url = absolute_url(href)

        if (
            urlparse(full_url).netloc == "www.dzexams.com"
            and href not in ("/", "#", "")
            and not href.startswith("http://")
            and not href.startswith("mailto:")
            and not href.startswith("javascript:")
        ):
            title = a.get_text(strip=True)
            if title and len(title) > 2:
                entry = {"title": title, "url": full_url}
                if entry not in categories:
                    categories.append(entry)

    print(f"    → {len(categories)} liens trouvés")
    return categories


# ─── Scraping d'une page de liste d'examens ───────────────────────────────────

def scrape_exam_list(url: str) -> list[dict]:
    """
    Scrape une page listant des examens.
    Retourne une liste de dicts {title, year, url, pdf_url, source_page}.
    """
    soup = get_page(url)
    if not soup:
        return []

    exams: list[dict] = []

    for item in soup.find_all(["article", "div", "li"]):
        link = item.find("a", href=True)
        if not link:
            continue

        href = str(link["href"])
        full_url = absolute_url(href)

        if not (href.endswith(".pdf") or "/examen" in href or "/exam" in href):
            continue

        title = link.get_text(strip=True) or item.get_text(strip=True)[:80]

        exam: dict = {
            "title": title.strip(),
            "url": full_url,
            "pdf_url": full_url if href.endswith(".pdf") else None,
            "source_page": url,
        }

        for word in item.get_text().split():
            if word.isdigit() and 1990 < int(word) < 2100:
                exam["year"] = int(word)
                break

        exams.append(exam)

    return exams


# ─── Scraping d'une page d'examen individuelle ────────────────────────────────

def scrape_exam_page(url: str) -> dict:
    """Scrape une page d'examen individuelle."""
    soup = get_page(url)
    if not soup:
        return {}

    data: dict = {"url": url}

    h1 = soup.find("h1")
    if h1:
        data["title"] = h1.get_text(strip=True)

    for a in soup.find_all("a", href=True):
        if str(a["href"]).endswith(".pdf"):
            data["pdf_url"] = absolute_url(str(a["href"]))
            break

    main = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
    if main:
        data["text_content"] = main.get_text(separator="\n", strip=True)[:2000]

    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        data["description"] = str(meta_desc.get("content", ""))

    return data


# ─── Téléchargement de PDF (optionnel) ────────────────────────────────────────

def download_pdf(pdf_url: str, dest_dir: str = PDF_DIR) -> str | None:
    """Télécharge un PDF et le sauvegarde localement."""
    os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(urlparse(pdf_url).path) or "exam.pdf"
    filepath = os.path.join(dest_dir, filename)

    if os.path.exists(filepath):
        print(f"    [SKIP] {filename} déjà téléchargé")
        return filepath

    try:
        resp = session.get(pdf_url, timeout=30, stream=True)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
        time.sleep(DELAY)
        print(f"    [PDF] Sauvegardé : {filepath}")
        return filepath
    except requests.RequestException as e:
        print(f"    [ERREUR PDF] {pdf_url} → {e}")
        return None


# ─── Scraper principal ────────────────────────────────────────────────────────

def main(
    max_categories: int = 5,
    max_exams_per_category: int = 10,
    download_pdfs: bool = False,
) -> list[dict]:
    all_data: list[dict] = []

    categories = scrape_homepage()
    if not categories:
        print("\n❌ Aucune catégorie trouvée. Le site est peut-être inaccessible.")
        return all_data

    categories = categories[:max_categories]

    for cat in categories:
        print(f"\n[Catégorie] {cat['title']} — {cat['url']}")

        exams = scrape_exam_list(cat["url"])
        exams = exams[:max_exams_per_category]
        print(f"    → {len(exams)} examens trouvés")

        for exam in exams:
            print(f"  [Examen] {exam['title'][:60]}")

            if exam["url"] and not exam["url"].endswith(".pdf"):
                details = scrape_exam_page(exam["url"])
                exam.update(details)

            if download_pdfs and exam.get("pdf_url"):
                exam["local_pdf"] = download_pdf(str(exam["pdf_url"]))

            all_data.append(exam)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Terminé ! {len(all_data)} examens sauvegardés dans '{OUTPUT_FILE}'")
    return all_data


# ─── Point d'entrée ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    main(
        max_categories=5,
        max_exams_per_category=10,
        download_pdfs=False,
    )