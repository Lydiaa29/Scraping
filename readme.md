# Dzexams Scraper 🎓

Un scraper Python professionnel et robuste pour extraire les sujets d'examens et annales du site [dzexams.com](https://www.dzexams.com).

## ✨ Fonctionnalités

- **Scraping Hiérarchique** : Récupère les sujets par niveau (Primaire, Moyen, Secondaire), matière et filière.
- **Téléchargement Automatique** : Télécharge les fichiers PDF et les organise dans une structure de dossiers logique.
- **Extraction Intelligente** : Décode les identifiants dynamiques du site pour obtenir les liens directs.
- **Gestion du Débit** : Inclut des délais entre les requêtes pour respecter le serveur.
- **Interface CLI** : Paramétrable via des arguments en ligne de commande.

## 🚀 Installation

1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/Lydiaa29/Scraping.git
   cd Scraper
   ```

2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## 🛠 Utilisation

Pour lancer le scraper avec les paramètres par défaut (tous les niveaux) :
```bash
python DzexamsScrap.py
```

### Options avancées

Vous pouvez cibler des niveaux spécifiques ou limiter le nombre de résultats pour un test rapide :

```bash
# Scraper uniquement le 5ème Primaire et le BAC
python DzexamsScrap.py --levels 5ap bac

# Faire un test rapide (1ère matière, 1ère filière)
python DzexamsScrap.py --levels 1am --max-matieres 1 --max-filieres 1

# Changer le délai entre les requêtes (en secondes)
python DzexamsScrap.py --delay 2.0
```

### Arguments disponibles :
- `--levels` : Liste des niveaux à scraper (ex: `1ap 2ap bac`).
- `--delay` : Délai entre les requêtes (défaut: 0.5s).
- `--output` : Nom du fichier JSON de sortie (défaut: `dzexams_full.json`).
- `--max-matieres` : Limiter le nombre de matières par niveau.
- `--max-filieres` : Limiter le nombre de filières par matière.

## 📂 Structure des Téléchargements

Les fichiers sont organisés comme suit :
```text
downloads/
└── [Niveau]/
    └── [Matière]/
        └── [Filière]/
            └── [Année]_[Titre].pdf
```

## ⚖️ Avertissement Légal
Ce projet est destiné à un usage éducatif. Assurez-vous de respecter les conditions d'utilisation de `dzexams.com` et de ne pas surcharger leurs serveurs. L'auteur n'est pas responsable de l'utilisation faite de ce script.
