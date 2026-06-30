#!/usr/bin/env python3
"""
enrich_loop.py — Enrichit tous les docs publiables, reprend automatiquement
après chaque reset de token. Parse l'heure de reset depuis le message d'erreur
Claude CLI et attend reset+5min pour relancer.

Usage : python3 scripts/enrich_loop.py &
Log   : reports/enrich_loop.log
"""
import sys, os, json, re, time, datetime, subprocess
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT    = Path(__file__).resolve().parent.parent
PIDFILE = Path('/tmp/enrich_loop_biblio.pid')

# ── Unicité : un seul process à la fois ─────────────────────────────────────
if PIDFILE.exists():
    old_pid = int(PIDFILE.read_text().strip())
    try:
        os.kill(old_pid, 0)   # vérifie si le process existe
        print(f'enrich_loop déjà actif (PID {old_pid}). Sortie.')
        sys.exit(0)
    except OSError:
        pass  # process mort → on peut continuer
PIDFILE.write_text(str(os.getpid()))

import atexit
atexit.register(lambda: PIDFILE.unlink(missing_ok=True))

os.chdir(str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
os.environ.setdefault('PUBLISH_THRESHOLD', '4')

import watch, synopsis_enricher, pdf_processor

CATALOG = ROOT / 'synopsis' / 'catalog.json'
DOCS    = ROOT / 'docs'
LOG     = ROOT / 'reports' / 'enrich_loop.log'
LOG.parent.mkdir(exist_ok=True)

# Regex pour extraire l'heure de reset depuis le message d'erreur CLI
# ex: "resets 8pm (Europe/Paris)" ou "resets 3:30pm (Europe/Paris)"
RESET_RE = re.compile(
    r'resets?\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*\(([^)]+)\)',
    re.IGNORECASE
)

def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    # Écriture directe dans le fichier uniquement (pas de print pour éviter
    # le doublon si stdout est aussi redirigé vers le même fichier)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')
        f.flush()

def pending_uids():
    cat = json.loads(CATALOG.read_text())
    uids = []
    for uid, d in cat['docs'].items():
        if not watch._is_publishable(d): continue
        enr = d.get('enrichment') or {}
        if 'summary' in enr: continue  # déjà traité (vide ou non)
        fn = d.get('filename', '')
        pdf = DOCS / fn if fn else None
        if not pdf or not pdf.exists():
            pdf = next(iter(list(DOCS.glob(f'{uid}_*.pdf'))), None)
        if pdf and pdf.exists():
            uids.append(uid)
    return uids

def parse_reset_time(error_msg):
    """Extrait l'heure de reset depuis le message d'erreur. Retourne datetime UTC ou None."""
    m = RESET_RE.search(error_msg)
    if not m:
        return None
    hour, minute, ampm, tz_name = m.group(1), m.group(2), m.group(3), m.group(4)
    hour = int(hour)
    minute = int(minute) if minute else 0
    if ampm:
        if ampm.lower() == 'pm' and hour != 12:
            hour += 12
        elif ampm.lower() == 'am' and hour == 12:
            hour = 0
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo('Europe/Paris')
    now_tz = datetime.datetime.now(tz)
    reset_tz = now_tz.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if reset_tz <= now_tz:
        reset_tz += datetime.timedelta(days=1)
    return reset_tz.astimezone(datetime.timezone.utc)

def enrich_one(uid):
    """Enrichit un doc. Retourne ('ok', info) | ('token_limit', reset_dt) | ('skip', raison) | ('error', msg)."""
    cat = json.loads(CATALOG.read_text())
    d = cat['docs'].get(uid)
    if not d:
        return 'skip', 'not_found'
    enr = d.get('enrichment') or {}
    if 'summary' in enr:
        return 'skip', 'already'

    fn = d.get('filename', '')
    pdf = DOCS / fn if fn else None
    if not pdf or not pdf.exists():
        pdf = next(iter(list(DOCS.glob(f'{uid}_*.pdf'))), None)
    if not pdf or not pdf.exists():
        return 'skip', 'no_pdf'

    text = pdf_processor.extract_text(pdf)
    if not text:
        cat['docs'][uid].setdefault('enrichment', {})['summary'] = ''
        CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2))
        return 'skip', 'no_text (PDF scanné)'

    title = d.get('title') or d.get('link_text') or fn
    config = watch.load_config()
    keywords = config.get('keywords', [])

    result = synopsis_enricher.enrich(text, keywords, title)

    if 'error' in result:
        err = result['error']
        err_lo = err.lower()
        if 'session limit' in err_lo or 'hit your' in err_lo:
            reset_dt = parse_reset_time(err)
            return 'token_limit', reset_dt
        # Autres erreurs → marquer et passer
        cat['docs'][uid].setdefault('enrichment', {})['summary'] = ''
        CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2))
        return 'error', err[:80]

    # Succès
    existing = d.get('enrichment') or {}
    existing.update(result)
    cat['docs'][uid]['enrichment'] = existing

    # Couverture
    if not d.get('cover'):
        try:
            import fitz, PIL.Image
            doc_fitz = fitz.open(str(pdf))
            pix = doc_fitz[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.thumbnail((400, 600))
            cover = ROOT / 'site' / 'assets' / 'covers' / f'{uid}.png'
            img.save(cover, "PNG")
            cat['docs'][uid]['cover'] = f'assets/covers/{uid}.png'
            doc_fitz.close()
        except Exception:
            pass

    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2))
    n_sum = len(result.get('summary', '') or '')
    n_cit = len(result.get('citations', []) or [])
    return 'ok', f'{n_sum}c,{n_cit}cit'

