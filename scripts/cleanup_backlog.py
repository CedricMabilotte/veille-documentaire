#!/usr/bin/env python3
"""cleanup_backlog.py — résorption locale du backlog de docs catalogués non lus.

Contexte (session #25, 2026-09-15) : 1197 docs du catalogue n'ont jamais reçu de
lecture (score_final absent). Les traiter par runs GitHub Actions coûterait
25-30 h de quota ; on les traite ici, sur la machine de Ced, où 800 PDF sont
déjà présents dans docs/.

Pour chaque doc « à traiter » (même critère que la veille :
watch._known_skip_reason) :
  1. PDF local, sinon téléchargement (watch.download_and_validate) ;
  2. chaîne d'enrichissement canonique de la veille (watch.analyse_pdf_and_enrich :
     dédup, couverture, métadonnées, synopsis, score post-lecture, bulle) ;
  3. fusion directe dans la fiche existante (enrichment, score_final, couverture,
     bulle, métadonnées, entrée runs[]) — sans passer par
     update_synopsis_catalog, qui indexe par file_uid(url) et créerait des
     fiches fantômes pour les clés réécrites ; latest_run / collected_date
     sont préservés (sinon les vieux docs repasseraient « nouveaux » dans le RSS).
Un doc qui ne peut pas être lu est MIS DE CÔTÉ avec une raison
(`enrich_abandon`), et la veille ne le retentera plus.

Limite de session Claude : pause jusqu'à l'heure de reset (+5 min), puis reprise
sur le même doc. Checkpoint catalogue tous les 10 docs, commit+push tous les 50.
Tous les REBUILD_EVERY docs, et en fin de backlog : déclenchement de
.github/workflows/rebuild-site.yml, qui régénère et publie le site en CI
(le site suit donc au fil de l'eau). En fin de backlog : traduction des
citations, dernier push, sync des PDF vers Drive.

Usage : setsid nohup python3 scripts/cleanup_backlog.py > /dev/null 2>&1 &
        python3 scripts/cleanup_backlog.py --status
Options : --limit N (s'arrêter après N docs, sans phase finale), --no-final
Log     : reports/cleanup_backlog.log
"""
from __future__ import annotations
import argparse, datetime as dt, json, os, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "scripts"))
PIDFILE = Path("/tmp/cleanup_backlog_biblio.pid")
LOG = ROOT / "reports" / "cleanup_backlog.log"
CATALOG = ROOT / "synopsis" / "catalog.json"
CHECKPOINT_EVERY = 10
COMMIT_EVERY = 50
DOWNLOAD_THRESHOLD = 4

RESET_RE = re.compile(r"resets?\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*\(([^)]+)\)", re.I)


def log(msg: str) -> None:
    line = f"[{dt.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if sys.stdout and sys.stdout.isatty():
        print(line)


def reset_wait_seconds(message: str) -> float:
    """Secondes à attendre d'après « resets 8:30pm (UTC) » ; défaut 1 h. Plafond 6 h."""
    from zoneinfo import ZoneInfo
    m = RESET_RE.search(message or "")
    if not m:
        return 3600
    h, mi, ampm, tz = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "").lower(), m.group(4)
    if ampm == "pm" and h < 12:
        h += 12
    if ampm == "am" and h == 12:
        h = 0
    try:
        zone = ZoneInfo(tz.strip())
    except Exception:
        zone = dt.timezone.utc
    now = dt.datetime.now(zone)
    target = now.replace(hour=h, minute=mi, second=0, microsecond=0)
    if target <= now:
        target += dt.timedelta(days=1)
    return min((target - now).total_seconds() + 300, 6 * 3600)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, text=True)


LOCAL_PATHS = ["synopsis/catalog.json", "synopsis/duplicates.json",
               "interface/covers", "bulles"]
REBUILD_EVERY = 50


