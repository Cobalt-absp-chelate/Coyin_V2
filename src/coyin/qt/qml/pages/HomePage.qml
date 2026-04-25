pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "../components"
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

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
    readonly property int recentDocumentCount: Math.min(root.recentDocuments ? root.recentDocuments.count : 0, 4)
    readonly property int recentAnalysisCount: Math.min(root.analysisHistory ? root.analysisHistory.count : 0, 4)
    readonly property int groupCount: Math.min(root.groups ? root.groups.count : 0, 3)
    readonly property int recentSearchCount: Math.min(root.recentSearches ? root.recentSearches.count : 0, 3)
    readonly property int recentWriterCount: Math.min(root.recentWriters ? root.recentWriters.count : 0, 3)
    readonly property int recentLatexCount: Math.min(root.recentLatexSessions ? root.recentLatexSessions.count : 0, 2)
    readonly property int recentNoteCount: Math.min(root.recentNotes ? root.recentNotes.count : 0, 3)

    contentWidth: availableWidth
    ScrollBar.vertical: AutoHideScrollBar { theme: root.theme }
    ScrollBar.horizontal: AutoHideScrollBar { theme: root.theme }

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

                        }

                        GridLayout {
                            id: actionGrid
                            width: parent.width
                            columns: root.actionColumns
                            columnSpacing: 12
                            rowSpacing: 12

                            Repeater {
                                model: root.workbenchPaths
                                delegate: Item {
                                    id: actionDelegate
                                    required property string title
                                    required property string caption
                                    required property string badge
                                    required property string page_id
                                    required property string action_id
                                    required property string action_label
                                    required property string mark
                                    required property string tone
                                    readonly property string entryTitle: title || ""
                                    readonly property string entryCaption: caption || ""
                                    readonly property string entryBadge: badge || ""
                                    readonly property string entryPageId: page_id || ""
                                    readonly property string entryActionId: action_id || ""
                                    readonly property string entryActionLabel: action_label || ""
                                    readonly property string entryMark: mark || ""
                                    readonly property string entryTone: tone || "neutral"

                                    Layout.fillWidth: true
                                    Layout.preferredWidth: Math.max(0, (actionGrid.width - (actionGrid.columns - 1) * actionGrid.columnSpacing) / actionGrid.columns)
                                    implicitWidth: card.implicitWidth
                                    implicitHeight: card.implicitHeight

                                    WorkbenchActionCard {
                                        id: card
                                        anchors.fill: parent
                                        theme: root.theme
                                        heading: actionDelegate.entryTitle
                                        detail: actionDelegate.entryCaption
                                        badge: actionDelegate.entryBadge
                                        actionLabel: actionDelegate.entryActionLabel
                                        mark: actionDelegate.entryMark
                                        tone: actionDelegate.entryTone
                                        onTriggered: {
                                            if (actionDelegate.entryPageId.length > 0 && actionDelegate.entryPageId !== "home" && root.shellState)
                                                root.shellState.setCurrentPage(actionDelegate.entryPageId)
                                            if (root.controller && (actionDelegate.entryActionId === "importDocuments" || actionDelegate.entryActionId === "createWriterDocument" || actionDelegate.entryActionId === "openLatexWindow"))
                                                root.controller.triggerWorkbenchAction(actionDelegate.entryActionId)
                                        }
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
                                delegate: Item {
                                    id: metricDelegate
                                    required property string label
                                    required property var value
                                    required property string detail
                                    required property string tone
                                    readonly property string metricLabel: label || ""
                                    readonly property string metricValue: value === undefined || value === null ? "0" : String(value)
                                    readonly property string metricDetail: detail || ""
                                    readonly property string metricTone: tone || "neutral"

                                    Layout.fillWidth: true
                                    Layout.preferredWidth: Math.max(0, (overviewGrid.width - (overviewGrid.columns - 1) * overviewGrid.columnSpacing) / overviewGrid.columns)
                                    implicitWidth: tile.implicitWidth
                                    implicitHeight: tile.implicitHeight

                                    MetricTile {
                                        id: tile
                                        anchors.fill: parent
                                        theme: root.theme
                                        label: metricDelegate.metricLabel
                                        value: metricDelegate.metricValue
                                        detail: metricDelegate.metricDetail
                                        tone: metricDelegate.metricTone
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

                                ListView {
                                    width: parent.width
                                    height: contentHeight
                                    implicitHeight: contentHeight
                                    interactive: false
                                    clip: true
                                    spacing: 10
                                    reuseItems: true
                                    model: root.recentDocumentCount

                                    delegate: Rectangle {
                                        required property int index
                                        readonly property var entry: root.recentDocuments ? root.recentDocuments.record(index) : ({})
                                        width: ListView.view.width
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

                                                Text { text: entry.display_title || ""; color: root.theme.text; width: parent.width; elide: Text.ElideRight; font.weight: Font.DemiBold }
                                                Text { text: entry.metadata_summary || entry.status_line || ""; color: root.theme.textMuted; width: parent.width; elide: Text.ElideRight; font.pixelSize: 11 }
                                                Text { text: entry.excerpt || "打开继续阅读"; color: root.theme.textSoft; width: parent.width; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; font.pixelSize: 11 }
                                            }

                                            InteractiveButton {
                                                Layout.alignment: Qt.AlignVCenter
                                                theme: root.theme
                                                text: "打开"
                                                onClicked: if (root.controller && entry.document_id) root.controller.openDocument(entry.document_id)
                                            }
                                        }
                                    }
                                }

                                Text {
                                    visible: root.recentDocumentCount === 0
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

                                ListView {
                                    width: parent.width
                                    height: contentHeight
                                    implicitHeight: contentHeight
                                    interactive: false
                                    clip: true
                                    spacing: 10
                                    reuseItems: true
                                    model: root.recentAnalysisCount

                                    delegate: Rectangle {
                                        required property int index
                                        readonly property var entry: root.analysisHistory ? root.analysisHistory.record(index) : ({})
                                        width: ListView.view.width
                                        radius: root.theme.radiusSmall
                                        color: MotionCore.mixColor(root.theme.panelInset, root.theme.accentSurface, analysisInteraction.frameStrength * 0.16)
                                        border.color: MotionCore.mixColor(root.theme.border, root.theme.accentOutline, analysisInteraction.frameStrength * 0.68 + analysisInteraction.settleStrength * 0.18)
                                        border.width: 1
                                        implicitHeight: analysisCardColumn.implicitHeight + 20

                                        Behavior on color {
                                            ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                                        }

                                        Behavior on border.color {
                                            ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                                        }

                                        InteractionTracker {
                                            id: analysisInteraction
                                            targetItem: parent
                                            tapEnabled: true
                                            onTapped: {
                                                if (root.shellState) root.shellState.setCurrentPage("analysis")
                                                if (root.controller && entry.report_id) root.controller.focusAnalysis(entry.report_id)
                                            }
                                        }

                                        Column {
                                            id: analysisCardColumn
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            spacing: 5

                                            Text {
                                                text: entry.title || ""
                                                color: MotionCore.mixColor(root.theme.text, root.theme.anchor, analysisInteraction.textStrength * 0.24)
                                                width: parent.width
                                                elide: Text.ElideRight
                                                font.weight: Font.DemiBold

                                                Behavior on color {
                                                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                                                }
                                            }
                                            Text { text: entry.status_line || ""; color: root.theme.textSoft; width: parent.width; elide: Text.ElideRight; font.pixelSize: 11 }
                                            Text { text: entry.summary || ""; color: root.theme.textMuted; width: parent.width; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; font.pixelSize: 11 }
                                        }

                                        SignalAccent {
                                            anchors.fill: parent
                                            active: analysisInteraction.settleStrength > 0.12
                                            hovered: analysisInteraction.hovered
                                            pressed: analysisInteraction.pressed
                                            accentColor: root.theme.anchor
                                            neutralColor: root.theme.accentSoft
                                            edge: "frame"
                                            radius: 4
                                        }

                                    }
                                }

                                Text {
                                    visible: root.recentAnalysisCount === 0
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

                        ListView {
                            width: parent.width
                            height: contentHeight
                            implicitHeight: contentHeight
                            interactive: false
                            clip: true
                            spacing: 8
                            reuseItems: true
                            model: root.groupCount

                            delegate: Rectangle {
                                required property int index
                                readonly property var entry: root.groups ? root.groups.record(index) : ({})
                                width: ListView.view.width
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
                                    color: entry.group_color || "transparent"
                                }

                                Text {
                                    anchors.left: parent.left
                                    anchors.leftMargin: 14
                                    anchors.verticalCenter: parent.verticalCenter
                                    width: Math.max(0, parent.width - 26)
                                    text: (entry.name || "") + "  " + (entry.document_count || "")
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

                        ListView {
                            width: parent.width
                            height: contentHeight
                            implicitHeight: contentHeight
                            interactive: false
                            clip: true
                            spacing: 8
                            reuseItems: true
                            model: root.recentSearchCount

                            delegate: Rectangle {
                                required property int index
                                readonly property var entry: root.recentSearches ? root.recentSearches.record(index) : ({})
                                width: ListView.view.width
                                height: 36
                                radius: root.theme.radiusSmall
                                color: MotionCore.mixColor(root.theme.panelInset, root.theme.accentSurface, recentSearchInteraction.frameStrength * 0.16)
                                border.color: MotionCore.mixColor(root.theme.border, root.theme.accentOutline, recentSearchInteraction.frameStrength * 0.68 + recentSearchInteraction.settleStrength * 0.18)
                                border.width: 1

                                Behavior on color {
                                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                                }

                                Behavior on border.color {
                                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                                }

                                InteractionTracker {
                                    id: recentSearchInteraction
                                    targetItem: parent
                                    tapEnabled: true
                                    onTapped: {
                                        if (root.shellState) root.shellState.setCurrentPage("search")
                                        if (root.controller && entry.label) root.controller.runRecentSearch(entry.label)
                                    }
                                }

                                Text {
                                    anchors.fill: parent
                                    anchors.margins: 12
                                    text: entry.label || ""
                                    color: MotionCore.mixColor(root.theme.textMuted, root.theme.text, recentSearchInteraction.textStrength * 0.90 + recentSearchInteraction.settleStrength * 0.10)
                                    verticalAlignment: Text.AlignVCenter
                                    elide: Text.ElideRight

                                    Behavior on color {
                                        ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                                    }
                                }

                                SignalAccent {
                                    anchors.fill: parent
                                    active: recentSearchInteraction.settleStrength > 0.12
                                    hovered: recentSearchInteraction.hovered
                                    pressed: recentSearchInteraction.pressed
                                    accentColor: root.theme.anchor
                                    neutralColor: root.theme.accentSoft
                                    edge: "frame"
                                    radius: 4
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

                    Text { text: "写作"; color: root.theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }

                    ListView {
                        width: parent.width
                        height: contentHeight
                        implicitHeight: contentHeight
                        interactive: false
                        clip: true
                        spacing: 8
                        reuseItems: true
                        model: root.recentWriterCount

                        delegate: Rectangle {
                            required property int index
                            readonly property var entry: root.recentWriters ? root.recentWriters.record(index) : ({})
                            width: ListView.view.width
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
                                    Text { text: entry.display_title || ""; color: root.theme.text; width: parent.width; elide: Text.ElideRight; font.weight: Font.DemiBold }
                                    Text { text: entry.status_line || ""; color: root.theme.textSoft; width: parent.width; elide: Text.ElideRight; font.pixelSize: 11 }
                                }

                                InteractiveButton {
                                    Layout.alignment: Qt.AlignVCenter
                                    theme: root.theme
                                    text: "继续"
                                    onClicked: if (root.controller && entry.document_id) root.controller.openWriterDocument(entry.document_id)
                                }
                            }
                        }
                    }

                    ListView {
                        width: parent.width
                        height: contentHeight
                        implicitHeight: contentHeight
                        interactive: false
                        clip: true
                        spacing: 8
                        reuseItems: true
                        model: root.recentLatexCount

                        delegate: Rectangle {
                            required property int index
                            readonly property var entry: root.recentLatexSessions ? root.recentLatexSessions.record(index) : ({})
                            width: ListView.view.width
                            radius: root.theme.radiusSmall
                            color: MotionCore.mixColor(root.theme.panelInset, root.theme.accentSurface, latexInteraction.frameStrength * 0.16)
                            border.color: MotionCore.mixColor(root.theme.border, root.theme.accentOutline, latexInteraction.frameStrength * 0.68 + latexInteraction.settleStrength * 0.18)
                            border.width: 1
                            implicitHeight: latexText.implicitHeight + 22

                            Behavior on color {
                                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                            }

                            Behavior on border.color {
                                ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                            }

                            InteractionTracker {
                                id: latexInteraction
                                targetItem: parent
                                tapEnabled: true
                                onTapped: if (root.controller && entry.session_id) root.controller.openLatexSession(entry.session_id)
                            }

                            Text {
                                id: latexText
                                anchors.fill: parent
                                anchors.margins: 12
                                text: (entry.title || "") + "  ·  " + (entry.status_line || "")
                                color: MotionCore.mixColor(root.theme.textMuted, root.theme.text, latexInteraction.textStrength * 0.90 + latexInteraction.settleStrength * 0.10)
                                verticalAlignment: Text.AlignVCenter
                                wrapMode: Text.Wrap
                                maximumLineCount: 2
                                elide: Text.ElideRight

                                Behavior on color {
                                    ColorAnimation { duration: MotionCore.duration("fast", root.theme) }
                                }
                            }

                            SignalAccent {
                                anchors.fill: parent
                                active: latexInteraction.settleStrength > 0.12
                                hovered: latexInteraction.hovered
                                pressed: latexInteraction.pressed
                                accentColor: root.theme.anchor
                                neutralColor: root.theme.accentSoft
                                edge: "frame"
                                radius: 4
                            }

                        }
                    }

                    Text {
                        visible: root.recentWriterCount === 0 && root.recentLatexCount === 0
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

                    Text { text: "笔记"; color: root.theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }

                    ListView {
                        width: parent.width
                        height: contentHeight
                        implicitHeight: contentHeight
                        interactive: false
                        clip: true
                        spacing: 8
                        reuseItems: true
                        model: root.recentNoteCount

                        delegate: Rectangle {
                            required property int index
                            readonly property var entry: root.recentNotes ? root.recentNotes.record(index) : ({})
                            width: ListView.view.width
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

                                Text { text: entry.title || ""; color: root.theme.text; width: parent.width; elide: Text.ElideRight; font.weight: Font.DemiBold; font.pixelSize: 12 }
                                Text { text: entry.content || ""; color: root.theme.textMuted; width: parent.width; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; font.pixelSize: 11 }
                            }
                        }
                    }

                    Text {
                        visible: root.recentNoteCount === 0
                        text: "暂无研究笔记"
                        color: root.theme.textSoft
                    }
                }
            }
        }
    }
}