def publish_and_deploy():
    log('Publication en cours…')
    try:
        from datetime import datetime as dt
        watch.publish_site(dt.utcnow().strftime('%Y-%m-%d_%H-%M'))
        log('publish_site OK')
    except Exception as e:
        log(f'publish_site erreur: {e}')
        return

    import subprocess as sp
    res = sp.run(['python3', 'scripts/audit_site.py'], capture_output=True, text=True, cwd=str(ROOT))
    log(res.stdout.strip().split('\n')[-1])

    sp.run(['git', '-C', str(ROOT), 'add', '-A'])
    sp.run(['git', '-C', str(ROOT), 'commit', '-m',
            f'feat: enrichissement complet {datetime.date.today()}'],
           capture_output=True)
    sp.run(['git', '-C', str(ROOT), 'push'], capture_output=True)
    res = sp.run(['bash', 'scripts/publish_direct.sh'], capture_output=True, text=True, cwd=str(ROOT))
    log(res.stdout.strip() or res.stderr.strip() or 'publish_direct.sh OK')
    log('🎉 Déploiement terminé.')

def main():
    log('=== enrich_loop démarré ===')
    done = skipped = errors = 0

    while True:
        uids = pending_uids()
        if not uids:
            log(f'✅ Tout enrichi — done={done} skip={skipped} err={errors}')
            publish_and_deploy()
            sys.exit(0)

        log(f'{len(uids)} docs en attente…')
        uid = uids[0]
        title = json.loads(CATALOG.read_text())['docs'].get(uid, {}).get('title', '?')[:50]
        log(f'  → {uid} {title}')

        status, info = enrich_one(uid)

        if status == 'ok':
            log(f'  ✓ {uid} {info}')
            done += 1

        elif status == 'token_limit':
            reset_dt = info  # datetime UTC ou None
            if reset_dt:
                wait_secs = max(0, (reset_dt - datetime.datetime.now(datetime.timezone.utc)).total_seconds()) + 300
                wake = reset_dt + datetime.timedelta(seconds=300)
                log(f'⏸  Token limit. Reset détecté : {reset_dt.astimezone(ZoneInfo("Europe/Paris")).strftime("%H:%M")} Paris → reprise à {wake.astimezone(ZoneInfo("Europe/Paris")).strftime("%H:%M")} (dans {int(wait_secs//3600)}h{int((wait_secs%3600)//60)}min)')
            else:
                # Fallback : 20h05 Paris
                paris = ZoneInfo('Europe/Paris')
                now_paris = datetime.datetime.now(paris)
                reset_paris = now_paris.replace(hour=20, minute=5, second=0, microsecond=0)
                if reset_paris <= now_paris:
                    reset_paris += datetime.timedelta(days=1)
                wait_secs = (reset_paris - now_paris).total_seconds() + 300
                log(f'⏸  Token limit (heure non parsée). Reprise à 20h10 Paris (dans {int(wait_secs//3600)}h{int((wait_secs%3600)//60)}min)')
            time.sleep(wait_secs)
            log('⏰ Reprise après reset tokens.')

        elif status == 'skip':
            log(f'  ⏭  {uid} ({info})')
            skipped += 1

        else:  # error
            log(f'  ✗ {uid} {info}')
            errors += 1

if __name__ == '__main__':
    main()