def commit_push(message: str, paths: list[str] | None = None) -> bool:
    """Commit par plomberie, rebasé sur origin/main, puis push.

    - Clone partiel (--filter=blob:none), site/ non matérialisé : aucune
      commande porcelaine qui lirait l'index complet (commit, reset, status).
    - La CI (rebuild-site.yml) pousse site/ en parallèle : on reconstruit
      l'arbre depuis origin/main et on n'y remplace QUE nos fichiers
      (LOCAL_PATHS), jamais les autres — pas de conflit, pas de retour arrière.
    """
    paths = paths or LOCAL_PATHS
    for attempt in range(3):
        git("fetch", "-q", "origin", "main")
        base = git("rev-parse", "origin/main").stdout.strip()
        env = dict(os.environ, GIT_INDEX_FILE=str(ROOT / ".git" / "index-cleanup"))
        run = lambda *a: subprocess.run(["git", *a], capture_output=True, text=True, env=env)
        run("read-tree", base)
        files = []
        for pth in paths:
            pp = ROOT / pth
            files += [pp] if pp.is_file() else [f for f in pp.rglob("*") if f.is_file()]
        # --index-info : ajout en masse sans lire les blobs absents
        lines = []
        for f in files:
            oid = git("hash-object", "-w", str(f)).stdout.strip()
            lines.append(f"100644 {oid}\t{f.relative_to(ROOT).as_posix()}")
        subprocess.run(["git", "update-index", "--index-info"], input="\n".join(lines) + "\n",
                       capture_output=True, text=True, env=env)
        tree = run("write-tree", "--missing-ok").stdout.strip()
        if tree == git("rev-parse", f"{base}^{{tree}}").stdout.strip():
            return True  # rien de nouveau
        msg = (message + "\n\nCo-Authored-By: Claude Opus 5 <noreply@anthropic.com>\n"
               "Claude-Session: https://claude.ai/code/session_01BFvYB33vk7pWQSf27Lju7J")
        c = git("commit-tree", tree, "-p", base, "-m", msg).stdout.strip()
        p = git("push", "origin", f"{c}:refs/heads/main")
        if p.returncode == 0:
            git("update-ref", "refs/heads/main", c)
            git("read-tree", c)
            log(f"  git : {c[:8]} {message} / push ok")
            return True
        log(f"  … push refusé (tentative {attempt + 1}) : {p.stderr.strip()[:120]}")
        time.sleep(15)
    log("  ✗ push impossible après 3 tentatives")
    return False


