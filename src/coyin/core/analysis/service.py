from __future__ import annotations

import json
import re
from typing import Any

import requests

from coyin.core.analysis.models import AnalysisReport
from coyin.core.documents.models import DocumentDescriptor, DocumentSnapshot
from coyin.core.workspace.state import ProviderConfig


class AnalysisService:
    def __init__(self, plugin_manager=None):
        self.plugin_manager = plugin_manager

    def analyze(
        self,
        descriptor: DocumentDescriptor,
        snapshot: DocumentSnapshot,
        provider: ProviderConfig | None = None,
    ) -> AnalysisReport:
        if provider and provider.active and provider.api_key:
            try:
                report = self._analyze_remote(descriptor, snapshot, provider)
            except Exception:
                report = self._analyze_local(descriptor, snapshot)
        else:
            report = self._analyze_local(descriptor, snapshot)
        payload = {
            "title": report.title,
            "summary": report.summary,
            "contributions": report.contributions,
            "experiments": report.experiments,
            "method_steps": report.method_steps,
            "risks": report.risks,
            "comparison_rows": report.comparison_rows,
            "reading_note": report.reading_note,
            "latex_snippet": report.latex_snippet,
            "raw_fields": report.raw_fields,
        }
        if self.plugin_manager:
            for handler in self.plugin_manager.analysis_postprocessors():
                try:
                    payload = handler(payload)
                except Exception:
                    continue
        return AnalysisReport(
            title=payload["title"],
            summary=payload["summary"],
            contributions=payload["contributions"],
            experiments=payload["experiments"],
            method_steps=payload["method_steps"],
            risks=payload["risks"],
            comparison_rows=payload["comparison_rows"],
            reading_note=payload["reading_note"],
            latex_snippet=payload["latex_snippet"],
            raw_fields=payload.get("raw_fields", {}),
        )

    def _analyze_remote(self, descriptor: DocumentDescriptor, snapshot: DocumentSnapshot, provider: ProviderConfig) -> AnalysisReport:
        model = provider.analysis_model or provider.default_model
        prompt = (
            "你是科研论文分析器。请只返回 JSON，字段包括：summary, contributions, datasets, method_steps,"
            " experiments, risks, future_work, reproducibility, latex_snippet, reading_note。"
            " experiments 为数组，每项包含 label/value。内容使用中文，简洁正式。"
        )
        response = requests.post(
            provider.base_url.rstrip("/") + "/chat/completions",
            headers={"Authorization": f"Bearer {provider.api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "temperature": 0.2,
                "messages": [
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": f"标题：{descriptor.title}\n作者：{', '.join(descriptor.authors)}\n正文：\n{snapshot.raw_text[:16000]}",
                    },
                ],
            },
            timeout=90,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = self._extract_json(content)
        return self._normalize_report(descriptor, payload)

    def _extract_json(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", content, re.S)
            if match:
                return json.loads(match.group(0))
            raise

    def _normalize_report(self, descriptor: DocumentDescriptor, payload: dict[str, Any]) -> AnalysisReport:
        experiments = payload.get("experiments", [])
        normalized_rows: list[dict[str, str]] = []
        if isinstance(experiments, list):
            for item in experiments:
                if isinstance(item, dict):
                    normalized_rows.append({key: str(value) for key, value in item.items()})
                else:
                    normalized_rows.append({"label": "实验结果", "value": str(item)})
        return AnalysisReport(
            title=descriptor.title,
            summary=str(payload.get("summary", "")).strip(),
            contributions=[str(item).strip() for item in payload.get("contributions", []) if str(item).strip()],
            experiments=normalized_rows,
            method_steps=[str(item).strip() for item in payload.get("method_steps", []) if str(item).strip()],
            risks=[str(item).strip() for item in payload.get("risks", []) if str(item).strip()],
            comparison_rows=payload.get("comparison_rows", []),
            reading_note=str(payload.get("reading_note", "")).strip(),
            latex_snippet=str(payload.get("latex_snippet", "")).strip(),
            raw_fields={key: str(value) for key, value in payload.items() if key not in {"summary", "contributions", "experiments", "method_steps", "risks", "comparison_rows", "reading_note", "latex_snippet"}},
        )

    def _analyze_local(self, descriptor: DocumentDescriptor, snapshot: DocumentSnapshot) -> AnalysisReport:
        text = snapshot.raw_text or "未提取到正文内容。"
        sentences = re.split(r"(?<=[。！？.!?])\s+", text)
        summary = " ".join(sentences[:3]).strip()[:420] or descriptor.excerpt or "未生成摘要。"
        contributions = self._extract_candidates(text, [r"contribution", r"贡献", r"we propose", r"提出"], limit=4)
        if not contributions:
            contributions = [sentence.strip() for sentence in sentences[1:4] if sentence.strip()][:3]
        risks = self._extract_candidates(text, [r"limitation", r"局限", r"future work", r"未来工作"], limit=4)
        method_steps = self._extract_candidates(text, [r"method", r"framework", r"pipeline", r"方法"], limit=5)
        experiments = self._extract_metrics(text)
        reading_note = f"1. 先通读摘要与引言。\n2. 重点核对方法与实验设置。\n3. 与本地同主题论文做对照。\n\n{summary}"
        escaped_summary = summary.replace("%", "\\%")
        latex_snippet = (
            "\\subsection{文献综述条目}\n"
            f"{descriptor.title} 主要讨论了以下内容：{escaped_summary}\n"
        )
        comparison_rows = [
            {"维度": "研究问题", "内容": descriptor.metadata.get("subject", "") or "待与本地文献对照"},
            {"维度": "实验指标", "内容": experiments[0].get("value", "待补充") if experiments else "待补充"},
        ]
        return AnalysisReport(
            title=descriptor.title,
            summary=summary,
            contributions=contributions,
            experiments=experiments,
            method_steps=method_steps,
            risks=risks or ["局限待结合原文复核。"],
            comparison_rows=comparison_rows,
            reading_note=reading_note,
            latex_snippet=latex_snippet,
            raw_fields={
                "datasets": "; ".join(self._extract_candidates(text, [r"dataset", r"数据集"], limit=4)),
                "reproducibility": "; ".join(self._extract_candidates(text, [r"code", r"github", r"reproduce", r"复现"], limit=4)),
            },
        )

    def _extract_candidates(self, text: str, patterns: list[str], limit: int = 4) -> list[str]:
        sentences = re.split(r"(?<=[。！？.!?])\s+", text)
        result: list[str] = []
        for sentence in sentences:
            lowered = sentence.lower()
            if any(pattern.lower() in lowered for pattern in patterns):
                cleaned = " ".join(sentence.split()).strip()
                if cleaned and cleaned not in result:
                    result.append(cleaned[:180])
            if len(result) >= limit:
                break
        return result

    def _extract_metrics(self, text: str) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for match in re.finditer(r"([A-Za-z0-9_\-/ ]{2,20})\s*[:=]\s*([0-9]+(?:\.[0-9]+)?%?)", text):
            label = " ".join(match.group(1).split())
            value = match.group(2)
            rows.append({"label": label, "value": value})
            if len(rows) >= 6:
                break
        return rows or [{"label": "实验结果", "value": "待结合原文表格核对"}]
