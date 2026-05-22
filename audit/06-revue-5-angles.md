# Revue critique multi-angles — propositions hiérarchisées

Cinq analyses critiques parallèles (chercheur, journaliste, activiste, influenceur,
ergonome), fusionnées en une liste unique classée par intérêt.

Légende — **Effort** : faible / moyen / élevé · **Impact** : faible / moyen / fort ·
**Angles** : C chercheur · J journaliste · A activiste · I influenceur · E ergonome.

---

## Palier S — Fondations à réparer (convergence maximale)

### S1. Réconcilier le scoring et nettoyer les faux positifs
Angles : C · J · A · I — Effort : moyen — Impact : fort
Le score affiché est le score « sur titre seul » (`latest_score`), pas le score
post-lecture produit par `synopsis_enricher`. Résultat : des fiches « 1/10 » ou
« 0/10 » richement éditorialisées, et des hors-sujet (Nick Land, accélérationnisme)
dans le flux RSS. 254/345 docs sont notés ≤2. Solution : propager le score
post-lecture comme tri principal, afficher les deux scores distinctement, et ne
publier (fiche HTML, sitemap, RSS) que le corpus retenu — `catalog.json` reste
complet pour la transparence.

### S2. Métadonnées bibliographiques fiables
Angles : C · J · I — Effort : moyen — Impact : fort
Auteur et année sont devinés par regex sur le nom de fichier ; le champ `lang`
n'est jamais peuplé ; date de publication et date de collecte sont confondues.
Solution : extraire auteur/date/éditeur/langue via les API déjà disponibles (HAL,
Archive.org, OPDS, RSS `pubDate`) + une passe Claude dédiée sur la page de titre,
stocker `doc_date` distinct de `collected_date`.

### S3. Pérennité des liens — vérification + miroir d'archive
Angles : C · J — Effort : moyen — Impact : fort
Les fiches renvoient vers l'URL source directe, fragile (sites militants
instables, 404 fréquents). Solution : HEAD périodique sur chaque lien
(`link_status` + `last_checked`), soumission à `web.archive.org/save`, affichage
d'un badge « lien vérifié le… » et d'une copie pérenne Wayback en secours.

---

## Palier A — Fort impact

### A1. Typologie documentaire + page « Boîte à outils »
Angles : C · A — Effort : moyen — Impact : fort
Aucune distinction entre tract, étude académique, rapport, source primaire, guide
pratique. Solution : champ `doc_type` renseigné au scoring, exposé en facette de
filtrage, + une page dédiée aux ressources actionnables (baux types, statuts
GFA/SCI, retours de collectifs).

### A2. Moteur de génération d'images de partage
Angles : I · A — Effort : moyen — Impact : fort
`og:image` pointe vers la couverture PDF brute (souvent illisible en vignette) ;
`og-default.svg` est manquant. Solution : script Pillow générant par fiche un PNG
1200×630 (carte sociale) et des citation-cards 1080×1080 à partir des
`citations_phares` déjà présentes dans les bulles.

### A3. Boucle d'abonnement : newsletter visible + « document de la semaine »
Angles : I · J — Effort : faible — Impact : fort
`newsletter.py` génère un digest mais aucune page ne propose de s'inscrire.
Solution : bloc d'inscription (home + footer) et page `/une` à URL stable mettant
en avant le document phare de la semaine.

### A4. Vérification des citations littérales (anti-hallucination)
Angles : C — Effort : moyen — Impact : fort
Les citations « exactes » et leurs numéros de page ne sont jamais re-vérifiées
dans le PDF. Solution : re-rechercher chaque `quote` dans le texte extrait,
marquer « vérifiée / non retrouvée », distinguer page physique et page imprimée.

### A5. Fiabiliser le chargement client du site
Angles : E — Effort : moyen — Impact : fort
Tout le contenu est rendu côté JS ; en cas d'échec, le visiteur voit un message
destiné au développeur ; les fiches pré-rendues font un `meta refresh` immédiat.
Solution : skeleton cards, message d'erreur orienté visiteur, vrai contenu
lisible dans le fallback pré-rendu (pas de redirection).

### A6. Filtres du catalogue : chips actifs + persistance URL
Angles : E — Effort : moyen — Impact : fort
Aucun récapitulatif des filtres appliqués ; sources/langues/formats ne sont pas
dans l'URL → état perdu au retour depuis une fiche ; le filtre par défaut
(score≥5) masque la moitié du corpus sans le signaler clairement. Solution :
barre de chips supprimables, sérialisation de tous les filtres dans l'URL,
bandeau « N fiches masquées ».

### A7. Dossiers éditoriaux nommés par lutte / thème
Angles : A · I — Effort : moyen — Impact : fort
`dossiers.html` regroupe mécaniquement par catégorie IA et n'affiche rien sans
docs notés ≥9. Solution : une dizaine de dossiers définis éditorialement (Sortir
une terre du marché, ZAD & défense de territoires, Sans-terre & réforme
agraire…), chacun avec un chapô écrit et des ressources clés rattachées.

### A8. Page « État du corpus » — transparence des biais
Angles : C · J — Effort : faible — Impact : fort
Le corpus penche fortement militant francophone, sans que rien ne le quantifie ni
ne le signale. Solution : page générée depuis `catalog.json` (répartition
langue / source / décennie / score), champ `orientation` par source, section
honnête « ce que cette veille ne couvre pas ».

---

## Palier B — Impact moyen

### B1. Bloc « Citer ce document » + orientation des sources
Angles : J · C — Effort : moyen — Impact : moyen
Encart de citation prêt-à-publier (auteur/titre/éditeur/année/URL, bouton copier)
sur chaque fiche, et badge d'orientation (militant/académique/institutionnel).

