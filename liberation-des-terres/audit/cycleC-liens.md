# Cycle C — Audit santé des liens et des sources

Date : 2026-05-23
Périmètre : `site/` (47 pages HTML) + 35 fiches YAML (`lieux/`, `porteurs/`, `usufruitiers/`, `modeles/`)
Méthode : lecture seule. Liens internes vérifiés contre l'arborescence réelle des fichiers et les `id=` présents. Liens externes testés par interrogation web domaine par domaine (disponibilité + résolution des chemins exacts). Aucun blocage contourné.

---

## 1. Liens internes

**Résultat : aucun lien interne cassé.**

- Les 47 pages HTML ont été parcourues (`href` internes : navigation, footer, cartes, fils d'Ariane, ancres, liens croisés entre fiches).
- Toutes les cibles `l/`, `p/`, `u/`, `m/*.html` correspondent à un fichier existant.
- Tous les liens croisés entre fiches de détail (`../p/...`, `../u/...`, `../l/...`) résolus.
- Toutes les ancres référencées existent comme `id` : `#contenu`, `#tri-base` (pages listes + fiches), `#corpus`, `#indice`, `#nature`, `#limites`, `#etat` (methode.html).
- `data.json` (référencé dans tous les footers) : présent dans `site/`.
- `404.html` utilise des chemins absolus (`/index.html`, `/classement.html`, etc.) : corrects pour un site déployé à la racine du domaine.
- NAV réduit et footer post-cycles A/B : cohérents, aucune cible orpheline ou supprimée.

Aucun correctif requis.

---

## 2. Liens externes / sources

35 fiches testées. Chaque fiche possède un champ `url:` (site principal) et un bloc `sources:` (2 à 4 entrées). Domaines et chemins exacts vérifiés.

### CRITIQUE — 1 lien cassé

**`usufruitiers/gfa-mutuels.yml`** — lignes 9 et 103

URL stockée :
`https://www.ressources.terredeliens.org/les-ressources/decouvrir-les-gfa-sci-citoyen·nes`

Problème : le slug contient un point médian U+00B7 (`citoyen·nes`). L'URL réelle de la ressource est :
`https://ressources.terredeliens.org/les-ressources/decouvrir-les-gfa-sci-citoyens`

Le slug effectif est `decouvrir-les-gfa-sci-citoyens` (sans point médian, terminaison `citoyens`). L'URL actuelle renvoie un 404.

**Correctif proposé** — remplacer aux deux emplacements (ligne 9 `url:` et ligne 103 `sources:`) :
`url: "https://ressources.terredeliens.org/les-ressources/decouvrir-les-gfa-sci-citoyens"`

(Au passage : retirer le `www.` superflu — le domaine canonique du centre de ressources est `ressources.terredeliens.org` sans `www`. Non bloquant mais à uniformiser.)

### À VÉRIFIER MANUELLEMENT — aucun

Tous les chemins profonds soupçonnés au départ ont finalement été confirmés valides :
- `agter.org/bdf/fr/corpus_chemin/fiche-chemin-9.html` — confirmé : c'est bien la fiche SCTL du Larzac.
- `fph.ch/article16_fr.html` — confirmé : `article16` = « La Bergerie de Villarceaux » ; la variante `_fr.html` est la version française standard de ce site SPIP.
- `zad.nadir.org/spip.php?article6260=` — confirmé : forme SPIP standard, article 6260 = fonds de dotation « La Terre en Commun ».

### Redirections / variantes notables (non bloquantes)

- Plusieurs URL `ressources.terredeliens.org` sont stockées avec un `www.` ; le domaine sans `www` est canonique. Fonctionne par redirection, mais à uniformiser.
- Les URL avec caractères pré-encodés (`%C3%A9`, etc.) dans les fiches `gfa-mutuels` et `feve` fonctionnent telles quelles.

### Domaines testés et vivants (synthèse)

Tous confirmés disponibles : hameaudesbuis.org, lurzaindia.eu, arrapitz.eus, terredeliens.org, ressources.terredeliens.org, encommun.eco, zad.nadir.org, bergerie-villarceaux.org, fph.ch, prolongomaif.ch, lacabrery.org, village-vertical.org, habicoop.fr, lelabo-ess.org, larzac.org, agter.org, fonciere-chenelet.org, impactivist.co, eaudubassinrennais-collectivite.fr, finance-fair.org, aventure-antidote.org, socialter.fr, conservatoire-du-littoral.fr, geolittoral.developpement-durable.gouv.fr, reseau-cen.org, auvergne-rhone-alpes.developpement-durable.gouv.fr, banquedesterritoires.fr, feve.co, france-pat.fr, actu-environnement.com, cooperative-oasis.org, colibris-lemouvement.org, reneta.fr, leschampsdespossibles.fr, foncier-solidaire.fr, amenagement-durable.ecologie.gouv.fr, stiftung-trias.de, cooperativecity.org, citego.org, metropolitiques.eu, legifrance.gouv.fr, ecologie.gouv.fr, syndikat.org, frontiersin.org.

---

## 3. Cohérence

### Sources par fiche

**OK** — les 35 fiches possèdent un bloc `sources:` non vide (2 à 4 entrées chacune). Aucune fiche sans source.

### Liens croisés `liens:` → uid existants

**OK pour les cibles** — tous les uid référencés dans les blocs `liens:` correspondent à une fiche existante. Aucun uid fantôme.

### IMPORTANTE — mauvaise catégorisation d'un lien croisé

**`porteurs/conservatoire-littoral.yml`** — ligne 103

`federation-cen` est placé sous la clé `usufruitiers:` alors que `federation-cen` est un **porteur** (fichier `porteurs/federation-cen.yml`, `categorie: porteur`).

Conséquence : la donnée YAML est sémantiquement fausse. Le générateur a malgré tout produit un lien correct (`../p/federation-cen.html` dans `site/p/conservatoire-littoral.html`), donc pas de lien cassé visible — mais la fiche réciproque `federation-cen.yml` liste bien `conservatoire-littoral` sous `porteurs:`. L'incohérence est unilatérale.

**Correctif proposé** — dans `conservatoire-littoral.yml`, déplacer `federation-cen` de `usufruitiers:` vers `porteurs:` :

```yaml
liens:
  porteurs: [federation-cen]
  usufruitiers: []
  lieux: []
```

Priorité Importante (et non Critique) car le rendu HTML reste correct ; c'est la donnée source qui est à corriger pour éviter une régression si le générateur évolue.

---

## Récapitulatif priorisé

| Priorité | Fichier | Problème | Correctif |
|----------|---------|----------|-----------|
| Critique | `usufruitiers/gfa-mutuels.yml` (l. 9 et 103) | Lien externe 404 — slug avec point médian `citoyen·nes` | Slug `…decouvrir-les-gfa-sci-citoyens`, retirer `www.` |
| Importante | `porteurs/conservatoire-littoral.yml` (l. 103) | `federation-cen` (porteur) classé sous `usufruitiers:` | Déplacer vers `porteurs:` |
| Mineure | Fiches `ressources.terredeliens.org` | `www.` non canonique (fonctionne par redirection) | Uniformiser sans `www.` |

Aucun lien interne cassé. 34 fiches sur 35 ont des sources externes 100 % valides ; 1 fiche (`gfa-mutuels`) a 1 lien mort à corriger.
