import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "../components"
import "../support/UiDefaults.js" as UiDefaults

ScrollView {
    id: root
    property var controller: null
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property var selectedSources: []

    readonly property var searchSources: controller ? controller.searchSourceModel : null
    readonly property var results: controller ? controller.searchResultModel : null
    readonly property var recentSearches: controller ? controller.recentSearchModel : null
    readonly property var searchTask: controller ? controller.searchTaskState : ({ phase: "idle", summary: "输入关键词后检索。", loading: false })
    readonly property var searchState: controller ? controller.searchWorkspaceState : ({ query: "", result_count: 0, pdf_count: 0, source_count: 0, latest_year: "" })

    contentWidth: availableWidth

    Component.onCompleted: {
        if (root.selectedSources.length === 0) {
            if (root.searchState.selected_sources && root.searchState.selected_sources.length > 0) {
                root.selectedSources = root.searchState.selected_sources.slice()
            } else {
                root.selectedSources = ["arxiv", "crossref", "openalex", "dblp"]
            }
        }
        if (searchField.text.length === 0 && root.searchState.query)
            searchField.text = root.searchState.query
    }

    ColumnLayout {
        width: root.availableWidth
        spacing: 18

        Rectangle {
            Layout.fillWidth: true
            radius: 6
            color: root.theme.panelRaised
            border.color: root.theme.border
            border.width: 1
            implicitHeight: searchHeaderColumn.implicitHeight + 36

            ColumnLayout {
                id: searchHeaderColumn
                anchors.fill: parent
                anchors.margins: 18
                spacing: 14

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 18

                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 10

                        Column {
                            spacing: 6

                            Rectangle {
                                width: 34
                                height: 3
                                color: root.theme.anchor
                            }

                            Text {
                                text: "论文搜索中心"
                                color: root.theme.text
                                font.pixelSize: 22
                                font.weight: Font.DemiBold
                            }

                            Text {
                                text: "把主搜索框、来源切换、任务状态和结果工作区收束成一条清晰的检索路径。"
                                color: root.theme.textMuted
                                font.pixelSize: 12
                                wrapMode: Text.Wrap
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            height: 54
                            radius: 6
                            color: root.theme.panelInset
                            border.color: searchField.activeFocus ? root.theme.accentOutline : root.theme.border
                            border.width: 1

                            RowLayout {
                                anchors.fill: parent
                                anchors.margins: 8
                                spacing: 8

                                InteractiveTextField {
                                    id: searchField
                                    Layout.fillWidth: true
                                    theme: root.theme
                                    placeholderText: "按关键词、标题、作者或主题检索论文"
                                    onAccepted: if (root.controller) root.controller.runSearch(text, root.selectedSources)
                                }

                                InteractiveButton {
                                    theme: root.theme
                                    text: "搜索"
                                    tone: "accent"
                                    enabled: searchField.text.length > 0
                                    onClicked: if (root.controller) root.controller.runSearch(searchField.text, root.selectedSources)
                                }
                            }
                        }

                        TaskBanner {
                            Layout.fillWidth: true
                            theme: root.theme
                            task: root.searchTask
                            compact: true
                        }
                    }

                    Rectangle {
                        Layout.preferredWidth: 320
                        Layout.maximumWidth: 320
                        radius: 6
                        color: root.theme.panelInset
                        border.color: root.theme.border
                        border.width: 1
                        implicitHeight: searchMetricColumn.implicitHeight + 28

                        ColumnLayout {
                            id: searchMetricColumn
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 10

                            Text {
                                text: "当前检索脉络"
                                color: root.theme.anchor
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                            }

                            GridLayout {
                                Layout.fillWidth: true
                                columns: 2
                                columnSpacing: 10
                                rowSpacing: 10

                                MetricTile { Layout.fillWidth: true; theme: root.theme; label: "结果总数"; value: String(root.searchState.result_count || 0); detail: "中央结果区"; tone: "accent" }
                                MetricTile { Layout.fillWidth: true; theme: root.theme; label: "PDF 条目"; value: String(root.searchState.pdf_count || 0); detail: "可直接入库"; tone: "neutral" }
                                MetricTile { Layout.fillWidth: true; theme: root.theme; label: "命中来源"; value: String(root.searchState.source_count || 0); detail: root.searchState.top_source || "等待来源命中"; tone: "neutral" }
                                MetricTile { Layout.fillWidth: true; theme: root.theme; label: "最新年份"; value: root.searchState.latest_year || "—"; detail: root.searchState.query || "尚未检索"; tone: "neutral" }
                            }
                        }
                    }
                }

                Column {
                    Layout.fillWidth: true
                    spacing: 8

                    Text {
                        text: "检索来源"
                        color: root.theme.textMuted
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }

                    Flow {
                        width: parent.width
                        spacing: 8

                        Repeater {
                            model: root.searchSources
                            delegate: InteractiveChip {
                                property bool checkedSource: root.selectedSources.indexOf(source_id) >= 0
                                theme: root.theme
                                text: label + "  " + result_count
                                checked: checkedSource
                                onClicked: {
                                    var next = root.selectedSources.slice()
                                    var idx = next.indexOf(source_id)
                                    if (idx >= 0)
                                        next.splice(idx, 1)
                                    else
                                        next.push(source_id)
                                    root.selectedSources = next
                                }
                            }
                        }
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: 18

            Rectangle {
                Layout.preferredWidth: 300
                Layout.maximumWidth: 300
                radius: 6
                color: root.theme.panelRaised
                border.color: root.theme.border
                border.width: 1
                implicitHeight: searchRailColumn.implicitHeight + 28

                Column {
                    id: searchRailColumn
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 12

                    Text {
                        text: "搜索侧轨"
                        color: root.theme.text
                        font.pixelSize: 15
                        font.weight: Font.DemiBold
                    }

                    Repeater {
                        model: root.searchSources
                        delegate: Rectangle {
                            width: parent.width
                            height: 42
                            radius: 4
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1

                            Text {
                                anchors.left: parent.left
                                anchors.leftMargin: 12
                                anchors.verticalCenter: parent.verticalCenter
                                text: label + "  " + result_count
                                color: root.theme.text
                            }

                            Text {
                                anchors.right: parent.right
                                anchors.rightMargin: 12
                                anchors.verticalCenter: parent.verticalCenter
                                text: summary
                                color: root.theme.textSoft
                                font.pixelSize: 11
                            }
                        }
                    }

                    Text {
                        text: "最近搜索"
                        color: root.theme.textMuted
                        font.pixelSize: 12
                        font.weight: Font.DemiBold
                    }

                    Repeater {
                        model: root.recentSearches
                        delegate: Rectangle {
                            width: parent.width
                            height: 34
                            radius: 4
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1

                            Text {
                                anchors.fill: parent
                                anchors.margins: 10
                                text: label
                                color: root.theme.textMuted
                                verticalAlignment: Text.AlignVCenter
                                elide: Text.ElideRight
                            }

                            SignalAccent {
                                anchors.fill: parent
                                active: false
                                hovered: recentSearchHover.containsMouse
                                pressed: recentSearchHover.pressed
                                accentColor: root.theme.anchor
                                neutralColor: root.theme.accentSoft
                                edge: "frame"
                                radius: 4
                            }

                            MouseArea {
                                id: recentSearchHover
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: {
                                    searchField.text = label
                                    if (root.controller)
                                        root.controller.runRecentSearch(label)
                                }
                            }
                        }
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 6
                color: root.theme.panelRaised
                border.color: root.theme.border
                border.width: 1
                implicitHeight: resultsColumn.implicitHeight + 28

                Column {
                    id: resultsColumn
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 12

                    Row {
                        width: parent.width
                        spacing: 8

                        Text {
                            text: root.searchState.query ? ("结果工作区  ·  " + root.searchState.query) : "结果工作区"
                            color: root.theme.text
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                        }

                        InfoPill {
                            text: (root.searchState.result_count || 0) + " 条"
                            fillColor: root.theme.accentSurface
                            borderColor: root.theme.accentOutline
                            textColor: root.theme.anchor
                        }
                    }

                    Text {
                        visible: !!root.searchTask.detail && (root.searchTask.phase === "error" || root.searchTask.phase === "empty")
                        text: root.searchTask.detail || ""
                        color: root.theme.textSoft
                        font.pixelSize: 11
                        wrapMode: Text.Wrap
                        width: parent.width
                    }

                    Rectangle {
                        visible: !root.results || root.results.count === 0
                        width: parent.width
                        radius: 6
                        color: root.theme.panelInset
                        border.color: root.theme.border
                        border.width: 1
                        implicitHeight: 120

                        Column {
                            anchors.centerIn: parent
                            spacing: 8

                            Text { text: root.searchTask.summary || "暂无检索结果"; color: root.theme.text; font.pixelSize: 14; font.weight: Font.DemiBold; horizontalAlignment: Text.AlignHCenter }
                            Text { text: root.searchTask.detail || "主搜索区发起检索后，结果会集中出现在这里。"; color: root.theme.textSoft; font.pixelSize: 11; horizontalAlignment: Text.AlignHCenter }
                        }
                    }

                    Repeater {
                        model: root.results
                        delegate: SearchResultCard {
                            width: parent.width
                            itemData: ({
                                "result_id": result_id,
                                "title": title,
                                "authors": authors,
                                "year": year,
                                "item_type": item_type,
                                "abstract_text": abstract_text,
                                "source_label": source_label,
                                "landing_url": landing_url,
                                "pdf_url": pdf_url,
                                "venue": venue,
                                "doi": doi,
                                "has_pdf": has_pdf,
                                "meta_summary": meta_summary,
                                "status_line": status_line
                            })
                            controller: root.controller
                            theme: root.theme
                        }
                    }
                }
            }
        }
    }
}
