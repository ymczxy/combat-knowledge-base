from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
import json
import urllib.request


@dataclass(frozen=True, slots=True)
class SourceHit:
    source: str
    external_id: str
    label: str
    description: str
    url: str
    aliases: tuple[str, ...] = ()


class JsonHttpClient:
    def get_json(self, url: str, timeout: float = 20.0) -> dict[str, Any]:
        request = urllib.request.Request(url, headers={"User-Agent": "CKB/1.3 (+https://github.com/ymczxy/combat-knowledge-base)"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))


class WikidataAdapter:
    endpoint = "https://www.wikidata.org/w/api.php"

    def __init__(self, client: JsonHttpClient | None = None) -> None:
        self.client = client or JsonHttpClient()

    def build_search_url(self, query: str, language: str = "en", limit: int = 10) -> str:
        params = {
            "action": "wbsearchentities",
            "search": query,
            "language": language,
            "uselang": language,
            "limit": str(limit),
            "format": "json",
            "origin": "*",
        }
        return f"{self.endpoint}?{urlencode(params)}"

    def parse_search(self, payload: dict[str, Any]) -> list[SourceHit]:
        hits: list[SourceHit] = []
        for row in payload.get("search", []):
            entity_id = str(row.get("id", ""))
            if not entity_id:
                continue
            aliases = tuple(str(item) for item in row.get("aliases", []) if item)
            hits.append(SourceHit(
                source="wikidata",
                external_id=entity_id,
                label=str(row.get("label", "")),
                description=str(row.get("description", "")),
                url=str(row.get("concepturi") or f"https://www.wikidata.org/wiki/{entity_id}"),
                aliases=aliases,
            ))
        return hits

    def search(self, query: str, language: str = "en", limit: int = 10) -> list[SourceHit]:
        return self.parse_search(self.client.get_json(self.build_search_url(query, language, limit)))


class MediaWikiAdapter:
    def __init__(self, language: str = "en", client: JsonHttpClient | None = None) -> None:
        self.language = language
        self.client = client or JsonHttpClient()

    @property
    def endpoint(self) -> str:
        return f"https://{self.language}.wikipedia.org/w/api.php"

    def build_search_url(self, query: str, limit: int = 10) -> str:
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": str(limit),
            "format": "json",
            "origin": "*",
        }
        return f"{self.endpoint}?{urlencode(params)}"

    def parse_search(self, payload: dict[str, Any]) -> list[SourceHit]:
        hits: list[SourceHit] = []
        for row in payload.get("query", {}).get("search", []):
            page_id = str(row.get("pageid", ""))
            title = str(row.get("title", ""))
            if not page_id or not title:
                continue
            slug = title.replace(" ", "_")
            hits.append(SourceHit(
                source=f"wikipedia_{self.language}",
                external_id=page_id,
                label=title,
                description=str(row.get("snippet", "")),
                url=f"https://{self.language}.wikipedia.org/wiki/{slug}",
            ))
        return hits

    def search(self, query: str, limit: int = 10) -> list[SourceHit]:
        return self.parse_search(self.client.get_json(self.build_search_url(query, limit)))
