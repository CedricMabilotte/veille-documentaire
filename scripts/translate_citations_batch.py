#!/usr/bin/env python3
"""
translate_citations_batch.py — Traduit les citations en français par lots de 20.
Reprend là où il s'était arrêté (idempotent : skip les quote_fr déjà remplis).
Sortie propre :
  exit 0 — tout traduit
  exit 2 — token limit (enrich_loop relancera plus tard)
  exit 1 — erreur fatale
"""
import sys, os, json, re, datetime, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
os.environ.setdefault('PUBLISH_THRESHOLD', '4')

CATALOG = ROOT / 'synopsis' / 'catalog.json'
LOG     = ROOT / 'reports' / 'translate_batch.log'
LOG.parent.mkdir(exist_ok=True)

CLAUDE_MODEL = 'claude-haiku-4-5'
CLAUDE_FLAGS = [
    '--output-format', 'text',
    '--no-session-persistence',
    '--disable-slash-commands',
    '--dangerously-skip-permissions',
]
BATCH_SIZE = 15

def log(msg):
    ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{ts}] {msg}'
    print(line, flush=True)
    with open(LOG, 'a') as f: f.write(line + '\n')

def load_cat():
    return json.loads(CATALOG.read_text())

def save_cat(cat):
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2))

def pending_items(cat):
    """Retourne [(uid, i_cit, quote, lang)] pour les citations sans quote_fr."""
    items = []
    published = set(
        f.stem for f in Path('site/fiches').iterdir()
        if f.suffix == '.html' and f.stem not in ('index','fiche')
    )
    for uid in published:
        d = cat['docs'].get(uid)
        if not d: continue
        e = d.get('enrichment') or {}
        for i, c in enumerate(e.get('citations') or []):
            if not isinstance(c, dict): continue
            quote = (c.get('quote') or '').strip()
            if not quote: continue
            if (c.get('quote_fr') or '').strip(): continue
            lang = d.get('lang', 'en')
            if lang == 'fr':
                # Pour doc FR : traduire seulement si le quote semble non-FR
                fr_words = set('le la les un une des de du et est')
                words_lower = set(quote.lower().split())
                if len(fr_words & words_lower) >= 2:
                    continue  # semble déjà en FR
            items.append((uid, i, quote, lang))
    return items

def translate_batch(items):
    """Traduit une liste de citations via claude. Retourne dict uid:i → quote_fr ou 'token_limit'."""
    numbered = '\n'.join(f'{j+1}. [{item[3]}] {item[2]}' for j, item in enumerate(items))
    prompt = f"""Traduis ces {len(items)} citations en français (une par ligne, garde le numéro).
Langue source indiquée entre crochets. Retourne UNIQUEMENT les traductions numérotées, pas d'autre texte.
Format : "1. <traduction>"

Citations :
{numbered}"""
    try:
        r = subprocess.run(
            ['claude', '-p', prompt, '--model', CLAUDE_MODEL] + CLAUDE_FLAGS,
            capture_output=True, text=True, timeout=180, cwd='/tmp', stdin=subprocess.DEVNULL
        )
    except subprocess.TimeoutExpired:
        return 'timeout'
    if r.returncode != 0:
        err = (r.stdout + r.stderr)
        if 'session limit' in err.lower() or 'token' in err.lower() or 'usage limit' in err.lower():
            return 'token_limit'
        log(f'  ✗ erreur claude : {err[:100]}')
        return {}
    # Parser les réponses
    result = {}
    for line in r.stdout.strip().split('\n'):
        m = re.match(r'^(\d+)\.\s*(.*)', line.strip())
        if m:
            idx = int(m.group(1)) - 1
            if 0 <= idx < len(items):
                uid, i_cit, _, _ = items[idx]
                result[(uid, i_cit)] = m.group(2).strip()
    return result

def main():
    log('=== translate_citations_batch démarré ===')
    cat = load_cat()
    items = pending_items(cat)
    if not items:
        log('✅ Toutes les citations sont traduites.')
        sys.exit(0)
    log(f'{len(items)} citations à traduire, par lots de {BATCH_SIZE}')
    done = 0
    for start in range(0, len(items), BATCH_SIZE):
        batch = items[start:start + BATCH_SIZE]
        result = translate_batch(batch)
        if result == 'token_limit' or result == 'timeout':
            log(f'⏸  Token limit après {done} traductions.')
            sys.exit(2)
        if not result:
            log(f'  ⚠  lot {start//BATCH_SIZE+1} : aucune traduction récupérée')
            continue
        # Recharger + patcher + sauver
        cat = load_cat()
        for (uid, i_cit), quote_fr in result.items():
            try:
                cat['docs'][uid]['enrichment']['citations'][i_cit]['quote_fr'] = quote_fr
            except (KeyError, IndexError, TypeError):
                pass
        save_cat(cat)
        done += len(result)
        log(f'  ✓ lot {start//BATCH_SIZE+1} : {len(result)}/{len(batch)} traduits (total {done})')
    log(f'✅ Traductions terminées — {done} citations.')
    sys.exit(0)

if __name__ == '__main__':
    main()
