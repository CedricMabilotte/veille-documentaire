#!/usr/bin/env python3
"""
enrich_pending.py — Enrichit tous les docs publiables sans summary.
Résumable : relit le catalogue à chaque doc, skip ceux déjà enrichis.
Sortie propre sur token limit (exit code 2) pour que le scheduler relance.
"""
import sys, os, json, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
os.environ.setdefault('PUBLISH_THRESHOLD', '4')

import watch, synopsis_enricher, pdf_processor

CATALOG  = ROOT / 'synopsis' / 'catalog.json'
DOCS_DIR = ROOT / 'docs'
LOG      = ROOT / 'reports' / 'enrich_pending.log'
LOG.parent.mkdir(exist_ok=True)

def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG, 'a') as f: f.write(line + '\n')

def pending_uids():
    cat = json.loads(CATALOG.read_text())
    uids = []
    for uid, d in cat['docs'].items():
        if not watch._is_publishable(d): continue
        enr = d.get('enrichment') or {}
        if 'summary' in enr: continue  # '' ou texte → déjà traité
        fn = d.get('filename','')
        pdf = DOCS_DIR / fn if fn else None
        if not pdf or not pdf.exists():
            pdf = next(iter(list(DOCS_DIR.glob(f'{uid}_*.pdf'))), None)
        if pdf and pdf.exists():
            uids.append(uid)
    return uids

def enrich_one(uid):
    cat = json.loads(CATALOG.read_text())
    d = cat['docs'].get(uid)
    if not d:
        return 'skip_not_found'
    enr = d.get('enrichment') or {}
    if enr.get('summary'):
        return 'skip_already'

    fn = d.get('filename','')
    pdf = DOCS_DIR / fn if fn else None
    if not pdf or not pdf.exists():
        pdf = next(iter(list(DOCS_DIR.glob(f'{uid}_*.pdf'))), None)
    if not pdf or not pdf.exists():
        return 'skip_no_pdf'

    text = pdf_processor.extract_text(pdf)
    if not text:
        # Marquer summary='' pour ne pas reboucler indéfiniment sur les PDFs scannés
        cat['docs'][uid].setdefault('enrichment', {})['summary'] = ''
        CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2))
        return 'skip_no_text'

    title = d.get('title') or d.get('link_text') or d.get('filename','')
    config = watch.load_config()
    keywords = config.get('keywords', [])

    result = synopsis_enricher.enrich(text, keywords, title)

    if 'error' in result:
        err = result['error']
        if 'session limit' in err.lower() or 'token' in err.lower():
            return 'token_limit'
        return f'error: {err[:60]}'

    # Succès — mettre à jour le catalogue
    existing = d.get('enrichment') or {}
    existing.update(result)
    cat['docs'][uid]['enrichment'] = existing
    
    # Générer couverture si absente
    if not d.get('cover'):
        try:
            import fitz, PIL.Image
            doc_fitz = fitz.open(str(pdf))
            pix = doc_fitz[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5))
            img = PIL.Image.frombytes("RGB",[pix.width,pix.height],pix.samples)
            img.thumbnail((400,600))
            cover = ROOT / 'site' / 'assets' / 'covers' / f'{uid}.png'
            img.save(cover,"PNG")
            cat['docs'][uid]['cover'] = f'assets/covers/{uid}.png'
            doc_fitz.close()
        except: pass

    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2))
    summary_len = len(result.get('summary','') or '')
    n_cit = len(result.get('citations',[]) or [])
    return f'ok:{summary_len}c,{n_cit}cit'

def main():
    log('=== enrich_pending démarré ===')
    done = errors = skipped = 0

    while True:
        uids = pending_uids()
        if not uids:
            log(f'✅ Tout enrichi — done={done} errors={errors} skipped={skipped}')
            sys.exit(0)

        log(f'{len(uids)} docs en attente…')
        uid = uids[0]
        title = json.loads(CATALOG.read_text())['docs'].get(uid,{}).get('title','?')[:50]
        log(f'  → {uid} {title}')

        status = enrich_one(uid)

        if status == 'token_limit':
            log(f'⏸  Token limit — {len(uids)-1} restants. Relance à 20h05.')
            sys.exit(2)
        elif status.startswith('ok:'):
            log(f'  ✓ {uid} {status}')
            done += 1
        elif status.startswith('skip'):
            skipped += 1
        else:
            log(f'  ✗ {uid} {status}')
            errors += 1
            # Marquer enrichment vide pour ne pas reboucler
            cat = json.loads(CATALOG.read_text())
            if uid in cat['docs']:
                cat['docs'][uid].setdefault('enrichment', {})['summary'] = ''
            CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
