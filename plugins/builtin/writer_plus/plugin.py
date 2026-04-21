
class WriterPlusPlugin:
    def on_load(self, context):
        def writer_actions():
            return [
                {
                    "id": "insert_reference_stub",
                    "label": "插入引用占位",
                    "hint": "插入规范的文献引用占位文本。",
                },
                {
                    "id": "insert_method_scaffold",
                    "label": "插入方法小节",
                    "hint": "插入适合论文写作的方法小节骨架。",
                },
            ]

        context.register_writer_actions(writer_actions)

    def on_enable(self, context):
        return None

    def on_disable(self, context):
        return None


def create_plugin():
    return WriterPlusPlugin()
