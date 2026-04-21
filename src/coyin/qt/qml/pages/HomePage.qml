import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "../components"
import "../support/UiDefaults.js" as UiDefaults

ScrollView {
    id: root
    property var controller: null
    property var shellState: null
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())

    readonly property var workbenchPaths: controller ? controller.homePathModel : null
    readonly property var overviewMetrics: controller ? controller.overviewMetricModel : null
    readonly property var recentDocuments: controller ? controller.recentDocumentModel : null
    readonly property var recentWriters: controller ? controller.recentWriterModel : null
    readonly property var analysisHistory: controller ? controller.analysisHistoryModel : null
    readonly property var recentSearches: controller ? controller.recentSearchModel : null
    readonly property var recentNotes: controller ? controller.recentNoteModel : null
    readonly property var recentLatexSessions: controller ? controller.recentLatexModel : null
    readonly property var groups: controller ? controller.groupModel : null
    readonly property bool compactHero: root.availableWidth < 1360
    readonly property bool stackedMain: root.availableWidth < 1380
    readonly property bool stackedSecondary: root.availableWidth < 1260
    readonly property bool compactContext: root.availableWidth < 1180
    readonly property int actionColumns: root.availableWidth > 1580 ? 3 : 2

    contentWidth: availableWidth

    ColumnLayout {
        width: root.availableWidth
        spacing: 18

        Rectangle {
            Layout.fillWidth: true
            radius: 6
            color: root.theme.panelRaised
            border.color: root.theme.border
            border.width: 1
            implicitHeight: heroGrid.implicitHeight + 36

            GridLayout {
                id: heroGrid
                anchors.fill: parent
                anchors.margins: 18
                columns: root.compactHero ? 1 : 2
                columnSpacing: 18
                rowSpacing: 18

                Item {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop
                    implicitHeight: heroLeftColumn.implicitHeight

                    Column {
                        id: heroLeftColumn
                        width: parent.width
                        spacing: 14

                        Column {
                            width: parent.width
                            spacing: 6

                            Rectangle {
                                width: 34
                                height: 3
                                color: root.theme.anchor
                            }

                            Text {
                                text: "研究工作台"
                                color: root.theme.text
                                font.pixelSize: 22
                                font.weight: Font.DemiBold
                            }

                            Text {
                                width: parent.width
                                text: "把资料入库、论文检索、结构化分析、写作草稿和 LaTeX 排版组织成一条清晰的桌面工作路径。"
                                color: root.theme.textMuted
                                font.pixelSize: 12
                                wrapMode: Text.Wrap
                            }
                        }

                        GridLayout {
                            id: actionGrid
                            width: parent.width
                            columns: root.actionColumns
                            columnSpacing: 12
                            rowSpacing: 12

                            Repeater {
                                model: root.workbenchPaths
                                delegate: WorkbenchActionCard {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: (actionGrid.width - (actionGrid.columns - 1) * actionGrid.columnSpacing) / actionGrid.columns
                                    theme: root.theme
                                    heading: title
                                    detail: caption
                                    badge: badge
                                    actionLabel: detail
                                    mark: mark
                                    tone: tone
                                    onTriggered: {
                                        if (page_id && page_id !== "home" && root.shellState)
                                            root.shellState.setCurrentPage(page_id)
                                        if (root.controller && (action_id === "importDocuments" || action_id === "createWriterDocument" || action_id === "openLatexWindow"))
                                            root.controller.triggerWorkbenchAction(action_id)
                                    }
                                }
                            }
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: root.compactHero
                    Layout.preferredWidth: root.compactHero ? 0 : 360
                    Layout.maximumWidth: root.compactHero ? 16777215 : 360
                    Layout.alignment: Qt.AlignTop
                    radius: 6
                    color: root.theme.panelInset
                    border.color: root.theme.border
                    border.width: 1
                    implicitHeight: overviewColumn.implicitHeight + 28

                    Column {
                        id: overviewColumn
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 12

                        Text {
                            text: "工作概览"
                            color: root.theme.anchor
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }

                        GridLayout {
                            id: overviewGrid
                            width: parent.width
                            columns: root.compactHero ? 3 : 2
                            columnSpacing: 10
                            rowSpacing: 10

                            Repeater {
                                model: root.overviewMetrics
                                delegate: MetricTile {
                                    Layout.fillWidth: true
                                    Layout.preferredWidth: (overviewGrid.width - (overviewGrid.columns - 1) * overviewGrid.columnSpacing) / overviewGrid.columns
                                    theme: root.theme
                                    label: model.label
                                    value: String(model.value)
                                    detail: model.detail
                                    tone: model.tone
                                }
                            }
                        }
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.stackedMain ? 1 : 2
            columnSpacing: 18
            rowSpacing: 18

            Rectangle {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                radius: 6
                color: root.theme.panelRaised
                border.color: root.theme.border
                border.width: 1
                implicitHeight: contextColumn.implicitHeight + 32

                Column {
                    id: contextColumn
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    RowLayout {
                        width: parent.width
                        spacing: 12

                        Column {
                            Layout.fillWidth: true
                            spacing: 4

                            Text {
                                text: "最近上下文"
                                color: root.theme.text
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                            }

                            Text {
                                width: Math.min(parent.width, 520)
                                text: "把最近阅读和最近分析集中成首页主工作区，用更稳定的比例承接当前工作。"
                                color: root.theme.textSoft
                                font.pixelSize: 11
                                wrapMode: Text.Wrap
                            }
                        }

                        InfoPill {
                            text: "主工作区"
                            fillColor: root.theme.accentSurface
                            borderColor: root.theme.accentOutline
                            textColor: root.theme.anchor
                        }
                    }

                    GridLayout {
                        id: contextGrid
                        width: parent.width
                        columns: root.compactContext ? 1 : 2
                        columnSpacing: 14
                        rowSpacing: 14

                        Rectangle {
                            Layout.fillWidth: true
                            radius: 6
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: recentReadColumn.implicitHeight + 24

                            Column {
                                id: recentReadColumn
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 10

                                Text {
                                    text: "最近阅读"
                                    color: root.theme.anchor
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                }

                                Repeater {
                                    model: root.recentDocuments
                                    delegate: Rectangle {
                                        visible: index < 4
                                        width: parent.width
                                        radius: 4
                                        color: root.theme.panelRaised
                                        border.color: root.theme.border
                                        border.width: 1
                                        implicitHeight: docRow.implicitHeight + 20

                                        RowLayout {
                                            id: docRow
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            spacing: 10

                                            Column {
                                                Layout.fillWidth: true
                                                spacing: 4

                                                Text { text: display_title; color: root.theme.text; width: parent.width; elide: Text.ElideRight; font.weight: Font.DemiBold }
                                                Text { text: metadata_summary || status_line; color: root.theme.textMuted; width: parent.width; elide: Text.ElideRight; font.pixelSize: 11 }
                                                Text { text: excerpt || "继续进入阅读与标注"; color: root.theme.textSoft; width: parent.width; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; font.pixelSize: 11 }
                                            }

                                            InteractiveButton {
                                                Layout.alignment: Qt.AlignVCenter
                                                theme: root.theme
                                                text: "打开"
                                                onClicked: if (root.controller) root.controller.openDocument(document_id)
                                            }
                                        }
                                    }
                                }

                                Text {
                                    visible: !root.recentDocuments || root.recentDocuments.count === 0
                                    text: "暂无最近文档"
                                    color: root.theme.textSoft
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            radius: 6
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: recentAnalysisColumn.implicitHeight + 24

                            Column {
                                id: recentAnalysisColumn
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 10

                                Text {
                                    text: "最近分析"
                                    color: root.theme.anchor
                                    font.pixelSize: 13
                                    font.weight: Font.DemiBold
                                }

                                Repeater {
                                    model: root.analysisHistory
                                    delegate: Rectangle {
                                        visible: index < 4
                                        width: parent.width
                                        radius: 4
                                        color: root.theme.panelRaised
                                        border.color: root.theme.border
                                        border.width: 1
                                        implicitHeight: analysisCardColumn.implicitHeight + 20

                                        Column {
                                            id: analysisCardColumn
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            spacing: 5

                                            Text { text: title; color: root.theme.text; width: parent.width; elide: Text.ElideRight; font.weight: Font.DemiBold }
                                            Text { text: status_line; color: root.theme.textSoft; width: parent.width; elide: Text.ElideRight; font.pixelSize: 11 }
                                            Text { text: summary; color: root.theme.textMuted; width: parent.width; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; font.pixelSize: 11 }
                                        }

                                        SignalAccent {
                                            anchors.fill: parent
                                            active: false
                                            hovered: analysisHover.containsMouse
                                            pressed: analysisHover.pressed
                                            accentColor: root.theme.anchor
                                            neutralColor: root.theme.accentSoft
                                            edge: "frame"
                                            radius: 4
                                        }

                                        MouseArea {
                                            id: analysisHover
                                            anchors.fill: parent
                                            hoverEnabled: true
                                            cursorShape: Qt.PointingHandCursor
                                            onClicked: {
                                                if (root.shellState) root.shellState.setCurrentPage("analysis")
                                                if (root.controller) root.controller.focusAnalysis(report_id)
                                            }
                                        }
                                    }
                                }

                                Text {
                                    visible: !root.analysisHistory || root.analysisHistory.count === 0
                                    text: "暂无分析记录"
                                    color: root.theme.textSoft
                                }
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: root.stackedMain
                Layout.preferredWidth: root.stackedMain ? 0 : 326
                Layout.maximumWidth: root.stackedMain ? 16777215 : 326
                Layout.alignment: Qt.AlignTop
                spacing: 18

                AssistantDock {
                    Layout.fillWidth: true
                    controller: root.controller
                    theme: root.theme
                }

                Rectangle {
                    Layout.fillWidth: true
                    radius: 6
                    color: root.theme.panelRaised
                    border.color: root.theme.border
                    border.width: 1
                    implicitHeight: sideColumn.implicitHeight + 28

                    Column {
                        id: sideColumn
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 10

                        Text { text: "研究辅助"; color: root.theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }

                        Repeater {
                            model: root.groups
                            delegate: Rectangle {
                                visible: index < 3
                                width: parent.width
                                height: 40
                                radius: 4
                                color: root.theme.panelInset
                                border.color: root.theme.border
                                border.width: 1

                                Rectangle {
                                    anchors.left: parent.left
                                    anchors.top: parent.top
                                    anchors.bottom: parent.bottom
                                    width: 4
                                    color: group_color
                                }

                                Text {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 14
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: parent.width - 26
                                    text: name + "  " + document_count
                                    color: root.theme.text
                                    elide: Text.ElideRight
                                }
                            }
                        }

                        Rectangle {
                            width: parent.width
                            height: 1
                            color: root.theme.border
                        }

                        Text { text: "最近搜索"; color: root.theme.text; font.pixelSize: 13; font.weight: Font.DemiBold }

                        Repeater {
                            model: root.recentSearches
                            delegate: Rectangle {
                                visible: index < 3
                                width: parent.width
                                height: 36
                                radius: 4
                                color: root.theme.panelInset
                                border.color: root.theme.border
                                border.width: 1

                                Text {
                                    anchors.fill: parent
                                    anchors.margins: 12
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
                                        if (root.shellState) root.shellState.setCurrentPage("search")
                                        if (root.controller) root.controller.runRecentSearch(label)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.stackedSecondary ? 1 : 2
            columnSpacing: 18
            rowSpacing: 18

            Rectangle {
                Layout.fillWidth: true
                radius: 6
                color: root.theme.panelRaised
                border.color: root.theme.border
                border.width: 1
                implicitHeight: writingColumn.implicitHeight + 28

                Column {
                    id: writingColumn
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 10

                    Text { text: "写作与排版路径"; color: root.theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }
                    Text { text: "把最近写作草稿和最近 LaTeX 会话收进同一条延续路径，减少来回跳转。"; color: root.theme.textSoft; font.pixelSize: 11; width: parent.width; wrapMode: Text.Wrap }

                    Repeater {
                        model: root.recentWriters
                        delegate: Rectangle {
                            visible: index < 3
                            width: parent.width
                            radius: 4
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: writerRow.implicitHeight + 18

                            RowLayout {
                                id: writerRow
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 10

                                Column {
                                    Layout.fillWidth: true
                                    spacing: 4
                                    Text { text: display_title; color: root.theme.text; width: parent.width; elide: Text.ElideRight; font.weight: Font.DemiBold }
                                    Text { text: status_line; color: root.theme.textSoft; width: parent.width; elide: Text.ElideRight; font.pixelSize: 11 }
                                }

                                InteractiveButton {
                                    Layout.alignment: Qt.AlignVCenter
                                    theme: root.theme
                                    text: "继续"
                                    onClicked: if (root.controller) root.controller.openWriterDocument(document_id)
                                }
                            }
                        }
                    }

                    Repeater {
                        model: root.recentLatexSessions
                        delegate: Rectangle {
                            visible: index < 2
                            width: parent.width
                            radius: 4
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: latexText.implicitHeight + 22

                            Text {
                                id: latexText
                                anchors.fill: parent
                                anchors.margins: 12
                                text: title + "  ·  " + status_line
                                color: root.theme.textMuted
                                verticalAlignment: Text.AlignVCenter
                                wrapMode: Text.Wrap
                                maximumLineCount: 2
                                elide: Text.ElideRight
                            }

                            SignalAccent {
                                anchors.fill: parent
                                active: false
                                hovered: latexHover.containsMouse
                                pressed: latexHover.pressed
                                accentColor: root.theme.anchor
                                neutralColor: root.theme.accentSoft
                                edge: "frame"
                                radius: 4
                            }

                            MouseArea {
                                id: latexHover
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onClicked: if (root.controller) root.controller.openLatexSession(session_id)
                            }
                        }
                    }

                    Text {
                        visible: (!root.recentWriters || root.recentWriters.count === 0) && (!root.recentLatexSessions || root.recentLatexSessions.count === 0)
                        text: "暂无写作或排版会话"
                        color: root.theme.textSoft
                    }
                }
            }

            Rectangle {
                Layout.fillWidth: true
                radius: 6
                color: root.theme.panelRaised
                border.color: root.theme.border
                border.width: 1
                implicitHeight: secondaryColumn.implicitHeight + 28

                Column {
                    id: secondaryColumn
                    anchors.fill: parent
                    anchors.margins: 14
                    spacing: 10

                    Text { text: "次工作区"; color: root.theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }
                    Text { text: "把最近笔记和轻量回顾收在侧线，不抢主工作区，但随时可回到上下文。"; color: root.theme.textSoft; font.pixelSize: 11; width: parent.width; wrapMode: Text.Wrap }

                    Repeater {
                        model: root.recentNotes
                        delegate: Rectangle {
                            visible: index < 3
                            width: parent.width
                            radius: 4
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: noteColumn.implicitHeight + 20

                            Column {
                                id: noteColumn
                                anchors.fill: parent
                                anchors.margins: 10
                                spacing: 4

                                Text { text: title; color: root.theme.text; width: parent.width; elide: Text.ElideRight; font.weight: Font.DemiBold; font.pixelSize: 12 }
                                Text { text: content; color: root.theme.textMuted; width: parent.width; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; font.pixelSize: 11 }
                            }
                        }
                    }

                    Text {
                        visible: !root.recentNotes || root.recentNotes.count === 0
                        text: "暂无研究笔记"
                        color: root.theme.textSoft
                    }
                }
            }
        }
    }
}
