import re


class MetadataEnricherPlugin:
    def on_load(self, context):
        def on_import(payload: dict):
            descriptor = payload.get("descriptor", {})
            excerpt = descriptor.get("excerpt", "")
            doi = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", excerpt)
            arxiv = re.search(r"arXiv:\s*([0-9.]+)", excerpt, re.I)
            hints = []
            if doi:
                hints.append(f"DOI: {doi.group(0)}")
            if arxiv:
                hints.append(f"arXiv: {arxiv.group(1)}")
            if hints:
                descriptor.setdefault("metadata", {})
                descriptor["metadata"]["import_hints"] = hints

        context.register_document_import_hook(on_import)

    def on_enable(self, context):
        return None

    def on_disable(self, context):
        return None


def create_plugin():
    return MetadataEnricherPlugin()
