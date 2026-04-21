from __future__ import annotations

from pathlib import Path

import requests

from coyin.core.documents.models import SearchResult
from coyin.core.search.sources import ArxivSource, CrossrefSource, DblpSource, OpenAlexSource, SearchSource


class SearchService:
    def __init__(self):
        self.sources: dict[str, SearchSource] = {
            "arxiv": ArxivSource(),
            "crossref": CrossrefSource(),
            "openalex": OpenAlexSource(),
            "dblp": DblpSource(),
        }

    def source_list(self) -> list[dict[str, str]]:
        return [{"source_id": key, "label": source.label} for key, source in self.sources.items()]

    def search(self, query: str, source_ids: list[str]) -> list[SearchResult]:
        results: list[SearchResult] = []
        for source_id in source_ids:
            source = self.sources.get(source_id)
            if not source:
                continue
            try:
                results.extend(source.search(query))
            except Exception as exc:
                results.append(
                    SearchResult(
                        result_id=f"{source_id}_error",
                        source_id=source_id,
                        title=f"{source.label} 检索失败",
                        authors=[],
                        year="",
                        item_type="错误",
                        abstract=str(exc),
                        landing_url="",
                    )
                )
        return sorted(results, key=lambda item: item.year, reverse=True)

    def download(self, result: SearchResult, target_dir: Path) -> Path:
        url = result.pdf_url or result.landing_url
        if not url:
            raise RuntimeError("当前条目没有可下载地址")
        response = requests.get(url, timeout=40)
        response.raise_for_status()
        suffix = ".pdf" if "pdf" in response.headers.get("Content-Type", "").lower() or url.endswith(".pdf") else ".html"
        target = target_dir / f"{result.source_id}_{result.result_id}{suffix}"
        target.write_bytes(response.content)
        return target
