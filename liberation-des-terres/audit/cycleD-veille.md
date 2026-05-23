# Cycle D — Audit de la veille et de la découverte

**Date :** 2026-05-23
**Angle :** veille et découverte (back-end — n'alourdit pas le site public)
**Mode :** lecture seule + exécution d'observation de `scripts/watch.py`
**Périmètre :** `scripts/watch.py`, `config/sources.yml`, `discovery/`, `.github/workflows/veille.yml`

---

## 1. Diagnostic — la veille actuelle

### 1.1 Ce qui fonctionne bien

- **Sobriété assumée et juste.** `urllib` + `html.parser` de la stdlib, PyYAML pour seule
  dépendance, aucune clé d'API. C'est cohérent avec le projet (site statique, petit corpus) et
  ça n'alourdit pas le site public — la veille écrit dans `discovery/`, hors `site/`.
- **Bonne hygiène réseau.** User-Agent identifiable, `Accept-Language`, `POLITE_DELAY` de 2 s,
  plafond de lecture à 2,5 Mo, `timeout`, et `fetch()` qui ne plante jamais (renvoie `None`).
  Le workflow CI a `continue-on-error: true` sur la veille : une source qui tombe ne bloque
  pas la publication. Sain.
- **Décision humaine préservée.** La veille « défriche » seulement ; la promotion d'un candidat
  en fiche reste manuelle. C'est le bon choix pour un annuaire critique et sourcé.
- **Sortie double JSON + Markdown** lisible, triée, datée. Le `.md` est directement
  consultable dans le dépôt.

### 1.2 Faiblesses constatées

Le run du 2026-05-23 est révélateur : **3 candidats sur 10 sources, dont 2 déjà connus et
1 seul « nouveau »** — et ce candidat unique est un appel de financement participatif
(« Complément d'acquisition Ferme de la Coccinelle »), pas un montage de libération des terres
qualifiable. La veille tourne quasiment à vide. Causes :

1. **Scoring trop pauvre et trop binaire.** `score_candidate()` ne compte que des occurrences
   de mots-clés *dans le texte du lien* (`<a>…</a>`), tronqué de fait à quelques mots. Une
   page de ferme exemplaire dont le lien dit juste « En savoir plus » ou « Ferme de X »
   scorera 0–1 et sera écartée. Le seuil `score < 2` élimine alors l'essentiel du gisement.
   Le texte d'ancre est un signal beaucoup trop maigre.

2. **Aucune analyse de la page candidate elle-même.** La veille ne récupère jamais le contenu
   de la page pointée — elle juge un lien sur son seul libellé. Or les mots-clés forts
   (« démembrement », « nue-propriété », « fonds de dotation ») apparaissent dans le *corps*
   des pages, pas dans les ancres.

3. **Déduplication grossière.** `known_urls()` ne compare que le **domaine** (`netloc`). Tout
   lien `terredeliens.org/...` est marqué `deja_reference` même si c'est une ferme jamais
   fichée — alors qu'une seule fiche `reseau-terre-de-liens` couvre ce domaine. Inversement,
   deux URL différentes du même lieu ne sont pas rapprochées. La dédup est à la fois trop
   large (masque des nouveautés réelles) et trop faible (pas de dédup par URL exacte ni par
   candidats déjà vus lors des passes précédentes).

4. **Pas de mémoire entre passes.** Chaque run écrit `candidats-AAAA-MM-JJ.json` et ignore
   les fichiers précédents. Un même candidat ressort chaque semaine ; un candidat écarté puis
   réapparu n'est pas détecté ; `discovery/` grossit sans consolidation.

5. **Sources non qualifiées / non suivies.** `sources.yml` liste 10 portails — tous sérieux —
   mais sans champ de santé (dernière réussite, dernier scan) ni typage (page d'actu vs
   annuaire vs page conceptuelle). Une source morte ou refondue passe inaperçue. Plusieurs
   sources visent une page d'accueil dont la liste de liens change peu : faible rendement.

6. **Angles morts non outillés.** Le `cycleA-corpus.md` montre un travail d'angles morts fait
   **à la main** (habitat coopératif absent à 100 %, périurbain, SCIC régionales, foncier
   solidaire de logement). La veille ne sait rien du corpus : elle ne dit jamais « la région X
   ou le montage Y est sous-représenté ». C'est l'amélioration la plus utile et elle est
   simple : toute la donnée existe déjà dans les fiches YAML.

7. **`categorie_probable` non exploitée pour qualifier.** Elle est recopiée dans le candidat
   mais n'influence ni le score ni le tri.

---

## 2. Recommandations priorisées

Principe directeur : **rester dans l'esprit du projet** — stdlib only, pas de service externe,
sortie dans `discovery/`, décision humaine finale. Aucune reco ci-dessous ne touche `site/`.

### P1 — Analyser la page candidate, pas seulement l'ancre *(impact fort, effort moyen)*

Le gain le plus net. Pour les liens passant un premier filtre faible (ancre score ≥ 1),
récupérer la page pointée (en réutilisant `fetch()` + `POLITE_DELAY` déjà en place) et scorer
sur le **texte de la page** : `<title>`, `<meta name="description">` et premiers ~2000
caractères de corps. Plafonner le nombre de pages approfondies par passe (p. ex. 40) pour
garder le run court.

Un extracteur de texte minimal réutilisant `HTMLParser` (mêmes outils que `LinkHarvester`) :

```python
class TextExtractor(HTMLParser):
    """Récupère <title>, meta description et le texte visible (hors script/style)."""
    SKIP = {"script", "style", "noscript", "svg"}
    def __init__(self):
        super().__init__()
        self.title, self.meta_desc = "", ""
        self._chunks, self._skip, self._in_title = [], 0, False
    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            a = dict(attrs)
            if a.get("name", "").lower() in ("description", "og:description"):
                self.meta_desc = a.get("content", "")
    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        elif tag == "title":
            self._in_title = False
    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip:
            self._chunks.append(data)
    def text(self, limit=2000):
        body = re.sub(r"\s+", " ", " ".join(self._chunks)).strip()
        return f"{self.title} {self.meta_desc} {body[:limit]}"
```

### P2 — Scoring qualifié et pondéré *(impact fort, effort faible)*

Remplacer le comptage binaire par un score pondéré qui distingue les signaux. Idée :
mots-clés de source = 1 pt, mots-clés transverses = 2 pts, mots-clés « forts » = 3 pts,
présence d'une **forme juridique attendue** (fondation, fonds de dotation, SCIC, GFA, bail
emphytéotique…) = 2 pts. Ajouter un petit jeu de **signaux négatifs** pour écarter le bruit
financier/marchand (« faire un don », « objectif de financement », « à vendre », « SCI
familiale »), qui retranchent des points. Le candidat « Ferme de la Coccinelle » du run actuel
serait ainsi rétrogradé.

```python
FORMES = ["fondation", "fonds de dotation", "scic", "gfa", "bail emphytéotique",
          "bail réel solidaire", "coopérative d'habitants", "société civile"]
NEGATIFS = ["faire un don", "objectif de financement", "collecte", "à vendre",
            "investissez", "rendement", "sci familiale"]

def score_candidate(text, source_kw, transverse_kw, strong_kw):
    t = normalise(text)
    score, hits = 0, []
    for kw in source_kw or []:
        if normalise(kw) in t: score += 1; hits.append(kw)
    for kw in transverse_kw or []:
        if normalise(kw) in t: score += 2; hits.append(kw)
    for kw in strong_kw:
        if kw in t: score += 3; hits.append(kw)
    for f in FORMES:
        if f in t: score += 2; hits.append(f)
    for n in NEGATIFS:
        if n in t: score -= 2
    return score, sorted(set(hits))
```

Les `strong_kw` peuvent être tirés de `sources.yml` (`mots_cles_transverses`) plutôt que
codés en dur dans `watch.py` — voir P5.

### P3 — Détecteur d'angles morts *(impact fort, effort faible — la reco phare)*

Petit module qui lit le corpus existant (`lieux/`, `porteurs/`, `usufruitiers/`) et compte la
couverture par **région** (`localisation.region`) et par **type de montage**
(`montage.type`). Il produit dans `discovery/` un court rapport listant les dimensions
sous-représentées, et — surtout — il sert à **bonifier le score** des candidats qui touchent
un angle mort. Toute la donnée nécessaire est déjà dans les fiches.

```python
from collections import Counter

def corpus_profile():
    regions, montages = Counter(), Counter()
    for folder in ("lieux", "porteurs", "usufruitiers"):
        for fp in (ROOT / folder).glob("*.yml"):
            data = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
            loc = data.get("localisation") or {}
            if loc.get("region"):
                regions[loc["region"]] += 1
            m = data.get("montage") or {}
            if m.get("type"):
                montages[m["type"]] += 1
    return regions, montages

def blind_spots(regions, montages, all_regions, all_montages):
    """Régions/montages absents ou faiblement couverts (≤ 1 fiche)."""
    faibles_r = [r for r in all_regions if regions.get(r, 0) <= 1]
    faibles_m = [m for m in all_montages if montages.get(m, 0) <= 1]
    return faibles_r, faibles_m
```

Un candidat dont la page mentionne une région ou un montage sous-représenté reçoit un
**bonus de score** (p. ex. +2) et un tag `angle_mort`. Le rapport `discovery/angles-morts.md`
devient un outil de pilotage éditorial — c'est exactement ce que `cycleA-corpus.md` a fait à
la main. La liste de référence des régions/montages se tire de `concepts.yml` (bloc
`montages`) et d'une liste figée des 13 régions métropolitaines.

### P4 — Mémoire des passes + déduplication plus fine *(impact moyen, effort faible)*

Maintenir un `discovery/_seen.json` : pour chaque URL candidate déjà vue, la date de première
détection, le dernier score, le statut (`nouveau` / `revu` / `promu` / `ignore`). Bénéfices :

- ne pas re-signaler chaque semaine les mêmes liens en tête de rapport ;
- distinguer les **vraies nouveautés** (URL jamais vue) des récurrences ;
- permettre d'ignorer durablement un candidat écarté manuellement (lui mettre `ignore`).

Et corriger la déduplication contre les fiches : comparer non pas le `netloc` seul mais
**l'URL normalisée** (sans `?utm_*`, sans fragment, sans `/` final, `www.` retiré), et
indexer **toutes** les URL des fiches — champ `url:` *et* bloc `sources:` —, pas seulement
`url:`. Garder en parallèle un set de domaines, mais l'utiliser pour un signal nuancé
(`domaine_connu` ≠ `fiche_existante`) plutôt que pour masquer le candidat.

```python
def norm_url(u):
    p = urlparse(u)
    netloc = p.netloc.lower().removeprefix("www.")
    path = p.path.rstrip("/") or "/"
    return f"{netloc}{path}"

def known_urls():
    exact, domains = set(), set()
    for folder in ("lieux", "porteurs", "usufruitiers", "modeles"):
        for fp in (ROOT / folder).glob("*.yml"):
            data = yaml.safe_load(fp.read_text(encoding="utf-8")) or {}
            urls = [data.get("url")] + [
                s.get("url") for s in (data.get("sources") or []) if s.get("url")]
            for u in filter(None, urls):
                exact.add(norm_url(str(u)))
                domains.add(urlparse(str(u)).netloc.lower().removeprefix("www."))
    return exact, domains
```

### P5 — Qualifier et suivre les sources *(impact moyen, effort faible)*

Dans `sources.yml`, sans usine à gaz :

- Ajouter un champ `type:` par source (`actualites`, `annuaire`, `conceptuel`) — informatif,
  utile pour pondérer plus tard.
- Sortir les mots-clés « forts » du code (`watch.py` les a en dur l. 115-116) vers
  `sources.yml` sous un bloc `mots_cles_forts:`, pour que toute la connaissance métier vive
  dans la config.
- Élargir prudemment de quelques sources qui adressent les angles morts identifiés en
  cycle A : **Habicoop** (`habicoop.fr` — habitat coopératif, absent), **Le Labo de l'ESS**
  (`lelabo-ess.org` — déjà cité comme source de fiches), **RECit / réseau des écolieux**,
  **Foncière Chênelet**, **Eau du Bassin Rennais / Terres de Sources** (périurbain, captages).
  S'en tenir à ~15 sources : c'est un petit annuaire.
- Écrire un `discovery/sources-sante.md` à chaque passe : par source, dernier scan, succès/
  échec, nombre de candidats. Une source en échec deux passes de suite est signalée. Trivial
  à produire à partir des données déjà collectées par `main()`.

### P6 — Consolidation et hygiène de `discovery/` *(impact faible, effort faible)*

- Maintenir un `discovery/index.md` (ou `derniers-candidats.md`) toujours à jour pointant la
  dernière passe + le rapport d'angles morts, plutôt que d'accumuler des fichiers datés
  jamais relus.
- Conserver les `candidats-AAAA-MM-JJ.json` (traçabilité) mais éventuellement purger les
  `.md` datés au-delà de N passes — ils sont régénérables depuis le JSON.
- `discovery/` est déjà committé par le workflow ; rien à changer côté CI, le périmètre
  `git add discovery/ site/` reste correct.

---

## 3. Ce qu'il ne faut PAS faire (garde-fous)

- **Pas de crawl récursif profond.** Suivre les liens de 2e niveau transformerait la veille
  en crawler ; rester à : pages sources → liens → page candidate (1 saut), plafonné.
- **Pas d'API payante, pas de LLM dans le pipeline.** La qualification fine reste humaine ;
  `watch.py` ne fait que pré-trier et signaler.
- **Pas de base de données.** Quelques fichiers JSON/MD dans `discovery/` suffisent au volume.
- **Ne rien ajouter à `site/`.** Toute la veille reste back-end ; le poids du site public est
  inchangé.

---

## 4. Récapitulatif priorisé

| Priorité | Amélioration | Impact | Effort | Touche `site/` ? |
|----------|--------------|--------|--------|------------------|
| **P1** | Scorer le contenu de la page candidate, pas que l'ancre | Fort | Moyen | Non |
| **P2** | Scoring pondéré + signaux négatifs (anti-bruit) | Fort | Faible | Non |
| **P3** | Détecteur d'angles morts (régions / montages sous-représentés) + bonus de score | Fort | Faible | Non |
| **P4** | Mémoire des passes (`_seen.json`) + dédup par URL normalisée, fiches *et* sources | Moyen | Faible | Non |
| **P5** | Qualifier `sources.yml` (type, mots-clés forts en config), `sources-sante.md`, +5 sources angles morts | Moyen | Faible | Non |
| **P6** | `discovery/index.md` consolidé, hygiène des fichiers datés | Faible | Faible | Non |

**Ordre de mise en œuvre conseillé :** P2 d'abord (gain immédiat, quasi sans risque), puis P1
(qui rend P2 réellement efficace), puis P3 (la reco la plus structurante pour l'éditorial),
puis P4–P6 en finition. L'ensemble reste réalisable dans le même fichier `watch.py` enrichi,
sans nouvelle dépendance.
