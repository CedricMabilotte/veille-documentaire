"""_ua.py — User-Agent par domaine pour les parsers.
Leçon L70 (2026-10-07, HAL) : les anti-bots récents (Anubis) défient les
user-agents de navigateur (« Mozilla… ») mais laissent passer un robot qui se
déclare franchement (nom + URL de contact). Le réessai du 2026-11-20
(propositions/2026-11-20/sources-ci-reessai.md, lignes 2-4 et 9) montre le même
défi sur www.fian.org (RSS, WP REST, deep_html) et books.openedition.org :
notre UA « Mozilla/5.0 (compatible; LibraryBot/1.0) » déclenche Anubis depuis
une IP de datacenter (FIAN) ou même depuis la machine (OpenEdition Books), et
« LibraryBot/1.0 (+URL) » obtient le contenu.
Un parser appelle `headers_for(url)` au lieu de sa constante HEADERS : pour les
domaines listés il s'identifie en robot déclaré, pour les autres rien ne change.
"""
from __future__ import annotations
from urllib.parse import urlparse
# UA historique des parsers (inchangé pour les domaines non listés).
DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LibraryBot/1.0)"}
# UA de robot déclaré, identique à HONEST_HEADERS de scripts/watch.py (téléchargements).
HONEST_HEADERS = {"User-Agent": "LibraryBot/1.0 (+https://biblio.actitude.org/apropos.html)"}
# Domaines (et sous-domaines) où l'UA honnête est nécessaire. Ajouter un domaine
# ici seulement sur constat daté (réponse en défi avec l'UA par défaut, contenu
# avec l'UA honnête).
HONEST_UA_DOMAINS = (
    "hal.science",          # L70, 2026-10-07
    "archives-ouvertes.fr", # L70, 2026-10-07
    "fian.org",             # 2026-11-20, sources-ci-reessai.md lignes 2-4
    "openedition.org",      # 2026-11-20, sources-ci-reessai.md ligne 9
)
def headers_for(url: str, default: dict | None = None) -> dict:
    """Headers HTTP à utiliser pour `url` : HONEST_HEADERS si le domaine est
    listé dans HONEST_UA_DOMAINS, sinon `default` (ou DEFAULT_HEADERS)."""
    host = (urlparse(url).hostname or "").lower()
    if any(host == d or host.endswith("." + d) for d in HONEST_UA_DOMAINS):
        return HONEST_HEADERS
    return default if default is not None else DEFAULT_HEADERS
