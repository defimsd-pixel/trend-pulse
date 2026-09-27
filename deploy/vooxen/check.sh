#!/usr/bin/env bash
# Vérifications VOOXEN. Le jeton est lu dans .env et n'est jamais affiché.
# Usage : ./check.sh [mot-clé présent dans l'historique]
set -u
cd "$(dirname "$0")"
set -a; . ./.env; set +a
BASE="https://${TP_DOMAIN}"
auth() { printf 'Authorization: Bearer %s\n' "$TP_TOKEN"; }
code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }

echo "health sans jeton            : $(code "$BASE/health") (attendu 200)"
echo "trending sans jeton          : $(code "$BASE/trending?geo=FR&sources=google_trends,google_news&count=10") (attendu 401)"
echo "trending avec jeton          : $(auth | code -H @- "$BASE/trending?geo=FR&sources=google_trends,google_news&count=10") (attendu 200)"
auth | curl -s -H @- "$BASE/trending?geo=FR&sources=google_trends,google_news&count=10" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('  sources OK', d['sources_ok'], 'erreurs', list(d['sources_error'])); [print('  -', i['source'], i['keyword'][:80]) for i in d['merged'][:5]]"
auth | curl -s -H @- "$BASE/search?q=diagnostic%20immobilier&geo=FR" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print('search diagnostic immobilier  :', json.dumps(d, ensure_ascii=False)[:300])"
if [ -n "${1:-}" ]; then
  auth | curl -s -H @- "$BASE/history?keyword=$(python3 -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1]))' "$1")&days=7" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); print('history', d.get('keyword'), ':', d.get('count'), 'enregistrement(s) (attendu >= 2 après 2 instantanés)')"
fi
docker compose ps --format '{{.Service}} {{.State}}'
