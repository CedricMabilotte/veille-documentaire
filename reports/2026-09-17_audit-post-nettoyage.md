# Audit post-nettoyage du 17/09/2026 — biblio.actitude.org

Périmètre : site public `CedricMabilotte/biblio-actitude-org` au commit 79f0184 (publié le 17/09 à 09:01 UTC, 841 fiches), dépôt privé `veille-documentaire` et catalogue local. Onze dimensions ont été auditées en lecture seule : non-régression, liens internes, liens externes (moitiés A et B), titres, citations, métadonnées, UX/SEO/accessibilité, revue de code, dépublications et exclusions, rendu client. Les corrections sûres ont ensuite été appliquées par un seul écrivain. Les rapports bruts de chaque dimension (JSON) sont dans `/home/claude/audit/reports/` (conteneur d'audit).

## 1. Ce qui a été corrigé (commits sur `main`)

| Commit | Contenu | Constats |
|---|---|---|
| c950f03 | **translate_citations.py** : un échec de traduction n'écrit plus rien dans quote_fr (avant, l'original y était recopié et ne partait plus jamais en traduction). Ajouts : claude_guard (pause en cas de limite de session), timeout porté à 240 s, prompt « langue source indiquée » qui traduit depuis la langue réelle, libellés sw/ts/sn/el/tr/eu/da/sv/pl/ja/id/ku/tl/ar/ko/ca | RC5, RC6, D-identique, C |
| c950f03 | **export_bibtex.py** : exports = docs publiés (`watch._is_publishable`), aucune année devinée (URL, nom de fichier, creationDate) | NRL-01, LI-04, NRL-02 |
| c950f03 | **watch.py** : `data/dossiers.json` publié filtré sur le catalogue public, doc_count recalculé ; flux scoops limité aux fiches publiables ; sitemap sans graph.html, avec concepts/, une.html et etat-corpus.html ; description jamais tirée de `runs[].raison` ; `<html lang="fr">` sur les fiches pré-rendues | NRL-03, LI-02, RCN-06, LI-03, NRL-05, SEO-01, LI-05, NRL-06, DE-06, SEO-02 (code), A11Y-01 (partiel) |
| c950f03 | **corpus_stats.py** : lisait la clé YAML `excluded`, qui n'existe pas, au lieu de `exclusions` | NRL-07, UX-03 (données) |
| c950f03 | **Front** : liens de pied de page `rss.xml` (supprimé, doublon de feed.xml) et `scoops.xml` (remplacé par feeds/scoops.xml) sur 10 pages ; `<base href="/">` dans 404.html ; `_latestRunDate` sans le préfixe `cleanup_` (tuile « Dernière veille », tri « récent », année BibTeX) ; recherche indexant doc.title, doc.author et doc.journal ; facette langue lisant doc.lang, avec ajout de de et it ; libellé « Fiches éditorialisées » à la place de « Dossiers éditoriaux » | LI-01, NRL-04, LI-06, UX-01, RCN-01, RCN-03, UX-02 |
| c950f03 | **rebuild-site.yml** : un push qui échoue trois fois fait maintenant échouer le job, avec abandon du rebase | RC4 (partiel) |
| 239097d | **app.js** : `inferAuthor()` = `docAuthor()`, plus d'auteur deviné à partir du nom de fichier (« EN », « The », « LVC »…) | MD-16 (partiel), RCN-07 (partiel) |
| 239097d | **link_check.py** : `%` ajouté à `safe`, les %xx ne sont plus ré-encodés | B1, LEA-05 (code) |
| 239097d | **doc_metadata.py** : `find_isbn` valide le checksum ISBN-10/13 | MD-06 (code) |
| c5f145d | **catalog.json** : 13 titres pris dans pdf_title ou link_text (20da6e80, c1c58233, 13352415, 7cf86983, a2c763f2, 4de4a141, b071dbb5, 3d90732c, 03e23323, 9e831a55, db7d89b2, 8c24eb4d, 83b6390f) ; 22 titres corrigés en typographie seulement (retour ligne, espaces doubles, « L’ i », « n° NN –X ») ; lang corrigé sur 18 docs d'après l'URL ou le titre (it ×8, sw ×5, el ×2, es, tr, sn, ts) ; 7 quote_fr inversées retirées (514c1d0e) ; 908 quote_fr identiques à une citation non française et 200 quote_fr tronquées effacées pour être retraduites | TI-12, TI-05a, B-fr-jamais-traduit, R7, MD-04 (partiel), D-inverse, R9, R5, R6, D-traduction-tronquee, R8 |
| 4f1a9ab | **DEPLOIEMENT.md / INSTRUCTIONS.md** : réalignés sur watch.yml, rebuild-site.yml et publish-only.yml | RC13 |
| cf6df92 | **catalog.json** : 1240 citations retraduites depuis la langue réelle (187 docs), dont les versions swahili, grecque, turque, italienne, tsonga et shona | C, D-identique, D-traduction-tronquee, R5, R6, R7, R8 |

