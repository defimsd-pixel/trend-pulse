# Trend Pulse — déploiement VOOXEN (VPS)

Base épinglée : `d8e5fdb` (v2.0.0). Ce dossier n'ajoute que des fichiers ; le code d'origine est inchangé.

**Ce qui tourne** : `api` (FastAPI, `127.0.0.1:8000` seulement), `worker` (un instantané par jour à 07h00, heure de Paris, puis une sauvegarde SQLite conservée 14 jours) et `caddy` (HTTPS Let's Encrypt, jeton Bearer obligatoire sauf `/health`, 60 requêtes/min par IP, lecture seule, CORS fermé). Pas de tableau de bord Streamlit, aucune clé LLM ni Cloudflare.

**Sources** : `google_trends` (FR), `google_news` (français : `hl=fr&gl=FR&ceid=FR:fr`), `wikipedia` (fr), `reddit` (r/france, r/vosfinances, r/entrepreneur_fr). `youtube_trending` est désactivé par défaut : il lit une page YouTube. Pour l'ajouter après test, compléter `TP_SOURCES` dans `.env`.

**Avant de commencer** : enregistrement DNS A `trends.vooxen.fr` → IP du VPS ; ports 80 et 443 libres (si Traefik ou nginx les occupe déjà, par exemple pour n8n, ne pas lancer le service `caddy` et router `trends.vooxen.fr` vers `127.0.0.1:8000` avec les mêmes règles).

## Installation (root, 5 commandes)

```bash
git clone -b vooxen-deploy https://github.com/defimsd-pixel/trend-pulse /opt/vooxen/trend-pulse && cd /opt/vooxen/trend-pulse/deploy/vooxen && git merge-base --is-ancestor d8e5fdbcf42cc02d0149ecb2b4ab1a93430c654e HEAD && echo "base d8e5fdb OK"
cp .env.example .env && sed -i "s/^TP_TOKEN=.*/TP_TOKEN=$(openssl rand -hex 32)/" .env && chmod 600 .env
mkdir -p /opt/vooxen/trend-pulse-data /opt/vooxen/trend-pulse-backups && chown 10001 /opt/vooxen/trend-pulse-data /opt/vooxen/trend-pulse-backups && systemctl enable docker
docker compose up -d --build
./check.sh            # puis, après 2 instantanés : ./check.sh "<mot-clé présent>"
```

Le jeton est dans `/opt/vooxen/trend-pulse/deploy/vooxen/.env` (lisible par root seul). Le copier depuis le serveur vers le gestionnaire de mots de passe ; ne jamais le coller dans Git ni dans une conversation.

**Vérifier le redémarrage** : `reboot`, puis `./check.sh` (les trois services ont `restart: unless-stopped`).

**Sauvegardes** : `/opt/vooxen/trend-pulse-backups/history-AAAA-MM-JJ.db`, une par jour, 14 jours. À copier aussi hors du VPS.
