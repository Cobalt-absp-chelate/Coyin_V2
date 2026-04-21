from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod

import requests

from coyin.core.common import short_id
from coyin.core.documents.models import SearchResult


class SearchSource(ABC):
    source_id: str
    label: str

    @abstractmethod
    def search(self, query: str, limit: int = 12) -> list[SearchResult]:
        raise NotImplementedError


class ArxivSource(SearchSource):
    source_id = "arxiv"
    label = "arXiv"

    def search(self, query: str, limit: int = 12) -> list[SearchResult]:
        url = (
            "https://export.arxiv.org/api/query?"
            + urllib.parse.urlencode({"search_query": f"all:{query}", "start": 0, "max_results": limit})
        )
        response = requests.get(url, headers={"User-Agent": "Coyin/0.1"}, timeout=45)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        namespace = {"a": "http://www.w3.org/2005/Atom"}
        results: list[SearchResult] = []
        for entry in root.findall("a:entry", namespace):
            title = (entry.findtext("a:title", default="", namespaces=namespace) or "").strip().replace("\n", " ")
            abstract = (entry.findtext("a:summary", default="", namespaces=namespace) or "").strip().replace("\n", " ")
            authors = [item.findtext("a:name", default="", namespaces=namespace) for item in entry.findall("a:author", namespace)]
            published = entry.findtext("a:published", default="", namespaces=namespace) or ""
            year = published[:4]
            landing = ""
            pdf_url = ""
            for link in entry.findall("a:link", namespace):
                href = link.attrib.get("href", "")
                link_type = link.attrib.get("title", "")
                if not landing:
                    landing = href
                if link_type == "pdf":
                    pdf_url = href
            results.append(
                SearchResult(
                    result_id=short_id("arxiv"),
                    source_id=self.source_id,
                    title=title,
                    authors=[name for name in authors if name],
                    year=year,
                    item_type="预印本",
                    abstract=abstract,
                    landing_url=landing,
                    pdf_url=pdf_url,
                    raw={"published": published},
                )
            )
        return results


class CrossrefSource(SearchSource):
    source_id = "crossref"
    label = "Crossref"

    def search(self, query: str, limit: int = 12) -> list[SearchResult]:
        response = requests.get(
            "https://api.crossref.org/works",
            params={"query": query, "rows": limit, "select": "DOI,title,author,type,issued,URL,container-title,abstract"},
            headers={"User-Agent": "Coyin/0.1"},
            timeout=20,
        )
        response.raise_for_status()
        items = response.json().get("message", {}).get("items", [])
        results: list[SearchResult] = []
        for item in items:
            title_list = item.get("title", [])
            title = title_list[0] if title_list else "未命名条目"
            authors = []
            for author in item.get("author", []):
                parts = [author.get("given", ""), author.get("family", "")]
                authors.append(" ".join(part for part in parts if part).strip())
            year_parts = item.get("issued", {}).get("date-parts", [[]])
            year = str(year_parts[0][0]) if year_parts and year_parts[0] else ""
            abstract = (item.get("abstract") or "").replace("<jats:p>", "").replace("</jats:p>", "")
            venue = item.get("container-title", [""])
            results.append(
                SearchResult(
                    result_id=short_id("crossref"),
                    source_id=self.source_id,
                    title=title,
                    authors=[author for author in authors if author],
                    year=year,
                    item_type=item.get("type", "文献"),
                    abstract=abstract,
                    landing_url=item.get("URL", ""),
                    doi=item.get("DOI", ""),
                    venue=venue[0] if venue else "",
                    raw=item,
                )
            )
        return results


class OpenAlexSource(SearchSource):
    source_id = "openalex"
    label = "OpenAlex"

    def search(self, query: str, limit: int = 12) -> list[SearchResult]:
        response = requests.get(
            "https://api.openalex.org/works",
            params={"search": query, "per-page": limit},
            headers={"User-Agent": "Coyin/0.1"},
            timeout=20,
        )
        response.raise_for_status()
        items = response.json().get("results", [])
        results: list[SearchResult] = []
        for item in items:
            authors = [author.get("author", {}).get("display_name", "") for author in item.get("authorships", [])]
            abstract = ""
            inverted = item.get("abstract_inverted_index", {})
            if inverted:
                words = [(position, word) for word, positions in inverted.items() for position in positions]
                abstract = " ".join(word for _, word in sorted(words)[:200])
            location = item.get("primary_location", {}) or {}
            source = (location.get("source") or {}).get("display_name", "")
            pdf_url = (location.get("pdf_url") or "") if isinstance(location, dict) else ""
            results.append(
                SearchResult(
                    result_id=short_id("openalex"),
                    source_id=self.source_id,
                    title=item.get("display_name", "未命名条目"),
                    authors=[author for author in authors if author],
                    year=str(item.get("publication_year") or ""),
                    item_type=item.get("type", "文献"),
                    abstract=abstract,
                    landing_url=item.get("id", ""),
                    pdf_url=pdf_url,
                    doi=(item.get("doi") or "").replace("https://doi.org/", ""),
                    venue=source,
                    raw=item,
                )
            )
        return results


class DblpSource(SearchSource):
    source_id = "dblp"
    label = "DBLP"

    def search(self, query: str, limit: int = 12) -> list[SearchResult]:
        response = requests.get(
            "https://dblp.org/search/publ/api",
            params={"q": query, "h": limit, "format": "json"},
            headers={"User-Agent": "Coyin/0.1"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json().get("result", {}).get("hits", {}).get("hit", [])
        results: list[SearchResult] = []
        for item in payload:
            info = item.get("info", {})
            authors_field = info.get("authors", {}).get("author", [])
            if isinstance(authors_field, dict):
                authors = [authors_field.get("text", "")]
            else:
                authors = [entry.get("text", "") if isinstance(entry, dict) else str(entry) for entry in authors_field]
            results.append(
                SearchResult(
                    result_id=short_id("dblp"),
                    source_id=self.source_id,
                    title=info.get("title", "未命名条目"),
                    authors=[author for author in authors if author],
                    year=str(info.get("year", "")),
                    item_type=info.get("type", "文献"),
                    abstract=info.get("venue", ""),
                    landing_url=info.get("url", ""),
                    venue=info.get("venue", ""),
                    raw=info,
                )
            )
        return results
