# Catalogue de sources pour la veille documentaire

> Document de référence réutilisable pour les agents de veille thématiques
> (communs, propriété d'usage, libération des terres, paysannerie, anti-autoritarisme).
>
> Dernière mise à jour : 2026-05-15
> Validé sur scraper `requests + BeautifulSoup` (détection d'extensions `.pdf .epub .txt .doc .docx`)

---

## 1. Méthodologie d'évaluation d'une source

Avant d'ajouter une URL à `config/sources.yml`, valider qu'elle expose des documents en HTML statique :

```bash
UA="Mozilla/5.0 (compatible; LibraryBot/1.0)"
URL="https://example.com/page-a-tester"
curl -s -L -A "$UA" --max-time 20 "$URL" \
  | grep -oiE 'href="[^"]+\.(pdf|epub|txt|docx?)"' \
  | wc -l
```

- Résultat ≥ 5 : exploitable directement → ajouter à `sources.yml`
- Résultat 1-4 : potentiellement intéressant, regarder les patterns d'URL (`/IMG/pdf/`, `/files/`, etc.)
- Résultat 0 : trois causes possibles :
  1. **JS-rendering** : page chargée en client side (React, Vue, Angular). Nécessite Playwright/Selenium.
  2. **Crawl 2-niveaux** : la page liste des articles, mais les PDFs ne sont accessibles que via les pages-articles individuelles. Solution : enrichir `find_documents()` pour suivre les liens internes.
  3. **API uniquement** : le contenu existe mais n'est exposé que via une API (HAL, Archive.org, OAI-PMH). Solution : ajouter un parser dédié.

---

## 2. Sources validées (HTML statique direct)

### Francophones — infokiosques.net

**Le seul site francophone vraiment scrapable en HTML statique.** Multi-milliers de brochures libertaires, anarchistes, antifascistes, écologie radicale, queer/féminisme, prison/répression, etc.

Pages les plus riches (validé par probe ; chiffres = nombre de liens `.pdf` distincts trouvés) :

| URL                                              | Nb docs | Thème (lettre alphabétique ou rubrique) |
|--------------------------------------------------|---------|-----------------------------------------|
| `https://infokiosques.net/spip.php?rubrique5`    | 290     | A — texts commençant par A              |
| `https://infokiosques.net/spip.php?rubrique7`    | 273     | C — Communauté, Communisation, etc.     |
| `https://infokiosques.net/spip.php?rubrique22`   | 236     | Rubrique thématique                     |
| `https://infokiosques.net/spip.php?rubrique8`    | 174     | Index alphabétique                      |
| `https://infokiosques.net/spip.php?rubrique9`    | 134     | Index alphabétique                      |
| `https://infokiosques.net/spip.php?rubrique19`   | 134     | Rubrique thématique                     |
| `https://infokiosques.net/spip.php?rubrique24`   | 124     | Rubrique thématique                     |
| `https://infokiosques.net/spip.php?rubrique11`   | 115     | T — Terre, Travail, etc.                |
| `https://infokiosques.net/spip.php?rubrique13`   | 93      | Index alphabétique                      |
| `https://infokiosques.net/spip.php?rubrique20`   | 86      | Rubrique thématique                     |
| `https://infokiosques.net/spip.php?rubrique18`   | 74      | L — Libération, Lutte, etc.             |
| `https://infokiosques.net/spip.php?rubrique27`   | 51      | Rubrique thématique                     |
| `https://infokiosques.net/spip.php?rubrique21`   | 48      | O — Occupation, Organisation, etc.      |
| `https://infokiosques.net/`                      | 47      | Accueil — nouveautés                    |
| `https://infokiosques.net/spip.php?rubrique26`   | 39      | Rubrique thématique                     |
| `https://infokiosques.net/spip.php?rubrique31`   | 35      | Rubrique thématique                     |
| `https://infokiosques.net/spip.php?rubrique38`   | 16      | Rubrique thématique                     |
| `https://infokiosques.net/spip.php?rubrique4`    | 10      | 0-9 — texts commençant par chiffre      |

**Conseil** : si tu cherches large, prends 3-5 rubriques alphabétiques (couvrent l'ensemble du fonds) ; si tu cherches ciblé, identifie d'abord les rubriques thématiques pertinentes en consultant le site.

### Germanophones (avec section anglophone) — boell.de

Heinrich-Böll-Stiftung (fondation politique allemande proche des Verts). Publications sur : communs (Commons), agriculture, foncier, démocratie, écologie, féminisme, géopolitique. Pagination ultra-fiable.

| URL                                          | Nb docs | Note                       |
|----------------------------------------------|---------|----------------------------|
| `https://www.boell.de/de/publikationen`      | 94      | Page d'accueil DE          |
| `?page=1..60`                                | 70-110/page | Pagination DE          |
| `https://www.boell.de/en/publications`       | 49      | Page d'accueil EN          |
| `?page=1..30`                                | 24-60/page  | Pagination EN          |

**Conseil** : pour un agent multilingue, ajouter `?page=1`, `?page=5`, `?page=10` sur `de/publikationen` et `en/publications`. Le contenu allemand est plus volumineux mais les keywords anglais matchent dessus aussi (titres mixtes).

### Hispanophones / Latino-américains

**Aucun site validé en HTML statique pur.** Tous les portails majeurs (Portal Oaca, alasbarricadas, biblioweb sindominio, Anarkismo, Enlace Zapatista, MST Brésil, Via Campesina, Rebelión, La Haine, Lavaca, Desinformemonos) sont :
- Soit en JS-rendering (SPA WordPress modernes)
- Soit en crawl 2-niveaux (PDFs accessibles uniquement via la page-article individuelle)
- Soit en vitrine éditoriale (livres papier à acheter, pas de PDFs libres)

Pour débloquer ce corpus, voir §4 ci-dessous (API + crawl 2-niveaux).

---

## 3. Sites identifiés mais non scrapables (nécessitent extension)

### Crawl 2-niveaux (suivre les liens d'articles depuis les listes)

Ces sites ont des PDFs réels, mais ils ne sont pas listés sur les pages d'index — il faut visiter chaque page-article puis extraire le PDF. Une simple extension de `find_documents()` (suivre `<a>` qui ne sont pas des PDFs mais qui mènent à des pages contenant des PDFs) débloquerait :

- **theanarchistlibrary.org** — corpus anglophone gigantesque ; les PDFs sont sur les pages texte (`/library/<slug>.pdf`, `.a4.pdf`, `.lt.pdf`, `.epub`). **Alternative supérieure : OPDS feed `https://theanarchistlibrary.org/opds`** (XML standardisé)
- **libcom.org/library** — articles HTML, certains exposent `libcom.org/files/*.pdf`
- **crimethinc.com/library** + `/books` + `/texts` — beaucoup de PDFs en `/zines/...`
- **sproutdistro.com/catalog/** — PDFs sur `files.sproutdistro.com/*.pdf`
- **cras31.info** — pattern `/IMG/pdf/` sur les pages-articles (SPIP)
- **kropotkine.cgt-energie.org**, **federation-anarchiste.org** — idem
- **portaloaca.com** — WordPress, PDFs dans `/wp-content/uploads/YYYY/MM/`

### JS-rendering (nécessite Playwright/Selenium)

- **iied.org**, **tni.org**, **fian.org** — instituts de recherche, listes paginées par JS
- **commonsstrategies.org**, **onthecommons.org**, **degrowth.info** — SPA
- **viacampesina.org** (toutes versions linguistiques)
- **theanarchistlibrary.org** (lui aussi rendu partiellement par JS — mais l'OPDS feed contourne)

### APIs publiques (préférables à Playwright pour la stabilité)

- **Archive.org** — `https://archive.org/advancedsearch.php?q=subject:%22anarchism%22+AND+mediatype:texts&fl[]=identifier&fl[]=title&fl[]=year&output=json&rows=200`. Collections suggérées : `folksonomy_anarchism`, `peasantmovements`, `commons_studies`
- **HAL Science** — `https://api.archives-ouvertes.fr/search/?q=communs+fonciers&fl=title_s,uri_s,fileMain_s&wt=json&rows=100` (téléchargement direct via `fileMain_s`)
- **OpenEdition Books** — `https://api.openedition.org/`
- **DOAB (Directory of Open Access Books)** — API JSON, contient des ouvrages sur les communs
- **Persée** — OAI-PMH disponible
- **FAO documents** — `https://www.fao.org/documents/api/` (food sovereignty / land rights)
- **theanarchistlibrary.org OPDS** — `https://theanarchistlibrary.org/opds` (catalogue complet structuré)

---

## 4. Mots-clés multilingues (template)

Pour tout agent de veille thématique, dupliquer la liste de mots-clés en FR/EN/ES augmente significativement le rappel sans dégrader la précision (Claude scoring tolère le multilingue).

### Thématique : communs, terres, paysannerie

| Français                     | English                            | Español                            |
|------------------------------|------------------------------------|------------------------------------|
| communs                      | commons                            | comunes / bienes comunes           |
| propriété d'usage            | usufruct / use rights              | usufructo / derecho de uso         |
| fonds de dotation            | endowment fund                     | fondo de dotación                  |
| libération des terres        | land liberation / land back        | liberación de la tierra            |
| accès à la propriété         | property access                    | acceso a la propiedad              |
| sans-terre                   | landless                           | sin tierra                         |
| paysans libres               | free peasants / free farmers       | campesinos libres                  |
| cosaques                     | Cossacks                           | cosacos                            |
| collectif d'habitants        | residents' collective              | colectivo de habitantes            |
| communauté                   | community                          | comunidad                          |
| paysannerie                  | peasantry                          | campesinado                        |
| vivrier / vivrière           | subsistence farming                | agricultura de subsistencia        |
| propriété privée             | private property                   | propiedad privada                  |

Concepts complémentaires utiles à ajouter selon le contexte : `food sovereignty / soberanía alimentaria / souveraineté alimentaire`, `agroecology / agroecología`, `commoning`, `enclosure`, `tierra y libertad`, `latifundio`, `minifundio`, `réforme agraire / agrarian reform / reforma agraria`, `ZAD`, `Zomia`, `usos colectivos`.

---

## 5. Roadmap d'extension

Par ordre de ROI décroissant pour étendre le corpus de l'agent :

1. **Ajouter plusieurs rubriques infokiosques** dans `sources.yml` (10 min, +1500 docs accessibles)
2. **Étendre `find_documents()` pour suivre 1 niveau** (1-2h, débloque libcom, crimethinc, sproutdistro, cras31, federation-anarchiste, portaloaca) — corpus FR/EN/ES enrichi
3. **Intégrer l'OPDS feed de theanarchistlibrary.org** (3-4h, débloque ~10000 textes anarchistes EN+ES+FR+IT+DE)
4. **Ajouter un parser archive.org API** (2-3h, débloque collections `folksonomy_anarchism` etc.)
5. **Ajouter un parser HAL API** (2h, débloque académique francophone)
6. **Mode Playwright pour les sites SPA** (1 journée, débloque viacampesina, commonsstrategies, etc.) — gros effort, à différer

---

## 6. Anti-pattern à éviter

- **Pages de recherche** (Persée `/search`, HAL `/search`, OpenEdition `/search`) : presque toujours rendues en JS, retournent 0 docs au scraper. Préférer les URLs canoniques (collection, numéro, article) ou l'API.
- **Vitrines d'éditeurs** (Amsterdam, Entremonde, Libertalia, La Fabrique) : pas de PDFs libres, contenu payant.
- **Wikis publics** (P2P Foundation, Wikipedia) : contenu en HTML inline, pas de PDFs.
- **Mégasites institutionnels** (FAO front page, ONU, OMS) : trop d'JS et trop de cookies, préférer leurs APIs documentaires.
- **Sites WordPress modernes** : WordPress 6+ utilise massivement le block editor + JS. Tester avant d'inclure.

---

## 7. Maintenance

Re-vérifier ce catalogue tous les 3-6 mois :

```bash
# Probe rapide des sources actuelles
UA="Mozilla/5.0 (compatible; LibraryBot/1.0)"
while IFS= read -r url; do
  count=$(curl -s -L -A "$UA" --max-time 15 "$url" \
    | grep -oiE 'href="[^"]+\.(pdf|epub|txt|docx?)"' | wc -l)
  printf "[%3d docs] %s\n" "$count" "$url"
done < <(grep -oE 'https?://[^"]+' config/sources.yml)
```

Si une source descend < 5 docs, vérifier si elle a basculé en JS ou si elle a été restructurée.

---

*Catalogue généré par l'agent de veille — réutilisable pour tout nouveau projet de veille thématique.*
