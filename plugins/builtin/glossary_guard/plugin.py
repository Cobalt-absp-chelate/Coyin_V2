import re


class GlossaryGuardPlugin:
    def on_load(self, context):
        def postprocess(payload: dict) -> dict:
            summary = payload.get("summary", "")
            acronyms = re.findall(r"\b[A-Z]{2,6}\b", summary)
            if acronyms:
                payload.setdefault("raw_fields", {})
                payload["raw_fields"]["glossary_watch"] = "、".join(dict.fromkeys(acronyms))
            return payload

        def writer_actions():
            return [
                {
                    "id": "check_glossary_consistency",
                    "label": "检查术语一致性",
                    "hint": "扫描当前草稿中的英文缩写与术语写法。",
                }
            ]

        context.register_analysis_postprocessor(postprocess)
        context.register_writer_actions(writer_actions)

    def on_enable(self, context):
        return None

    def on_disable(self, context):
        return None


def create_plugin():
    return GlossaryGuardPlugin()
