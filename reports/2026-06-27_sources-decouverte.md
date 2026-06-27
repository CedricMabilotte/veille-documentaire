# Rapport de découverte — nouvelles sources
*Session biblio #8 — 27 juin 2026*

## Résumé

Le catalogue de sources est plus complet qu'attendu. Sur les 6 sources suggérées (FAO, GRAIN, IJC, Via Campesina, FIAN, OpenEdition), **toutes sont déjà présentes** dans `config/sources.yml`. Les angles morts identifiés sont principalement un problème de **scoring**, pas de sourçage.

---

## Bilan par axe

### Afrique — ENDA dans les sources, 0 doc publié

**Source existante :** ENDA Tiers Monde (RSS). Aucun PDF thématique détecté à ce jour.

**Diagnostic :** ENDA publie principalement sur son site institutionnel (endatiersmonde.org), peu de PDFs en accès direct. Le RSS est actif mais les entrées pointent vers des pages HTML, pas des téléchargements.

**Action recommandée :** Observer les 2-3 prochains runs. Si 0 doc après 3 mois, ajouter `Archive.org — foncier Afrique subsaharienne` :
```
url: "https://archive.org/advancedsearch.php?q=%28%22land+rights%22+OR+%22foncier%22+OR+%22commons%22%29+AND+%28%22Africa%22+OR+%22afrique%22+OR+%22subsahar%22%29+AND+mediatype%3Atexts&rows=30&output=json"
```

### Théoriciens canoniques — Ostrom, Federici, Bollier

**Problème identifié :** Ces œuvres ne contiennent aucun keyword dans leur titre :
- *Governing the Commons* (Ostrom) → score_initial = 0
- *Caliban and the Witch* (Federici) → score_initial = 0
- *Think Like a Commoner* (Bollier) → non libre en PDF

**Ostrom :** Accessible sur Archive.org (`archive.org/details/governing-the-commons`) mais en **emprunt uniquement** (access-restricted-item). Aucun PDF librement téléchargeable. Les articles académiques d'Ostrom sont sur JSTOR (derrière paywall). HAL n'a pas ses travaux.

**Federici :** *Caliban and the Witch* disponible sur Archive.org et Monoskop (anti-copyright). Ses textes courts sont sur The Anarchist Library (déjà dans les sources).

**Bollier :** Pas de PDF libre. Son blog bollier.org publie des essais HTML, pas de PDFs.

**Actions réalisées :**
- 2 nouvelles requêtes archive.org ajoutées dans `config/sources.yml` :
  - *Archive.org — théorie des communs (Ostrom, CPR, collective action)*
  - *Archive.org — féminisme et communs (Federici, accumulation primitive)*
- Ces requêtes ciblent directement les `creator:` et titres canoniques, contournant le problème de scoring-titre.

**Limitation persistante :** Les œuvres majeures d'Ostrom sur Archive.org sont en emprunt. Le pipeline ne peut pas télécharger ces PDFs (même situation que les docs archive.org en accès restreint identifiés en session #7).

### Creux 1990-2010 — Via Campesina constitutifs absents

**Sources existantes :** La Vía Campesina (ES, WP REST) + CLOC. Nyéléni 2007 dans les sources.

**Diagnostic :** Les déclarations fondatrices (La Havane 1993, Tlaxcala 1996, Bangalore 2000, São Paulo 2004) sont des documents HTML ou PDFs de petite taille souvent mal indexés. Via Campesina publie des PDFs sur viacampesina.org (wp-content/uploads), couvert par la source WP REST.

**Action recommandée :** Vérifier au prochain run si la source Via Campesina WP REST remonte les publications 1996-2010. Si non, ajouter une requête archive.org :
```
- label: "Archive.org — Via Campesina & Nyéléni (1993-2010)"
  url: "https://archive.org/advancedsearch.php?q=%28%22via+campesina%22+OR+%22nyeleni%22+OR+%22food+sovereignty%22%29+AND+mediatype%3Atexts&rows=30&output=json"
  type: archive_org
```

### Sources suggérées — état réel

| Source | Présente | Type | État |
|--------|----------|------|------|
| FAO Open Repository | ✓ | OAI-PMH | Actif |
| GRAIN | ✓ | RSS + deep_html | Actif |
| International Journal of the Commons | ✓ | deep_html | Actif |
| La Vía Campesina | ✓ | WP REST + ES | Actif |
| FIAN International | ✓ | WP REST + RSS ES | Actif |
| OpenEdition Books | ✓ | deep_html | Actif |
| ENDA Tiers Monde | ✓ | RSS | 0 doc à ce jour |
| Nyéléni | ✓ | deep_html | Actif |
| CLACSO | ✓ | 4 sources | Actif |

---

## Scoring — le vrai angle mort

Les keywords couvrent bien les *concepts* (communs, enclosure, paysannerie…) mais pas les *titres canoniques*. Deux solutions complémentaires :

**Option A — Score override manuel** : Pour les œuvres-clés identifiées, ajouter un `score_override` dans `config/score_overrides.yml` une fois téléchargées. Exemple :
```yaml
<uid_ostrom>:
  score: 9
  raison: "Ostrom — référence fondatrice sur les communs"
```

**Option B — Keywords titre** : Ajouter au scorer des patterns titre-spécifiques :
```yaml
title_patterns:
  - "governing the commons"
  - "caliban and the witch"
  - "communs (de la connaissance)"
  - "think like a commoner"
```
*(nécessite modification du scorer)*

---

## Recommandations par priorité

1. **Court terme** : Observer les 2 nouvelles requêtes archive.org au prochain run CI.
2. **Moyen terme** : Si Ostrom/Federici remontent, appliquer score_override manuel.
3. **Long terme** : Enrichir le scorer avec des patterns titre pour les œuvres canoniques.
