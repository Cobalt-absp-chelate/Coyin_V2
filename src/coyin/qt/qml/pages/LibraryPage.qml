pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../support/UiDefaults.js" as UiDefaults

Item {
    id: root
    property var controller: null
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())

    readonly property var filterState: controller ? controller.libraryFilterState : UiDefaults.libraryFilterState()
    readonly property var groups: controller ? controller.groupModel : null
    readonly property var kindOptions: controller ? controller.libraryKindModel : null
    readonly property var documents: controller ? controller.libraryModel : null
    readonly property int documentCount: documents ? documents.count : 0

    ColumnLayout {
        anchors.fill: parent
        spacing: 18

        SectionCard {
            Layout.fillWidth: true
            title: "资料筛选"
            caption: "按标题、分组和类型筛选资料。"
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

                InteractiveButton {
                    theme: root.theme
                    text: root.filterState.recent_only ? "仅看最近打开" : "全部记录"
                    selected: root.filterState.recent_only
                    onClicked: if (root.controller) root.controller.setLibraryRecentOnly(!root.filterState.recent_only)
                }

                InteractiveButton {
                    theme: root.theme
                    text: "清空筛选"
                    onClicked: if (root.controller) root.controller.clearLibraryFilters()
                }

                InteractiveButton {
                    theme: root.theme
                    text: "批量导入"
                    onClicked: if (root.controller) root.controller.importDocuments()
                }

                InteractiveButton {
                    theme: root.theme
                    text: "新建文档"
                    tone: "accent"
                    onClicked: if (root.controller) root.controller.createWriterDocument()
                }
            }

            Text {
                text: "当前显示 " + root.filterState.visible_count + " / " + root.filterState.total_count + " 份资料。"
                color: root.theme.textSoft
            }

            Text {
                text: "分组"
                color: root.theme.textMuted
                font.weight: Font.DemiBold
            }

            Flow {
                id: groupFlow
                width: parent.width
                spacing: 8

                InteractiveChip {
                    theme: root.theme
                    text: "全部分组"
                    width: Math.min(implicitWidth, groupFlow.width)
                    checked: root.filterState.group_id === "all"
                    onClicked: if (root.controller) root.controller.setLibraryGroupFilter("all")
                }

                Repeater {
                    model: root.groups

                    delegate: InteractiveChip {
                        required property string group_id
                        required property string name
                        required property var group_color
                        required property int document_count
                        theme: root.theme
                        width: Math.min(implicitWidth, groupFlow.width)
                        text: (name || "") + " (" + document_count + ")"
                        checked: root.filterState.group_id === group_id
                        markColor: group_color || "transparent"
                        onClicked: if (root.controller) root.controller.setLibraryGroupFilter(group_id)
                    }
                }
            }

            Text {
                text: "类型"
                color: root.theme.textMuted
                font.weight: Font.DemiBold
            }

            Flow {
                id: kindFlow
                width: parent.width
                spacing: 8

                Repeater {
                    model: root.kindOptions

                    delegate: InteractiveChip {
                        required property string kind_id
                        required property string label
                        required property int count
                        theme: root.theme
                        width: Math.min(implicitWidth, kindFlow.width)
                        text: (label || "") + " (" + count + ")"
                        checked: root.filterState.kind === kind_id
                        onClicked: if (root.controller) root.controller.setLibraryKindFilter(kind_id)
                    }
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            SectionCard {
                anchors.fill: parent
                visible: root.documentCount === 0
                title: "资料视图"
                panelColor: root.theme.panelRaised
                borderColor: root.theme.border
                textColor: root.theme.text
                captionColor: root.theme.textSoft
                accentColor: root.theme.anchor
                accentSoft: root.theme.accentSoft

                Text {
                    width: parent.width
                    text: "没有匹配结果"
                    color: root.theme.textMuted
                    wrapMode: Text.Wrap
                }
            }

            ListView {
                id: documentList
                anchors.fill: parent
                visible: root.documentCount > 0
                clip: true
                spacing: 12
                reuseItems: true
                cacheBuffer: 1200
                model: root.documents
                boundsBehavior: Flickable.StopAtBounds
                ScrollBar.vertical: AutoHideScrollBar { theme: root.theme }

                delegate: Item {
                    required property string document_id
                    required property string display_title
                    required property string kind
                    required property string kind_label
                    required property string authors
                    required property string year
                    required property string source
                    required property string group_id
                    required property var group_color
                    required property bool favorite
                    required property int progress
                    required property string excerpt
                    required property int annotation_count
                    required property string metadata_summary

                    width: ListView.view.width
                    height: card.implicitHeight

                    DocumentLibraryCard {
                        id: card
                        width: parent.width
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

                footer: Item {
                    width: 1
                    height: 8
                }
            }
        }
    }
}
