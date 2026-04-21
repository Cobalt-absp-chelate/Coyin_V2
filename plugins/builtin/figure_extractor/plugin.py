import re


class FigureExtractorPlugin:
    def on_load(self, context):
        def postprocess(payload: dict) -> dict:
            text = " ".join(
                [
                    payload.get("summary", ""),
                    " ".join(payload.get("contributions", [])),
                    " ".join(item.get("value", "") for item in payload.get("experiments", [])),
                ]
            )
            hits = re.findall(r"(Fig\.?\s*\d+|Figure\s*\d+|Table\s*\d+|表\s*\d+|图\s*\d+)", text, re.I)
            if hits:
                payload.setdefault("raw_fields", {})
                payload["raw_fields"]["figure_mentions"] = "；".join(dict.fromkeys(hits))
            return payload

        context.register_analysis_postprocessor(postprocess)

    def on_enable(self, context):
        return None

    def on_disable(self, context):
        return None


def create_plugin():
    return FigureExtractorPlugin()