def trigger_rebuild() -> None:
    r = subprocess.run(["gh", "workflow", "run", "rebuild-site.yml", "--ref", "main"],
                       capture_output=True, text=True)
    log(f"  🌐 rebuild-site.yml {'déclenché' if r.returncode == 0 else 'NON déclenché : ' + r.stderr.strip()[:120]}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-final", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    import watch, claude_guard

    def candidates() -> list[str]:
        cat = json.loads(CATALOG.read_text(encoding="utf-8"))
        known = cat["docs"]
        _, archived = watch._load_known_docs()
        local = {p.name.split("_", 1)[0] for p in watch.DOCS_PATH.glob("*_*")}
        # Par clé catalogue (et non par URL : 297 clés ≠ file_uid(url)).
        todo = [u for u, d in known.items()
                if u not in archived and watch._fiche_skip_reason(d, DOWNLOAD_THRESHOLD) is None]
        # Publiés d'abord, puis PDF déjà présents localement.
        todo.sort(key=lambda u: (not watch._is_publishable(known[u]), u not in local))
        return todo

    if args.status:
        cat = json.loads(CATALOG.read_text(encoding="utf-8"))["docs"]
        ab = [d["enrich_abandon"]["reason"] for d in cat.values() if d.get("enrich_abandon")]
        from collections import Counter
        running = PIDFILE.exists() and Path(f"/proc/{PIDFILE.read_text().strip()}").exists()
        print(f"process actif : {running}")
        print(f"reste à traiter : {len(candidates())}")
        print(f"lus (score_final) : {sum(1 for d in cat.values() if d.get('score_final') is not None)}")
        print(f"mis de côté : {len(ab)} {dict(Counter(r.split(' :')[0] for r in ab))}")
        print(f"publiables : {sum(1 for d in cat.values() if watch._is_publishable(d))}")
        return 0

    if PIDFILE.exists() and Path(f"/proc/{PIDFILE.read_text().strip()}").exists():
        print("cleanup_backlog déjà actif — sortie.")
        return 0
    PIDFILE.write_text(str(os.getpid()))
    import atexit
    atexit.register(lambda: PIDFILE.unlink(missing_ok=True))

    # Garde-fou : on ne travaille que sur un arbre à jour et propre côté catalogue.
    # Pas de `git pull` : sur ce clone partiel il rapatrierait des milliers de
    # blobs de site/. commit_push reconstruit chaque commit sur origin/main.
    git("fetch", "-q", "origin", "main")

    config = watch.load_config()
    keywords = config.get("keywords", [])
    langs = {s.get("label"): s.get("default_lang", "") for s in config.get("sources", [])}

    todo = candidates()
    log(f"=== cleanup_backlog démarré — {len(todo)} docs à traiter ===")
    run_date = "cleanup_" + dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d_%H-%M")
    pending: list[dict] = []          # résultats à fusionner
    abandons: dict[str, str] = {}     # uid -> raison
    retry: dict[str, str] = {}        # uid -> raison du 1er échec
    done = 0

    def flush() -> None:
        nonlocal pending, abandons
        if not pending and not abandons:
            return
        cat = json.loads(CATALOG.read_text(encoding="utf-8"))
        docs = cat["docs"]
        for r in pending:
            fiche = docs.get(r["uid"])
            if fiche is None:
                continue
            out = r["out"]
            enr = out.get("enrichment") or {}
            fiche.setdefault("runs", []).append({
                "date": run_date, "score": r["score"],
                "raison": "nettoyage backlog (lecture différée)",
                "context_seen": "", "link_text": r["link_text"],
                "downloaded": True, "model": "", "prompt_version": "",
            })
            fiche["enrichment"] = enr
            rs = enr.get("relevance_score")
            if isinstance(rs, (int, float)):
                fiche["score_final"] = int(rs)
            for k in ("cover", "bulle", "meta", "archive_url"):
                if out.get(k):
                    fiche[k] = out[k]
            for k, v in (out.get("bib") or {}).items():
                if k in ("doc_date", "lang", "editeur", "doi", "isbn", "hal_id") and v:
                    fiche[k] = v
            fiche["downloaded"] = True
            fiche["saved_as"] = r["saved_as"]
            if not fiche.get("title"):
                try:
                    t = watch.doc_metadata.normalize_title(
                        link_text=r["link_text"] or "",
                        pdf_title=(out.get("meta") or {}).get("pdf_title", "") or "",
                        filename=fiche.get("filename", "") or "",
                        author_hint=fiche.get("author", "") or "")
                    if t:
                        fiche["title"] = t
                except Exception:
                    pass
        today = dt.date.today().isoformat()
        for u, why in abandons.items():
            if u in docs:
                docs[u]["enrich_abandon"] = {"reason": why, "date": today}
        tmp = CATALOG.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(cat, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, CATALOG)
        pending, abandons = [], {}

    def process(uid: str, second_try: bool) -> str:
        """'ok' | 'fail:<raison>' | 'abandon:<raison>' | 'limit:<message>' | 'skip'"""
        cat = json.loads(CATALOG.read_text(encoding="utf-8"))["docs"]
        fiche = cat.get(uid)
        if not fiche:
            return "skip"
        url = fiche["url"]
        fn = fiche.get("filename") or "document.pdf"
        dest = None
        for cand in [fiche.get("saved_as")] + [str(p) for p in watch.DOCS_PATH.glob(f"{uid}_*")]:
            if cand and Path(cand).exists() and watch.pdf_processor.validate_pdf(Path(cand)):
                dest = Path(cand); break
        if dest is None:
            dest = watch.DOCS_PATH / f"{uid}_{fn}"
            ok, status = watch.download_and_validate(url, dest)
            if not ok:
                return f"fail:téléchargement impossible : {status}"
        link_text = next((r.get("link_text") for r in reversed(fiche.get("runs") or []) if r.get("link_text")), "")
        doc = {"url": url, "filename": fn, "extension": fiche.get("format", "pdf"),
               "link_text": link_text, "context": ""}
        score = fiche.get("score_initial") or fiche.get("latest_score") or 0
        out = watch.analyse_pdf_and_enrich(dest, doc, score, keywords,
                                           source_default_lang=langs.get(fiche.get("source"), ""),
                                           uid=uid)
        if claude_guard.session_limit_active():
            return "limit:" + claude_guard.session_limit_message()
        if out.get("duplicate_of"):
            return f"abandon:doublon de {out['duplicate_of']}"
        enr = out.get("enrichment")
        if not isinstance(enr, dict):
            return "abandon:pas de texte extractible (PDF scanné ?)"
        if "error" in enr:
            return f"fail:enrichissement raté : {str(enr['error'])[:120]}"
        r = {"uid": uid, "score": score, "link_text": link_text,
             "saved_as": str(dest), "out": out}
        pending.append(r)
        return "ok"

    queue = [(u, False) for u in todo]
    while queue:
        uid, second = queue.pop(0)
        status = process(uid, second)
        kind, _, info = status.partition(":")
        if kind == "limit":
            flush()
            wait = reset_wait_seconds(info)
            log(f"⏸  limite de session Claude — pause {wait/3600:.1f} h ({info[:80]})")
            time.sleep(wait)
            claude_guard._session_limit_hit = False
            claude_guard._session_limit_message = ""
            queue.insert(0, (uid, second))
            continue
        if kind == "ok":
            done += 1
            sf = (pending[-1]["out"].get("enrichment") or {}).get("relevance_score", "?")
            log(f"  ✓ {uid} lu — score post-lecture {sf}  [{done}]")
        elif kind == "fail" and not second:
            retry[uid] = info
            queue.append((uid, True))            # 2e tentative en fin de file
            log(f"  … {uid} échec, reporté en fin de file : {info}")
        elif kind in ("fail", "abandon"):
            abandons[uid] = info
            log(f"  ⊘ {uid} mis de côté : {info}")
        processed = done + len(abandons)
        if done and done % CHECKPOINT_EVERY == 0 and kind == "ok":
            flush()
        if kind == "ok" and done % COMMIT_EVERY == 0:
            flush()
            if commit_push(f"data(backlog): nettoyage — {done} docs lus") and done % REBUILD_EVERY == 0:
                trigger_rebuild()
        if args.limit and done + len(retry) >= args.limit:
            break
    flush()
    log(f"Backlog : {done} lus ; reste {len(candidates())} à traiter.")
    if commit_push(f"data(backlog): nettoyage — {done} docs lus (lot)") and not args.limit:
        trigger_rebuild()

    if args.limit or args.no_final:
        return 0

    log("Phase finale — traduction des citations, dernier push, reconstruction CI")
    try:
        st = watch.translate_citations.run(catalog_path=watch.SYNOPSIS_PATH / "catalog.json", verbose=False)
        log(f"  ✓ citations : {st}")
    except Exception as e:
        log(f"  ⚠ citations : {e}")
    if commit_push("data(backlog): fin du nettoyage — citations traduites"):
        trigger_rebuild()
    try:
        s = subprocess.run(["rclone", "copy", "docs/", "gdrive:Veille_documentaire/"],
                           capture_output=True, text=True, timeout=3600)
        log(f"  rclone docs → Drive : exit {s.returncode}")
    except Exception as e:
        log(f"  ⚠ rclone : {e}")
    log("=== cleanup_backlog terminé ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
