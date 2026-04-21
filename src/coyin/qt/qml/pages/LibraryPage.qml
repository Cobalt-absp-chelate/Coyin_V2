import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../support/UiDefaults.js" as UiDefaults

ScrollView {
    id: root
    property var controller: null
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())

    readonly property var filterState: controller ? controller.libraryFilterState : UiDefaults.libraryFilterState()
    readonly property var groups: controller ? controller.groupModel : null
    readonly property var kindOptions: controller ? controller.libraryKindModel : null
    readonly property var documents: controller ? controller.libraryModel : null

    contentWidth: availableWidth

    Column {
        width: root.availableWidth
        spacing: 18

        SectionCard {
            width: parent.width
            title: "资料筛选"
            caption: "主列表已经直接依赖正式模型，不再让页面自己吃松散数组。"
            panelColor: root.theme.panelRaised
            borderColor: root.theme.border
            textColor: root.theme.text
            captionColor: root.theme.textSoft
            accentColor: root.theme.anchor
            accentSoft: root.theme.accentSoft

            Row {
                spacing: 10
                InteractiveTextField {
                    width: 320
                    theme: root.theme
                    placeholderText: "按标题、作者、来源或标签筛选"
                    text: root.filterState.query
                    onTextChanged: if (root.controller) root.controller.setLibrarySearchQuery(text)
                }
                InteractiveButton { theme: root.theme; text: root.filterState.recent_only ? "仅看最近打开" : "全部记录"; selected: root.filterState.recent_only; onClicked: if (root.controller) root.controller.setLibraryRecentOnly(!root.filterState.recent_only) }
                InteractiveButton { theme: root.theme; text: "清空筛选"; onClicked: if (root.controller) root.controller.clearLibraryFilters() }
                InteractiveButton { theme: root.theme; text: "批量导入"; onClicked: if (root.controller) root.controller.importDocuments() }
                InteractiveButton { theme: root.theme; text: "新建文档"; tone: "accent"; onClicked: if (root.controller) root.controller.createWriterDocument() }
            }

            Text {
                text: "当前显示 " + root.filterState.visible_count + " / " + root.filterState.total_count + " 份资料。"
                color: root.theme.textSoft
            }

            Text { text: "分组"; color: root.theme.textMuted; font.weight: Font.DemiBold }
            Flow {
                width: parent.width
                spacing: 8

                InteractiveChip { theme: root.theme; text: "全部分组"; checked: root.filterState.group_id === "all"; onClicked: if (root.controller) root.controller.setLibraryGroupFilter("all") }

                Repeater {
                    model: root.groups
                    delegate: InteractiveChip {
                        theme: root.theme
                        text: name + "  " + document_count
                        checked: root.filterState.group_id === group_id
                        markColor: group_color
                        onClicked: if (root.controller) root.controller.setLibraryGroupFilter(group_id)
                    }
                }
            }

            Text { text: "类型"; color: root.theme.textMuted; font.weight: Font.DemiBold }
            Flow {
                width: parent.width
                spacing: 8

                Repeater {
                    model: root.kindOptions
                    delegate: InteractiveChip {
                        theme: root.theme
                        text: label + "  " + count
                        checked: root.filterState.kind === id
                        onClicked: if (root.controller) root.controller.setLibraryKindFilter(id)
                    }
                }
            }
        }

        SectionCard {
            visible: !root.documents || root.documents.count === 0
            width: parent.width
            title: "当前资料视图"
            panelColor: root.theme.panelRaised
            borderColor: root.theme.border
            textColor: root.theme.text
            captionColor: root.theme.textSoft
            accentColor: root.theme.anchor
            accentSoft: root.theme.accentSoft

            Text {
                width: parent.width
                text: "当前筛选下无结果"
                color: root.theme.textMuted
                wrapMode: Text.Wrap
            }
        }

        Repeater {
            model: root.documents
            delegate: DocumentLibraryCard {
                width: root.availableWidth
                itemData: ({
                    "document_id": document_id,
                    "display_title": display_title,
                    "kind": kind,
                    "kind_label": kind_label,
                    "authors": authors,
                    "year": year,
                    "source": source,
                    "group_id": group_id,
                    "group_color": group_color,
                    "favorite": favorite,
                    "progress": progress,
                    "excerpt": excerpt,
                    "annotation_count": annotation_count,
                    "metadata_summary": metadata_summary
                })
                controller: root.controller
                theme: root.theme
            }
        }
    }
}
