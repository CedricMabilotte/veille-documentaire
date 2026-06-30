#!/bin/bash
# enrich_loop.sh — Enrichit en boucle, reprend après reset tokens (20h Paris = 18h UTC).
# Un seul process à la fois garanti par le PID file.

ROOT="/home/ced/Documents/Claude/Projects/biblio"
LOG="$ROOT/reports/enrich_loop.log"
PIDFILE="/tmp/enrich_loop.pid"
mkdir -p "$ROOT/reports"

# Vérification unicité
if [ -f "$PIDFILE" ]; then
    OLD=$(cat "$PIDFILE")
    if kill -0 "$OLD" 2>/dev/null; then
        echo "Déjà en cours (PID $OLD). Sortie." | tee -a "$LOG"
        exit 1
    fi
fi
echo $$ > "$PIDFILE"
trap "rm -f $PIDFILE" EXIT

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"; }

log "=== enrich_loop démarré (PID $$) ==="

while true; do
    log "Lancement enrich_pending.py…"
    cd "$ROOT"
    PYTHONUNBUFFERED=1 python3 scripts/enrich_pending.py >> "$LOG" 2>&1
    EXIT=$?

    if [ $EXIT -eq 0 ]; then
        log "✅ Tout enrichi ! Publication…"
        python3 -c "
import sys,os
from datetime import datetime
sys.path.insert(0,'scripts')
os.environ['PUBLISH_THRESHOLD']='4'
import watch
watch.publish_site(datetime.utcnow().strftime('%Y-%m-%d_%H-%M'))
" >> "$LOG" 2>&1
        python3 scripts/audit_site.py >> "$LOG" 2>&1
        git -C "$ROOT" add -A && \
          git -C "$ROOT" commit -m "feat: enrichissement complet $(date '+%Y-%m-%d')" >> "$LOG" 2>&1 && \
          git -C "$ROOT" push >> "$LOG" 2>&1
        bash "$ROOT/scripts/publish_direct.sh" >> "$LOG" 2>&1 \
          || log "publish_direct.sh raté — GitHub Action prendra le relais."
        log "🎉 Fini."
        exit 0

    elif [ $EXIT -eq 2 ]; then
        # Calculer secondes jusqu'au prochain 18h05 UTC
        NOW=$(date -u +%s)
        TODAY_RESET=$(date -u +%s -d "$(date -u +%Y-%m-%d) 18:05:00" 2>/dev/null)
        if [ -z "$TODAY_RESET" ]; then
            # Fallback si date -d non disponible (macOS)
            H=$(date -u +%H); M=$(date -u +%M)
            SECS_SINCE_MIDNIGHT=$(( H*3600 + M*60 ))
            RESET_SECS=$(( 18*3600 + 5*60 ))
            if [ $SECS_SINCE_MIDNIGHT -lt $RESET_SECS ]; then
                WAIT=$(( RESET_SECS - SECS_SINCE_MIDNIGHT ))
            else
                WAIT=$(( 86400 - SECS_SINCE_MIDNIGHT + RESET_SECS ))
            fi
        else
            if [ "$TODAY_RESET" -gt "$NOW" ]; then
                WAIT=$(( TODAY_RESET - NOW ))
            else
                WAIT=$(( TODAY_RESET + 86400 - NOW ))
            fi
        fi
        WAIT=$(( WAIT + 30 ))  # marge 30s
        log "⏸  Token limit. Reprise dans ${WAIT}s (~$(( WAIT/3600 ))h$(( (WAIT%3600)/60 ))min)."
        sleep "$WAIT"
        log "⏰ Reprise après reset tokens."

    else
        log "❌ Exit inattendu ($EXIT) — pause 120s."
        sleep 120
    fi
done
