"""VOOXEN — Trend Pulse restreint à la France (fork @ d8e5fdb, v2.0.0).

Réutilise l'API FastAPI et l'agrégateur d'origine sans modifier leur code :
sources limitées à la liste VOOXEN, Google News en français, Reddit limité
aux subreddits français, CORS ouvert d'origine retiré. Aucun appel à un LLM.
"""

from __future__ import annotations

import os

import httpx
from fastapi.middleware.cors import CORSMiddleware

from trend_pulse.aggregator import TrendAggregator
from trend_pulse.dashboard import api as upstream
from trend_pulse.sources.google_news import GoogleNewsSource
from trend_pulse.sources.reddit import RedditSource

# youtube_trending lit une page YouTube : à ajouter dans TP_SOURCES seulement après test sur le VPS.
ALLOWED = [s.strip() for s in os.environ.get(
    "TP_SOURCES", "google_trends,google_news,wikipedia,reddit").split(",") if s.strip()]
DEFAULT_GEO = os.environ.get("TP_GEO", "FR")
SUBREDDITS = os.environ.get("TP_SUBREDDITS", "france+vosfinances+entrepreneur_fr")

# Google News en français : hl=fr&gl=FR&ceid=FR:fr
GoogleNewsSource.GEO_LANG = {**GoogleNewsSource.GEO_LANG, "FR": "fr"}


class FrenchRedditSource(RedditSource):
    """Reddit limité aux subreddits français (tendances et recherche)."""

    URL = f"https://www.reddit.com/r/{SUBREDDITS}/hot.json"

    async def search(self, query: str, geo: str = ""):
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"https://www.reddit.com/r/{SUBREDDITS}/search.json",
                params={"q": query, "restrict_sr": 1, "sort": "relevance", "limit": 20},
                headers={"User-Agent": self.USER_AGENT},
            )
            resp.raise_for_status()
            data = resp.json()
        return self._parse_posts(data.get("data", {}).get("children", []))


class RestrictedAggregator(TrendAggregator):
    """Agrégateur limité aux sources VOOXEN ; toute autre source est refusée."""

    def __init__(self) -> None:
        super().__init__()
        self._instances["reddit"] = FrenchRedditSource()
        self._instances = {n: s for n, s in self._instances.items() if n in ALLOWED}

    def _select(self, names):
        if not names:
            return self._instances
        return {n: self._instances[n] for n in names if n in self._instances}

    async def trending(self, sources=None, geo: str = "", count: int = 20, save: bool = False):
        return await super().trending(sources=sources, geo=geo or DEFAULT_GEO, count=count, save=save)

    async def search(self, query: str, sources=None, geo: str = ""):
        return await super().search(query=query, sources=sources, geo=geo or DEFAULT_GEO)


upstream._agg = RestrictedAggregator()
app = upstream.app
# CORS fermé : seul le serveur VOOXEN appelle cette API.
app.user_middleware = [m for m in app.user_middleware if m.cls is not CORSMiddleware]
app.middleware_stack = None