### B2. Téléchargement hors-ligne & packs imprimables
Angles : A — Effort : moyen — Impact : moyen
Héberger une copie locale du PDF, bouton « télécharger pour imprimer », signaler
les formats brochure (`-cahier`), proposer des packs ZIP thématiques (« Kiosque »).

### B3. Partage natif + posts pré-formatés
Angles : I · A — Effort : faible — Impact : moyen
Boutons de partage (Web Share API, Mastodon, Bluesky, LinkedIn) sur fiches et
bulles, + thread / texte LinkedIn pré-rédigés copiables, alimentés par
`titre_accroche` et les citations.

### B4. Voix accessible : champ « en clair »
Angles : A · I — Effort : faible — Impact : moyen
Ajouter à chaque bulle 2 phrases en langue simple (« concrètement, à quoi ça sert
dans une lutte ? »), affichées en tête de fiche avant l'abstract éditorial.

### B5. RSS conforme + feeds dérivés + page « Cette semaine »
Angles : J · I — Effort : faible — Impact : moyen
Corriger le format de date RFC822 et le namespace Atom du flux ; générer des
feeds par concept et un feed « scoops » (≥9) ; page `/actu` listant les ajouts
des 7 derniers jours.

### B6. Hiérarchie de l'accueil + CTA
Angles : E · I — Effort : faible — Impact : moyen
Le hero ne propose aucune action ; six sections de poids visuel égal. Solution :
CTA primaire « Explorer les fiches » (et recherche) dans le hero, alléger les
sections redondantes (« Voix du Sud » / « Récemment ajoutés »).

### B7. Recherche : état vide actionnable + repli souple
Angles : E — Effort : moyen — Impact : moyen
La recherche exige tous les termes (`terms.every`) sans explication en cas de
zéro résultat. Solution : bouton « réinitialiser les filtres », repli « au moins
un terme », surlignage des occurrences, annonce du nombre de résultats.

### B8. Identifiants pérennes DOI / ISBN / HAL dans les exports
Angles : C — Effort : faible — Impact : moyen
Capturer DOI/ISBN/HAL-id à la collecte et les mapper en BibTeX/RIS/CSL.

### B9. Synopsis exploitable : acteurs, controverse, angle
Angles : J — Effort : moyen — Impact : moyen
Ajouter au prompt d'enrichissement des champs `acteurs`, `controverse`,
`angle_journalistique`, affichés dans un encart « pour aller plus loin ».

### B10. Contribution ouverte sans GitHub + retrait/anonymat
Angles : A · C — Effort : moyen — Impact : moyen
La seule porte d'entrée est une issue GitHub technique. Solution : formulaire web
simple relayé par e-mail, appel aux collectifs à soumettre leurs propres
brochures, procédure de déréférencement visible, et anonymat respecté par défaut
(ne jamais inférer un auteur absent de la source).

### B11. Recherche avancée structurée
Angles : C — Effort : moyen — Impact : moyen
Filtrage multi-critères combiné (auteur ET période ET langue ET score
post-lecture) côté `app.js`, à partir de champs structurés dans `catalog.json`.

### B12. Recoupement : versions et traductions d'un même texte
Angles : J — Effort : moyen — Impact : moyen
`dedup.py` détecte les doublons mais l'interface n'expose rien. Solution : bloc
« autres versions / traductions » sur la fiche, masquage des doublons binaires.

---

## Palier C — Polish / optionnel

### C1. Fiche détail : densité et scannabilité
Angles : E — Effort : faible — Impact : moyen
Reléguer l'identifiant technique en pied de fiche, hiérarchiser la grille méta
(Score/Auteur/Date en évidence), badge sobre « résumé généré automatiquement ».

### C2. Cibles tactiles mobile
Angles : E — Effort : faible — Impact : moyen
Labels de filtres à 44px min, supprimer le scroll imbriqué de la liste de sources
(liste pliable `<details>`).

### C3. Mettre en avant les récits de lutte et les victoires
Angles : A — Effort : faible — Impact : moyen
Tag `recit_de_lutte` + section d'accueil « Elles et ils l'ont fait » (terres
reprises, foncières créées, expulsions stoppées).

### C4. Contraste WCAG des 3 palettes + clavier du menu palette
Angles : E — Effort : moyen — Impact : moyen
Vérifier les ratios AA sur les trois palettes, ajuster `--text-faint`, rendre le
menu palette navigable au clavier.

### C5. Onboarding première visite + légende du score
Angles : E · I — Effort : faible — Impact : faible
Ligne d'aide pliable expliquant score et bulle ; ajouter le sens textuel
(« 7/10 · pertinent ») plutôt que la couleur seule.

### C6. Reproductibilité : versionner modèle + prompt par fiche
Angles : C — Effort : faible — Impact : moyen
Stocker `model` et `prompt_version` (hash) dans chaque run, les afficher dans
l'historique de veille.

### C7. Preuve sociale / fil d'activité sur la home
Angles : I — Effort : faible — Impact : faible
« N nouveaux documents ce mois-ci », mini-fil daté des derniers ajouts.

### C8. README à jour
Angles : J — Effort : faible — Impact : faible
Réécrire le README avec l'architecture réelle (synopsis, bulles, site, exports,
discovery) et les limites connues.

### C9. Licence à réciprocité + charte de gouvernance
Angles : A — Effort : faible — Impact : moyen
Envisager une licence non-marchande (CC-BY-NC-SA / Peer Production License) et
une courte charte : qui décide des sources, comment un collectif rejoint le
pilotage.
