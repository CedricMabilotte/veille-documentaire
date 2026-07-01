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
    """Phase 1 : summary manquant. Phase 2 : en_clair manquant."""
    cat = json.loads(CATALOG.read_text())
    phase1, phase2 = [], []
    for uid, d in cat['docs'].items():
        if not watch._is_publishable(d): continue
        enr = d.get('enrichment') or {}
        fn = d.get('filename', '')
        pdf = DOCS / fn if fn else None
        if not pdf or not pdf.exists():
            pdf = next(iter(list(DOCS.glob(f'{uid}_*.pdf'))), None)
        has_pdf = pdf and pdf.exists()
        has_summary = bool((enr.get('summary') or '').strip())
        has_enclair = bool((enr.get('en_clair') or '').strip())
        if not has_summary and 'summary' not in enr and has_pdf:
            phase1.append(uid)
        elif has_summary and not has_enclair:
            phase2.append(uid)  # pas besoin de PDF, on génère depuis le summary
    return phase1 + phase2

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
    has_summary = bool((enr.get('summary') or '').strip())
    has_enclair = bool((enr.get('en_clair') or '').strip())
    if has_summary and has_enclair:
        return 'skip', 'already'

    fn = d.get('filename', '')
    pdf = DOCS / fn if fn else None
    if not pdf or not pdf.exists():
        pdf = next(iter(list(DOCS.glob(f'{uid}_*.pdf'))), None)
    if not pdf or not pdf.exists():
        return 'skip', 'no_pdf'

    # Phase 2 : en_clair manquant alors que summary présent → générer depuis summary
    if has_summary and not has_enclair:
        summary_txt = enr.get('summary', '')
        import subprocess as _sp
        prompt = (
            "En deux phrases simples en français (accessibles à tous), explique l'essentiel "
            "de ce document dont voici le résumé :\n\n" + summary_txt[:1200] +
            "\n\nRéponds uniquement avec l'explication, sans titre ni introduction."
        )
        r = _sp.run(
            ['claude','-p', prompt,'--model','claude-haiku-4-5',
             '--output-format','text','--no-session-persistence',
             '--dangerously-skip-permissions'],
            capture_output=True, text=True, timeout=120, cwd='/tmp', stdin=_sp.DEVNULL
        )
        combined = r.stdout + r.stderr
        if 'session limit' in combined.lower() or 'hit your' in combined.lower():
            return 'token_limit', parse_reset_time(combined)
        if r.returncode == 0 and r.stdout.strip():
            enr2 = d.get('enrichment') or {}
            enr2['en_clair'] = r.stdout.strip()
            cat['docs'][uid]['enrichment'] = enr2
            CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2))
            return 'ok', f'en_clair ({len(r.stdout.strip())}c)'
        return 'error', f'en_clair failed (exit {r.returncode})'
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
            log(f'✅ Summaries + en_clair terminés — done={done} skip={skipped} err={errors}')
            break

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
            # Garde-fou : jamais plus de 6h de sleep (évite les process zombies)
            MAX_SLEEP = 6 * 3600
            if wait_secs > MAX_SLEEP:
                log(f'⚠  wait_secs={wait_secs:.0f}s > 6h — plafonné à {MAX_SLEEP}s')
                wait_secs = MAX_SLEEP
            # Sleep par tranches de 5 min pour rester réactif
            CHUNK = 300
            elapsed = 0
            while elapsed < wait_secs:
                chunk = min(CHUNK, wait_secs - elapsed)
                time.sleep(chunk)
                elapsed += chunk
            log('⏰ Reprise après reset tokens.')

        elif status == 'skip':
            log(f'  ⏭  {uid} ({info})')
            skipped += 1

        else:  # error
            log(f'  ✗ {uid} {info}')
            errors += 1

    # ── Phase 3 : traduction des citations ──────────────────────────────
    log('Phase 3 — traduction des citations en français…')
    r = subprocess.run(
        [sys.executable, str(ROOT / 'scripts' / 'translate_citations_batch.py')],
        cwd=str(ROOT)
    )
    if r.returncode == 2:
        log('⏸  Token limit pendant la traduction — sera repris au prochain cycle.')
        sys.exit(2)
    elif r.returncode == 0:
        log('✅ Traductions citations terminées.')
    else:
        log(f'⚠  translate_citations_batch exit {r.returncode}')
    publish_and_deploy()
    sys.exit(0)

if __name__ == '__main__':
    main()
