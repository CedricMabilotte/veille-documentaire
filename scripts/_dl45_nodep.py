#!/usr/bin/env python3
"""
Télécharge les docs score 4-5 non téléchargés — sans enrichissement LLM.
Timeout court : ~30s par doc max.
"""
import sys, json, hashlib, requests, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import pdf_processor

CATALOG_PATH = Path(__file__).parent.parent / 'synopsis' / 'catalog.json'
DOCS_PATH    = Path(__file__).parent.parent / 'docs'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; LibraryBot/1.0)'}

# Index de départ reçu en arg
START = int(sys.argv[1]) if len(sys.argv) > 1 else 0
COUNT = int(sys.argv[2]) if len(sys.argv) > 2 else 10

def file_uid(url):
    return hashlib.md5(url.encode()).hexdigest()[:8]

with open(CATALOG_PATH) as f:
    catalog = json.load(f)

# On regénère la liste complète pour que les index restent stables
all_targets = [(doc_id, doc) for doc_id, doc in catalog['docs'].items()
               if doc.get('score_initial') in (4,5) and doc.get('url')]
# Filtre sur ceux pas encore traités (downloaded=False ET pas de download_status=ok)
targets = [(did, d) for did, d in all_targets
           if not d.get('downloaded') and d.get('download_status') not in ('ok','already_present','ok_via_variant','ok_via_browser')]

print(f'Total non traités : {len(targets)} | Lot [{START}:{START+COUNT}]')
lot = targets[START:START+COUNT]

downloaded = failed = 0

def try_download(url, dest):
    """Retourne (ok, status)"""
    try:
        h = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        if h.status_code == 404:
            return False, 'failed_404'
    except Exception as e:
        print(f'    HEAD err: {e}')

    try:
        r = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        r.raise_for_status()
        with open(dest,'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
    except Exception as e:
        return False, f'failed_network ({e})'

    if pdf_processor.validate_pdf(dest):
        return True, 'ok'
    # Bypass UA
    try:
        ok2, err = pdf_processor.redownload_with_bypass(url, dest)
        if ok2:
            return True, 'ok_via_browser'
    except Exception as e:
        print(f'    bypass err: {e}')
    if dest.exists():
        dest.unlink()
    return False, 'failed_invalid'

for doc_id, doc in lot:
    url = doc['url']
    filename = doc.get('filename','')
    uid = file_uid(url)
    dest = DOCS_PATH / f'{uid}_{filename}'
    label = ((doc.get('runs') or [{}])[-1].get('link_text','') or filename)[:55]
    print(f'\n  {doc_id} [{doc.get("score_initial")}] {label}')

    if dest.exists() and pdf_processor.validate_pdf(dest):
        sz = dest.stat().st_size // 1024
        print(f'    deja present ({sz}kB) — mise a jour catalog')
        catalog['docs'][doc_id]['downloaded'] = True
        catalog['docs'][doc_id]['saved_as'] = f'docs/{uid}_{filename}'
        catalog['docs'][doc_id]['download_status'] = 'already_present'
        downloaded += 1
        continue

    ok, status = try_download(url, dest)
    if ok:
        sz = dest.stat().st_size // 1024
        print(f'    OK ({status}) — {sz}kB')
        catalog['docs'][doc_id]['downloaded'] = True
        catalog['docs'][doc_id]['saved_as'] = f'docs/{uid}_{filename}'
        catalog['docs'][doc_id]['download_status'] = status
        downloaded += 1
    else:
        print(f'    ECHEC: {status}')
        catalog['docs'][doc_id]['download_status'] = status
        failed += 1

with open(CATALOG_PATH,'w') as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

print(f'\n=== Lot [{START}:{START+COUNT}]: téléchargés={downloaded}, echecs={failed} ===')
