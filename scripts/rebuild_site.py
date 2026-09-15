#!/usr/bin/env python3
"""rebuild_site.py — régénère le site à partir du catalogue, sans veille.

Utilisé par .github/workflows/rebuild-site.yml pendant le nettoyage du backlog
(session #25) : la lecture des docs se fait sur la machine de Ced, qui pousse
le catalogue par lots ; la CI régénère site/ et publie, sans attendre la fin.

Ne modifie JAMAIS synopsis/catalog.json ni synopsis/duplicates.json (écrits
en parallèle par cleanup_backlog.py) : pas de traduction des citations, pas
d'archivage, pas de link_check — ces étapes restent à la veille normale.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import watch  # noqa: E402

cat = watch.SYNOPSIS_PATH / "catalog.json"
steps = [
    ("interface", lambda: watch.generate_interface()),
    ("index plein texte", lambda: watch.fulltext_index.build_index(cat, watch.SYNOPSIS_PATH / "fulltext_index.json")),
    ("état du corpus", lambda: watch.corpus_stats.build_stats(cat)),
    ("dossiers", lambda: (watch.editorial.build_dossiers(cat), watch.editorial.build_featured(cat))),
    ("exports", lambda: (watch.export_bibtex.export_bibtex(cat, Path("exports/catalog.bib")),
                         watch.export_bibtex.export_ris(cat, Path("exports/catalog.ris")),
                         watch.export_bibtex.export_csl_json(cat, Path("exports/catalog.csl.json")))),
    ("site", lambda: watch.publish_site(datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M"))),
]
failed = 0
for name, fn in steps:
    try:
        fn()
        print(f"✓ {name}")
    except Exception as e:  # une étape ratée n'empêche pas les autres
        failed += 1
        print(f"⚠ {name} : {e}")
import audit_site  # noqa: E402
rc = audit_site.main()
print(f"audit_site exit={rc}")
sys.exit(1 if failed or rc else 0)
