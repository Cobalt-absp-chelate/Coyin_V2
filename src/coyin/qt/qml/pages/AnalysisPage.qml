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

    readonly property var documentChoices: controller ? controller.documentChoiceModel : null
    readonly property var analysisHistory: controller ? controller.analysisHistoryModel : null
    readonly property var currentAnalysis: controller ? controller.currentAnalysis : UiDefaults.analysis()
    readonly property var analysisTask: controller ? controller.analysisTaskState : ({ phase: "idle", summary: "选择文档后开始分析。", loading: false })
    readonly property var analysisState: controller ? controller.analysisWorkspaceState : ({ history_count: 0, field_count: 0, experiment_count: 0, comparison_count: 0, has_current: false })
    readonly property bool stackedHeader: root.availableWidth < 1380
    readonly property bool stackedBody: root.availableWidth < 1450
    readonly property bool compactSections: root.availableWidth < 1120

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
            implicitHeight: headerColumn.implicitHeight + 36

            Column {
                id: headerColumn
                anchors.fill: parent
                anchors.margins: 18
                spacing: 14

                GridLayout {
                    width: parent.width
                    columns: root.stackedHeader ? 1 : 2
                    columnSpacing: 18
                    rowSpacing: 18

                    Item {
                        Layout.fillWidth: true
                        implicitHeight: titleColumn.implicitHeight

                        Column {
                            id: titleColumn
                            width: parent.width
                            spacing: 8

                            Rectangle {
                                width: 34
                                height: 3
                                color: root.theme.anchor
                            }

                            Text {
                                text: root.currentAnalysis.title || "分析报告工作区"
                                color: root.theme.text
                                font.pixelSize: 22
                                font.weight: Font.DemiBold
                            }

                            Text {
                                width: parent.width
                                text: root.currentAnalysis.summary || "这里承接分析发起、历史报告、结构化内容、补充字段和导出路径。"
                                color: root.theme.textMuted
                                font.pixelSize: 12
                                wrapMode: Text.Wrap
                            }
                        }
                    }

                    Rectangle {
                        Layout.fillWidth: root.stackedHeader
                        Layout.preferredWidth: root.stackedHeader ? 0 : 344
                        Layout.maximumWidth: root.stackedHeader ? 16777215 : 344
                        radius: 6
                        color: root.theme.panelInset
                        border.color: root.theme.border
                        border.width: 1
                        implicitHeight: metricsColumn.implicitHeight + 28

                        Column {
                            id: metricsColumn
                            anchors.fill: parent
                            anchors.margins: 14
                            spacing: 10

                            Text {
                                text: "当前分析脉络"
                                color: root.theme.anchor
                                font.pixelSize: 14
                                font.weight: Font.DemiBold
                            }

                            GridLayout {
                                id: metricsGrid
                                width: parent.width
                                columns: 2
                                columnSpacing: 10
                                rowSpacing: 10

                                MetricTile { Layout.fillWidth: true; theme: root.theme; label: "历史报告"; value: String(root.analysisState.history_count || 0); detail: "分析历史区"; tone: "accent" }
                                MetricTile { Layout.fillWidth: true; theme: root.theme; label: "补充字段"; value: String(root.analysisState.field_count || 0); detail: "当前报告"; tone: "neutral" }
                                MetricTile { Layout.fillWidth: true; theme: root.theme; label: "实验条目"; value: String(root.analysisState.experiment_count || 0); detail: "实验结构"; tone: "neutral" }
                                MetricTile { Layout.fillWidth: true; theme: root.theme; label: "比较维度"; value: String(root.analysisState.comparison_count || 0); detail: "报告比对"; tone: "neutral" }
                            }
                        }
                    }
                }

                TaskBanner {
                    width: parent.width
                    theme: root.theme
                    task: root.analysisTask
                    compact: true
                }

                Flow {
                    width: parent.width
                    spacing: 10

                    InteractiveButton {
                        theme: root.theme
                        text: "保存到研究笔记"
                        enabled: !!root.currentAnalysis.report_id
                        onClicked: if (root.controller) root.controller.saveAnalysisToNote(root.currentAnalysis.report_id)
                    }

                    InteractiveButton {
                        theme: root.theme
                        text: "生成写作草稿"
                        tone: "accent"
                        enabled: !!root.currentAnalysis.report_id
                        onClicked: if (root.controller) root.controller.createDraftFromAnalysis(root.currentAnalysis.report_id)
                    }

                    InteractiveButton {
                        theme: root.theme
                        text: "生成 LaTeX 草稿"
                        enabled: !!root.currentAnalysis.report_id
                        onClicked: if (root.controller) root.controller.openAnalysisLatex(root.currentAnalysis.report_id)
                    }
                }
            }
        }

        GridLayout {
            Layout.fillWidth: true
            columns: root.stackedBody ? 1 : 3
            columnSpacing: 18
            rowSpacing: 18

            ColumnLayout {
                Layout.fillWidth: root.stackedBody
                Layout.preferredWidth: root.stackedBody ? 0 : 320
                Layout.maximumWidth: root.stackedBody ? 16777215 : 320
                Layout.alignment: Qt.AlignTop
                spacing: 18

                Rectangle {
                    Layout.fillWidth: true
                    radius: 6
                    color: root.theme.panelRaised
                    border.color: root.theme.border
                    border.width: 1
                    implicitHeight: launchColumn.implicitHeight + 28

                    Column {
                        id: launchColumn
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 10

                        Text { text: "发起分析"; color: root.theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }
                        Text { text: "从资料流中选择文档后直接进入统一分析任务。"; color: root.theme.textSoft; font.pixelSize: 11; width: parent.width; wrapMode: Text.Wrap }

                        ComboBox {
                            id: documentPicker
                            width: parent.width
                            model: root.documentChoices
                            textRole: "display_title"
                        }

                        InteractiveButton {
                            width: parent.width
                            theme: root.theme
                            text: "生成结构化分析"
                            tone: "accent"
                            enabled: documentPicker.currentIndex >= 0 && !root.analysisTask.busy
                            onClicked: if (root.controller) root.controller.analyzeDocument(root.documentChoices.record(documentPicker.currentIndex).document_id)
                        }
                    }
                }

                Rectangle {
                    Layout.fillWidth: true
                    radius: 6
                    color: root.theme.panelRaised
                    border.color: root.theme.border
                    border.width: 1
                    implicitHeight: historyColumn.implicitHeight + 28

                    Column {
                        id: historyColumn
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 10

                        Text { text: "分析历史"; color: root.theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }

                        Repeater {
                            model: root.analysisHistory
                            delegate: Rectangle {
                                visible: index < 6
                                width: parent.width
                                radius: 4
                                color: report_id === root.currentAnalysis.report_id ? root.theme.accentPanel : root.theme.panelInset
                                border.color: report_id === root.currentAnalysis.report_id ? root.theme.accentOutline : root.theme.border
                                border.width: 1
                                implicitHeight: historyItemColumn.implicitHeight + 20

                                Column {
                                    id: historyItemColumn
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 4

                                    Text { text: title; color: report_id === root.currentAnalysis.report_id ? root.theme.anchor : root.theme.text; width: parent.width; elide: Text.ElideRight; font.weight: Font.DemiBold }
                                    Text { text: created_at; color: root.theme.textSoft; width: parent.width; elide: Text.ElideRight; font.pixelSize: 11 }
                                    Text { text: status_line; color: root.theme.textMuted; width: parent.width; elide: Text.ElideRight; font.pixelSize: 11 }
                                    Text { text: summary; color: root.theme.textMuted; width: parent.width; wrapMode: Text.Wrap; maximumLineCount: 2; elide: Text.ElideRight; font.pixelSize: 11 }
                                }

                                SignalAccent {
                                    anchors.fill: parent
                                    active: report_id === root.currentAnalysis.report_id
                                    hovered: historyHover.containsMouse
                                    pressed: historyHover.pressed
                                    accentColor: root.theme.anchor
                                    neutralColor: root.theme.accentSoft
                                    edge: "frame"
                                    radius: 4
                                }

                                MouseArea {
                                    id: historyHover
                                    anchors.fill: parent
                                    hoverEnabled: true
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: if (root.controller) root.controller.focusAnalysis(report_id)
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

            Rectangle {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignTop
                radius: 6
                color: root.theme.panelRaised
                border.color: root.theme.border
                border.width: 1
                implicitHeight: reportColumn.implicitHeight + 32

                Column {
                    id: reportColumn
                    anchors.fill: parent
                    anchors.margins: 16
                    spacing: 14

                    Text {
                        text: "报告结构区"
                        color: root.theme.text
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }

                    Rectangle {
                        width: parent.width
                        radius: 6
                        color: root.theme.panelInset
                        border.color: root.theme.border
                        border.width: 1
                        implicitHeight: summaryText.implicitHeight + 24

                        Text {
                            id: summaryText
                            anchors.fill: parent
                            anchors.margins: 12
                            text: root.currentAnalysis.summary || "暂无分析结果。生成分析后，结构化摘要会作为报告主开场出现在这里。"
                            color: root.theme.text
                            wrapMode: Text.Wrap
                        }
                    }

                    GridLayout {
                        id: reportGrid
                        width: parent.width
                        columns: root.compactSections ? 1 : 2
                        columnSpacing: 14
                        rowSpacing: 14

                        Rectangle {
                            Layout.fillWidth: true
                            radius: 6
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: contributionsColumn.implicitHeight + 24

                            Column {
                                id: contributionsColumn
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 8

                                Text { text: "贡献点提炼"; color: root.theme.anchor; font.pixelSize: 13; font.weight: Font.DemiBold }
                                Repeater {
                                    model: root.currentAnalysis.contributions || []
                                    delegate: Text {
                                        width: parent.width
                                        text: "• " + modelData
                                        color: root.theme.text
                                        wrapMode: Text.Wrap
                                    }
                                }
                                Text {
                                    visible: (root.currentAnalysis.contributions || []).length === 0
                                    text: "当前报告暂无贡献点。"
                                    color: root.theme.textSoft
                                    font.pixelSize: 11
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            radius: 6
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: methodColumn.implicitHeight + 24

                            Column {
                                id: methodColumn
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 8

                                Text { text: "方法流程"; color: root.theme.anchor; font.pixelSize: 13; font.weight: Font.DemiBold }
                                Repeater {
                                    model: root.currentAnalysis.method_steps || []
                                    delegate: Text {
                                        width: parent.width
                                        text: (index + 1) + ". " + modelData
                                        color: root.theme.text
                                        wrapMode: Text.Wrap
                                    }
                                }
                                Text {
                                    visible: (root.currentAnalysis.method_steps || []).length === 0
                                    text: "当前报告暂无方法流程。"
                                    color: root.theme.textSoft
                                    font.pixelSize: 11
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            radius: 6
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: experimentsColumn.implicitHeight + 24

                            Column {
                                id: experimentsColumn
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 8

                                Text { text: "实验信息"; color: root.theme.anchor; font.pixelSize: 13; font.weight: Font.DemiBold }
                                Repeater {
                                    model: root.currentAnalysis.experiments || []
                                    delegate: Rectangle {
                                        width: parent.width
                                        radius: 4
                                        color: root.theme.panelRaised
                                        border.color: root.theme.border
                                        border.width: 1
                                        implicitHeight: expRow.implicitHeight + 18

                                        RowLayout {
                                            id: expRow
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            spacing: 10
                                            Text { Layout.preferredWidth: 150; text: modelData.label || modelData["label"] || ""; color: root.theme.text; elide: Text.ElideRight }
                                            Text { Layout.fillWidth: true; text: modelData.value || modelData["value"] || ""; color: root.theme.textMuted; wrapMode: Text.Wrap }
                                        }
                                    }
                                }
                                Text {
                                    visible: (root.currentAnalysis.experiments || []).length === 0
                                    text: "当前报告暂无实验条目。"
                                    color: root.theme.textSoft
                                    font.pixelSize: 11
                                }
                            }
                        }

                        Rectangle {
                            Layout.fillWidth: true
                            radius: 6
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: comparisonColumn.implicitHeight + 24

                            Column {
                                id: comparisonColumn
                                anchors.fill: parent
                                anchors.margins: 12
                                spacing: 8

                                Text { text: "比较结构"; color: root.theme.anchor; font.pixelSize: 13; font.weight: Font.DemiBold }
                                Repeater {
                                    model: root.currentAnalysis.comparison_items || []
                                    delegate: Rectangle {
                                        width: parent.width
                                        radius: 4
                                        color: root.theme.panelRaised
                                        border.color: root.theme.border
                                        border.width: 1
                                        implicitHeight: comparisonItemColumn.implicitHeight + 18

                                        Column {
                                            id: comparisonItemColumn
                                            anchors.fill: parent
                                            anchors.margins: 10
                                            spacing: 4
                                            Text { text: modelData.label; color: root.theme.text; font.pixelSize: 11; font.weight: Font.DemiBold; elide: Text.ElideRight }
                                            Text { text: modelData.value; color: root.theme.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap; maximumLineCount: 3; elide: Text.ElideRight }
                                        }
                                    }
                                }
                                Text {
                                    visible: (root.currentAnalysis.comparison_items || []).length === 0
                                    text: "当前报告暂无比较结构。"
                                    color: root.theme.textSoft
                                    font.pixelSize: 11
                                }
                            }
                        }
                    }

                    Rectangle {
                        width: parent.width
                        radius: 6
                        color: root.theme.panelInset
                        border.color: root.theme.border
                        border.width: 1
                        implicitHeight: risksColumn.implicitHeight + 24

                        Column {
                            id: risksColumn
                            anchors.fill: parent
                            anchors.margins: 12
                            spacing: 8

                            Text { text: "局限与风险"; color: root.theme.anchor; font.pixelSize: 13; font.weight: Font.DemiBold }
                            Repeater {
                                model: root.currentAnalysis.risks || []
                                delegate: Text {
                                    width: parent.width
                                    text: "• " + modelData
                                    color: root.theme.text
                                    wrapMode: Text.Wrap
                                }
                            }
                            Text {
                                visible: (root.currentAnalysis.risks || []).length === 0
                                text: "当前报告暂无风险说明。"
                                color: root.theme.textSoft
                                font.pixelSize: 11
                            }
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: root.stackedBody
                Layout.preferredWidth: root.stackedBody ? 0 : 320
                Layout.maximumWidth: root.stackedBody ? 16777215 : 320
                Layout.alignment: Qt.AlignTop
                spacing: 18

                Rectangle {
                    Layout.fillWidth: true
                    radius: 6
                    color: root.theme.panelRaised
                    border.color: root.theme.border
                    border.width: 1
                    implicitHeight: fieldColumn.implicitHeight + 28

                    Column {
                        id: fieldColumn
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 10

                        Text { text: "补充字段区"; color: root.theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }

                        Repeater {
                            model: root.currentAnalysis.field_items || []
                            delegate: Rectangle {
                                width: parent.width
                                radius: 4
                                color: root.theme.panelInset
                                border.color: root.theme.border
                                border.width: 1
                                implicitHeight: fieldItemColumn.implicitHeight + 18

                                Column {
                                    id: fieldItemColumn
                                    anchors.fill: parent
                                    anchors.margins: 10
                                    spacing: 4
                                    Text { text: modelData.label; color: root.theme.text; font.pixelSize: 11; font.weight: Font.DemiBold; elide: Text.ElideRight }
                                    Text { text: modelData.value; color: root.theme.textMuted; font.pixelSize: 11; wrapMode: Text.Wrap; maximumLineCount: 3; elide: Text.ElideRight }
                                }
                            }
                        }

                        Text {
                            visible: (root.currentAnalysis.field_items || []).length === 0
                            text: "当前报告暂无补充字段。"
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
                    implicitHeight: outputColumn.implicitHeight + 28

                    Column {
                        id: outputColumn
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 10

                        Text { text: "输出路径"; color: root.theme.text; font.pixelSize: 15; font.weight: Font.DemiBold }

                        Rectangle {
                            width: parent.width
                            radius: 4
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: readingNoteText.implicitHeight + 24

                            Text {
                                id: readingNoteText
                                anchors.fill: parent
                                anchors.margins: 10
                                text: root.currentAnalysis.reading_note || "阅读笔记会在这里汇总，便于继续转研究笔记。"
                                color: root.theme.textMuted
                                wrapMode: Text.Wrap
                            }
                        }

                        Rectangle {
                            width: parent.width
                            radius: 4
                            color: root.theme.panelInset
                            border.color: root.theme.border
                            border.width: 1
                            implicitHeight: 160

                            TextArea {
                                anchors.fill: parent
                                anchors.margins: 8
                                readOnly: true
                                text: root.currentAnalysis.latex_snippet || ""
                                color: root.theme.text
                                wrapMode: Text.Wrap
                            }
                        }
                    }
                }
            }
        }
    }
}
