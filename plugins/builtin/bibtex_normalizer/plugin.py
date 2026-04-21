import re


class BibtexNormalizerPlugin:
    def on_load(self, context):
        def normalize_bibtex(raw_text: str) -> str:
            lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
            header = lines[0] if lines else "@article{entry,"
            fields = sorted(lines[1:-1])
            closing = lines[-1] if len(lines) > 1 and lines[-1].endswith("}") else "}"
            return "\n".join([header, *fields, closing])

        def postprocess(payload: dict) -> dict:
            payload.setdefault("raw_fields", {})
            payload["raw_fields"]["bibtex_note"] = "如需纳入写作草稿，建议先统一 BibTeX 字段大小写与作者格式。"
            return payload

        context.register_command("normalize_bibtex", normalize_bibtex)
        context.register_analysis_postprocessor(postprocess)

    def on_enable(self, context):
        return None

    def on_disable(self, context):
        return None


def create_plugin():
    return BibtexNormalizerPlugin()
