# Source Health Report

*Généré le 2026-05-15 14:57 UTC*

## Vue d'ensemble

- Total de sources recensées : **22**
- En production (`active`)    : **3**
- Validées (`validated`)      : **6**
- Nécessitent parser dédié    : **10**
- JS-only (Playwright requis) : **3**
- Rejetées                    : **0**

## Performance du dernier run

*Date : 2026-05-15_13-44*

| Source | Trouvés | Téléchargés | Score moyen |
|--------|---------|-------------|-------------|
| Infokiosques.net — brochures (lettre A) | 290 | 196 | 6.2/10 |
| Infokiosques.net — nouveautés | 47 | 36 | 6.7/10 |

## ✅ Actives (en production) (3)

- **Infokiosques — nouveautés** [fr, type=html] — 47 docs (probe: 2026-05-15)
  - `https://infokiosques.net/`
  - Thèmes : anarchisme, contre-culture, divers
  - 📝 Page d'accueil — nouvelles brochures ajoutées
- **Infokiosques — index A** [fr, type=html] — 290 docs (probe: 2026-05-15)
  - `https://infokiosques.net/spip.php?rubrique5`
  - Thèmes : anarchisme, index_alphabetique
- **Infokiosques — index C** [fr, type=html] — 273 docs (probe: 2026-05-15)
  - `https://infokiosques.net/spip.php?rubrique7`
  - Thèmes : anarchisme, index_alphabetique

## 🟢 Validées (prêtes à activer) (6)

- **Infokiosques — index T** [fr, type=html] — 115 docs (probe: 2026-05-15)
  - `https://infokiosques.net/spip.php?rubrique11`
  - Thèmes : anarchisme, index_alphabetique, terres
- **Infokiosques — index L** [fr, type=html] — 74 docs (probe: 2026-05-15)
  - `https://infokiosques.net/spip.php?rubrique18`
  - Thèmes : anarchisme, index_alphabetique, libération
- **Infokiosques — rubrique thématique 22** [fr, type=html] — 236 docs (probe: 2026-05-15)
  - `https://infokiosques.net/spip.php?rubrique22`
  - Thèmes : anarchisme
- **Infokiosques — rubrique thématique 24** [fr, type=html] — 124 docs (probe: 2026-05-15)
  - `https://infokiosques.net/spip.php?rubrique24`
  - Thèmes : anarchisme
- **Heinrich-Böll-Stiftung — publications EN** [en, type=html] — 49 docs (probe: 2026-05-15)
  - `https://www.boell.de/en/publications`
  - Thèmes : communs, écologie, démocratie, foncier
  - 📝 Pagination ?page=N jusqu'à 30+
- **Heinrich-Böll-Stiftung — publications DE** [de, type=html] — 94 docs (probe: 2026-05-15)
  - `https://www.boell.de/de/publikationen`
  - Thèmes : communs, écologie, démocratie, foncier
  - 📝 Pagination ?page=N jusqu'à 60+

## 🟡 Nécessitent parser spécialisé (12)

- **The Anarchist Library — OPDS feed** [multi, type=opds]
  - `https://theanarchistlibrary.org/opds`
  - Thèmes : anarchisme
  - 📝 ~10000 textes EN/FR/ES/DE/IT — corpus principal anglophone
- **libcom.org — library** [en, type=deep_html]
  - `https://libcom.org/library`
  - Thèmes : anarchisme, syndicalisme, communisme_libertaire
  - 📝 PDFs sur les pages-article, pattern libcom.org/files/*.pdf
- **CrimethInc — library** [en, type=deep_html]
  - `https://crimethinc.com/library`
  - Thèmes : anarchisme, contre-culture, zines
  - 📝 Section /zines avec beaucoup de PDFs
- **Sprout Distro — catalog** [en, type=deep_html]
  - `https://sproutdistro.com/catalog/`
  - Thèmes : anarchisme, zines, distro
  - 📝 files.sproutdistro.com/*.pdf
- **CRAS — Centre de Recherches sur les Alternatives Sociales** [fr, type=deep_html]
  - `https://cras31.info/`
  - Thèmes : anarchisme, histoire_sociale
  - 📝 Pattern SPIP /IMG/pdf/ sur articles
- **Fédération Anarchiste — publications** [fr, type=deep_html]
  - `https://www.federation-anarchiste.org/spip.php?rubrique3`
  - Thèmes : anarchisme
  - 📝 Pattern SPIP
- **Portal OACA — anarcosindicalismo ES** [es, type=deep_html]
  - `https://www.portaloaca.com/`
  - Thèmes : anarchisme, syndicalisme
  - 📝 WordPress, PDFs dans wp-content/uploads/YYYY/MM/
- **Archive.org — folksonomy_anarchism** [multi, type=archive_org]
  - `https://archive.org/advancedsearch.php?q=collection%3Afolksonomy_anarchism&output=json&rows=200`
  - Thèmes : anarchisme
  - 📝 Collection dédiée — quelques milliers d'items
- **Archive.org — peasant movements** [multi, type=archive_org]
  - `https://archive.org/advancedsearch.php?q=subject%3A%22peasant+movement%22+AND+mediatype%3Atexts&output=json&rows=200`
  - Thèmes : paysannerie
- **Archive.org — commons / propriété d'usage** [multi, type=archive_org]
  - `https://archive.org/advancedsearch.php?q=subject%3A%22commons%22+OR+subject%3A%22enclosure%22+AND+mediatype%3Atexts&output=json&rows=200`
  - Thèmes : communs, propriété_usage
- **HAL Science — communs fonciers** [fr, type=hal]
  - `https://api.archives-ouvertes.fr/search/?q=communs+fonciers&fl=title_s,uri_s,fileMain_s,language_s&wt=json&rows=100`
  - Thèmes : communs, foncier, recherche
- **HAL Science — paysannerie / agriculture vivrière** [fr, type=hal]
  - `https://api.archives-ouvertes.fr/search/?q=paysannerie+OR+vivri%C3%A8re&fl=title_s,uri_s,fileMain_s,language_s&wt=json&rows=100`
  - Thèmes : paysannerie, recherche

## 🟠 JS-only (Playwright requis) (3)

- **Persée — recherche contre-culture** [fr, type=html]
  - `https://www.persee.fr/search#v=list&q=contre-culture`
  - 📝 Page de recherche JS-rendered → 0 docs. API OAI-PMH disponible mais non implémentée.
- **HAL — recherche fanzine+genre** [fr, type=html]
  - `https://hal.science/search/index/?q=fanzine+genre&docType_s=ART`
  - 📝 Remplacé par hal_communs et hal_paysannerie via API
- **Archive.org — recherche fanzine+sociologie** [en, type=html]
  - `https://archive.org/search?query=fanzine+sociologie&mediatype=texts`
  - 📝 Page de recherche JS-rendered → 0 docs. Remplacé par archive_org_* via API.

## Roadmap d'activation

Sources `validated` à activer dans `config/sources.yml` :
- [ ] Infokiosques — index T
- [ ] Infokiosques — index L
- [ ] Infokiosques — rubrique thématique 22
- [ ] Infokiosques — rubrique thématique 24
- [ ] Heinrich-Böll-Stiftung — publications EN
- [ ] Heinrich-Böll-Stiftung — publications DE

Parsers à implémenter pour débloquer les sources `needs_parser` :
- [ ] `archive_org` (3 sources)
- [ ] `deep_html` (6 sources)
- [ ] `hal` (2 sources)
- [ ] `opds` (1 source)