Trois rebuilds ont été déclenchés et publiés (runs 35245715027 et 35283425643, publications 35246204574 et suivante). Vérifié en ligne (curl avec cache-bust) après le rebuild de 16:18 UTC :
- catalogue : 841 fiches ;
- dossiers.json : 0 id hors catalogue ;
- exports : bib, ris et csl à 841 entrées chacun, 0 hors catalogue, pas d'année pour 0b22d51b, c62d22bd ni 08baa6d1 ;
- sitemap : sans graph.html ;
- scoops : aucune fiche dépubliée ;
- fiches/20da6e80.html : titre corrigé, `lang="fr"` ;
- fiches/0380ea78.html : description neutre.

## 2. Citations : rattrapage

Script : `~/scratch-biblio/audit0917/catchup.py`, journal dans `catchup.log`. Il ne traite que les docs publiables.
- Phase A : effacements et corrections listés au §1. Le détail par id est dans `phaseA.json`.
- Phase B : retraduction de 173 docs avec le nouveau prompt. Quatre PDF trilingues EN-ES-FR (115993e5, 12d55115, 710fa08a, 73e20c5e) gardent lang=fr : ils sont traduits avec une langue source forcée.
- Résultat : deux passes. Passe 1 (16:00 → 22:15 UTC) : 173 docs, 1135 citations traduites, 14 docs en échec, tous pendant des coupures réseau de la machine. Passe 2 (22:20 → 22:34 UTC) sur ces 14 docs : 105 citations traduites, 1 seul doc encore en échec, **c46789b4** (citations en acholi : le modèle refuse de traduire). Commit **cf6df92b**, rebuild 35283425643, publié et vérifié en ligne à 22:55 UTC : 5636 citations publiées, 5224 avec quote_fr.
- Reste 54 citations non françaises sans quote_fr, dans 28 docs (contre 180 avant) : c46789b4 (6, acholi), 36acdcd4 (6, « List of members » — ce sont des noms d'organisations), et 26 docs avec une ou deux citations courtes. Elles seront retentées au prochain run, puisque rien n'est plus écrit en cas d'échec.
- Aucune quote_fr tronquée ne subsiste ; 7 quote_fr restent identiques à une citation non française dans 5 docs (4be4a4e2, e5c971ba, 38c834f3, 85283063, eea43d6c) : ce sont des réponses réelles du modèle, pas des échecs masqués.

Méthode de détection du français : proportion de mots-outils français ≥ 12 %. Sur ce critère, 285 citations identiques à leur quote_fr ont été jugées déjà en français et laissées telles quelles. Parmi elles, 27c5e053, 45a3b0e8 et e5c971ba.

## 3. Laissé en l'état : décisions pour Ced

### 3.1 Critiques
1. **Exclusions sans effet (RC1 / MD-01 / DE-01 / R3).** Cinq clés de `config/exclusions.yml` sont entièrement numériques et YAML les lit comme des entiers : 13352415, 40220080, 82204765, 89425142, 90230173. Ces docs restent donc publiés, et le total réel attendu est 836, pas 841. Le correctif tient en 1 ligne (`{str(k) for k in …}` dans `watch._load_exclusions`, plus des guillemets sur les clés), mais je ne l'ai **pas appliqué** : il dépublierait 5 fiches, dont 3 (40220080, 90230173, 82204765 — la Déclaration de Nyéléni) sont le **dernier exemplaire publié** de leur groupe de doublons (voir le point 2). Décider d'abord quelle version garder, puis appliquer. Attention aussi aux ids de forme `0[0-7]{7}`, que YAML lit en octal.
2. **Doublons « mutuels » (RC2 / DE-02 / R4).** 28 à 31 groupes (71 docs) sont exclus en entier : chaque copie est marquée « doublon de » l'autre. Par ailleurs, 59 exclusions visent un canonique fantôme, absent du catalogue. Au total, 120 des 139 doublons dépubliés le 17/09 n'ont plus aucun exemplaire en ligne. Il faut choisir un représentant par groupe et retirer sa clé. Côté code, `dedup.register_pdf` doit ignorer un `other_id` qui désigne déjà `doc_id` comme doublon.
3. **Couvertures fausses (MD-15) et docs/ corrompus (MD-14).** 25 couvertures sont des captures de page : anti-bot HAL (12) et bandeau Internet Archive (13). 15 fichiers de docs/ sont des pages HTML enregistrées sous le nom `.pdf`. À faire : passer `has_cover=false` sur ces 25 docs, re-télécharger les 15 fichiers, et ajouter à regen_covers et au téléchargement un contrôle de la signature `%PDF`. Aucune correction appliquée : le champ has_cover n'était pas dans le périmètre autorisé.
4. **Titres vides de sens (TI-01, 55 docs) et noms de fichier (TI-02, 356).** Il faut une relecture humaine : le slug n'est pas une source fiable. Cas signalé : **f6812800**. Son pdf_title (« Proposta de Preâmbulo… Agroecologia ») ne correspond pas au contenu (CONSEA, transgéniques). Il a été écarté de TI-12.
5. **LEA-01 (4ae9c4ba).** L'URL est doublement encodée (`%252520`) et la source répond 404. L'URL décodée (`%20`) répond 206 PDF. C'est une correction mécanique de `url`, non appliquée parce que ce champ était hors périmètre. À faire, puis remettre `link_status=ok`.

### 3.2 Majeurs éditoriaux
- **Pages sans source exploitable.** LEA-04 : 13352415, livre archive.org en prêt contrôlé, à exclure (même traitement que les 28 livres). LEA-03 : 037cb37e, PDF vide. B2 : 93066cf9, doublon de 89425142 avec une URL « Sudame?rica » en 404. B3 : 9207a9e2 et 899e341b, URL et titre en « ???? ».
- **Scores (MD-09, MD-10).** 19 docs ont un score_final alors qu'ils n'ont jamais été lus. 13 docs publiés auraient moins de 4 d'après leur relevance_score : 2fc51d22, a5f5ceea, 8af5f6c1, f349dcb8, d7759e91, b0e87371, dcb30b82, 2c9c4d74, fa6ceecb, cd8eaa5a, bb0dcc2a, cfb61947, a0be49c2.
- **Doublons encore publiés (MD-13).** Paires : 7a9e87db/17fe98fc (même md5), d518396b/59fe7d0a, 1c7c962e/e6ac8fd0, 76ab1d39/a5df1a9d, 3fe8867b/bd44cc6a, 72a2c796/3cc0465a, 8741a8e6/ac638fb6.
- **Auteurs faux (MD-17).** 41e09539 est attribué à « Karl Marx » alors que le texte est de Proudhon ; df13538a à « Hakim Bey ». Autres cas plausibles : 2ab410d3, 931fc89b, b0917bdf, f2168aa7, 47c6599a.
- **pdf_author parasites (MD-16, reste).** Ils s'affichent encore via docAuthor : « Windows User », « Lenovo », « %username% », des e-mails, « Jean-Marie Tremblay » (le numériseur). Décision à prendre : liste noire ou affichage de doc.author seul.
- **Champ editeur = logiciel producteur du PDF (MD-02, 284 docs).** Il faut vider les valeurs et retirer le repli sur `pdf_meta.producer` dans doc_metadata.
- **doc_date = date de création du PDF (MD-03, 29 cas contredits par IA ou HAL).**
- **ISBN invalides dans les données (MD-06).** 24 valeurs à vider ; le code est déjà corrigé.
- **Langues non gérées ou doublons linguistiques (C).** Il faut choisir entre traduire depuis la langue réelle (fait par le rattrapage) et dépublier les versions en swahili, grec, turc, etc. quand une version fr ou en existe.
- **Texte corrompu (F-texte-corrompu).** 26e16076, dont le texte a perdu ses « e » et ses « o » : OCR et régénération des citations.
- **Page Corpus (UX-03).** Chiffres calculés sur 1969 docs et pourcentages codés en dur périmés : le paragraphe « biais » est à réécrire.
- **Divers.** Redirections pour les fiches dépubliées (DE-03). Relecture de 36acdcd4 (« List of members », citations = noms d'organisations).

### 3.3 Code non appliqué (plus de 40 lignes ou risque)
- **DE-04 / LI-10.** Filtrer `fulltext_index.json` sur les publiés : l'index contient 1969 docs.
- **PERF-01 / PERF-02.** Catalogue allégé (7,9 Mo chargés par l'accueil) ; vignettes de couverture en 400 px.
- **A11Y-02.** Contrastes en thème sombre. RCN-12 : débordements horizontaux sur mobile.
- **TI-09.** normalize_title : rejeter les pdf_title de type nom de fichier, appliquer html.unescape. TI-08 : même repli de titre au rebuild et dans docTitle.
- **B8.** check_url : repli en GET quand HEAD renvoie 404. LEA-06 : backoff par domaine sur 503/429 (infokiosques).
- **Relance ciblée de link_check.** RECHECK_AFTER_DAYS bloque les 13 faux `dead` jusqu'au 29/09.
- **RC4 (reste).** trigger_rebuild sans nouvelle tentative, commit bloqué quand l'audit échoue. RC9 : garde anti-écrasement du catalogue. RC11/RC12 : budget du post-traitement, cron « */2 » contre lundi.
- **SEO-02 (reste).** noindex et retrait du sitemap pour les 52 fiches sans contenu. A11Y-01 (reste) : attribut `lang` sur les citations non traduites.

### 3.4 Git local
**RC7 / DE-09.** `.git/index` ne correspond plus à HEAD : un `git commit` porcelaine supprimerait les 167 exclusions. Lancer `git read-tree HEAD` (index seul) avant tout commit classique, ou continuer à passer exclusivement par `cleanup_backlog.commit_push`.

## 4. Constats mineurs (non traités)
- **Liens et sources.** archive_url en http:// (77 docs, LEA-11/B11) ; hal_id manquant (12, MD-07) ; clé `actores` (3, E-cle-actores) ; assets/covers/test.jpg (LI-09) ; versions[] vers des docs hors catalogue (LI-08) ; ancres auteurs.html (LI-07) ; certificat expiré revistacontroversia (B4) ; anti-bot HAL, SciELO, Springer (LEA-07, B5, B10) ; archive_url inutiles (LEA-08).
- **Titres et métadonnées.** Titres en majuscules, tronqués ou en double (TI-03 à TI-06) ; lang vide (56, MD-05) ; enrichment.error périmé (MD-11) ; résumés vides (MD-12) ; facette type inutile (RCN-04) ; filtre décennie (RCN-05).
- **Interface et accessibilité.** En-tête mobile (RCN-11) ; hiérarchie de titres et lien vide (A11Y-03/04) ; balises sociales (SEO-05) ; meta description coupée (SEO-03) ; tableau joint par virgule sur la page Corpus (UX-04) ; en-tête des fiches statiques (UX-05) ; cache 10 min (PERF-03).

## 5. Constats réfutés
- LEA-02 : erreur Cloudflare 520 persistante.
- TI-07 : titre des cartes différent du h1.
- RC3 : watch.yml sans rebase.
- RC8 : 321 clés ≠ file_uid au cron du 19/09 (resté plausible, non confirmé).

## 6. Déroulé et écarts
- **14:33 UTC.** La traduction était terminée côté catalogue : dernière sauvegarde et commit f20f077 à 12:09 UTC, catalogue local identique à origin. translate_resume.py restait bloqué sur l'étape `rclone copy docs/ → Drive`, en cours depuis plus de 3 h (débit d'environ 15 à 80 Ko/s), sans la ligne « terminé ». Après 1 h 25 d'attente, j'ai procédé à 15:57 UTC : le script n'écrit plus le catalogue après son commit final (source relue). À 16:39 UTC, rclone tournait toujours et la ligne « === cleanup_backlog terminé === » n'était pas encore écrite.
- **Coupures.** La machine a été injoignable de 16:55 à 20:15 UTC, puis par intermittence. Le rattrapage tournait en arrière-plan (sauvegarde tous les 20 docs) et a été repris sans perte ; les 14 docs en échec de la passe 1 correspondent à ces coupures.
- **Machine.** Coupures du pont entre 15:00 et 15:13, puis ponctuellement ensuite. Un push du catalogue a échoué pour cause de liaison montante saturée ; il a été relancé en arrière-plan.
- **Validations.** Tout le code a été vérifié par py_compile, `node --check` et chargement YAML avant commit ; les exports ont été testés localement (841/841/841).
