import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "support/UiDefaults.js" as UiDefaults
import "components"
import "pages"

ApplicationWindow {
    id: root
    width: 1480
    height: 940
    visible: true
    title: "Coyin"

    property var controllerRef: mainController
    property var shellRef: shellController
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property bool pagePulse: false
    readonly property var shellState: shellRef ? shellRef : UiDefaults.shellState()

    color: theme.background

    Component.onCompleted: {
        if (controllerRef && controllerRef.themeTokens)
            theme = UiDefaults.safeTheme(controllerRef.themeTokens)
    }

    Connections {
        target: shellRef ? shellRef : null
        function onCurrentPageChanged() {
            root.pagePulse = true
            pulseReset.restart()
        }
    }

    Connections {
        target: controllerRef ? controllerRef : null
        function onThemeChanged() {
            root.theme = UiDefaults.safeTheme(controllerRef && controllerRef.themeTokens ? controllerRef.themeTokens : UiDefaults.theme())
        }
    }

    Timer {
        id: pulseReset
        interval: 180
        onTriggered: root.pagePulse = false
    }

    Popup {
        id: appMenu
        x: root.width - width - 18
        y: 48
        width: 144
        padding: 8
        modal: false
        focus: true
        closePolicy: Popup.CloseOnPressOutside | Popup.CloseOnEscape
        background: Rectangle {
            radius: 6
            color: root.theme.panelRaised
            border.color: root.theme.border
            border.width: 1
        }

        Column {
            width: parent.width
            spacing: 6

            InteractiveButton {
                width: parent.width
                text: "设置"
                onClicked: {
                    if (root.shellRef) root.shellRef.setCurrentPage("settings")
                    appMenu.close()
                }
            }

            InteractiveButton {
                width: parent.width
                text: root.theme.mode === "light" ? "夜间模式" : "浅色模式"
                onClicked: {
                    if (root.controllerRef) root.controllerRef.toggleTheme()
                    appMenu.close()
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 54
            color: theme.chrome
            border.color: theme.border

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 12

                Rectangle {
                    width: 40
                    height: 28
                    radius: 6
                    color: theme.panelInset
                    border.color: theme.border
                    border.width: 1

                    Image {
                        anchors.fill: parent
                        anchors.margins: 4
                        fillMode: Image.PreserveAspectFit
                        source: Qt.resolvedUrl("../../../../assets/icons/coyin_mark.svg")
                    }
                }

                Column {
                    Layout.alignment: Qt.AlignVCenter
                    spacing: 2

                    Text {
                        text: root.shellState.currentTitle
                        color: theme.text
                        font.family: "Microsoft YaHei UI"
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }

                    Text {
                        text: "研究资料、搜索与分析的统一工作台"
                        color: theme.textSoft
                        font.pixelSize: 11
                    }
                }

                Rectangle {
                    Layout.preferredWidth: 340
                    Layout.fillWidth: true
                    Layout.maximumWidth: 420
                    Layout.alignment: Qt.AlignVCenter
                    height: 32
                    radius: 6
                    color: theme.panelInset
                    border.color: theme.border
                    border.width: 1

                    Text {
                        anchors.fill: parent
                        anchors.margins: 10
                        text: controllerRef ? controllerRef.statusText : "准备就绪"
                        color: theme.textMuted
                        elide: Text.ElideRight
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 12
                    }
                }

                LoadingStrip {
                    visible: controllerRef ? (controllerRef.searchLoading || controllerRef.analysisLoading) : false
                    Layout.preferredWidth: 126
                    Layout.alignment: Qt.AlignVCenter
                    tint: theme.anchor
                    base: theme.accentSoft
                    running: visible
                }

                InteractiveButton {
                    text: "导入"
                    theme: root.theme
                    onClicked: if (controllerRef) controllerRef.importDocuments()
                }

                InteractiveButton {
                    text: "新建"
                    theme: root.theme
                    onClicked: if (controllerRef) controllerRef.createWriterDocument()
                }

                InteractiveButton {
                    text: "LaTeX"
                    theme: root.theme
                    onClicked: if (controllerRef) controllerRef.openLatexWindow()
                }

                InteractiveButton {
                    text: "⋯"
                    theme: root.theme
                    width: 34
                    onClicked: appMenu.open()
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 40
            color: theme.chrome
            border.color: theme.border

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 8

                Repeater {
                    model: root.shellState.primaryPageEntries
                    delegate: TopNavTab {
                        text: modelData.title
                        active: root.shellState.currentPage === modelData.page_id
                        theme: root.theme
                        onClicked: if (root.shellRef) root.shellRef.setCurrentPage(modelData.page_id)
                    }
                }

                Item { Layout.fillWidth: true }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: theme.workspace

            Rectangle {
                anchors.fill: parent
                color: theme.workspaceTint
                opacity: 0.42
            }

            SignalAccent {
                anchors.fill: parent
                active: root.pagePulse
                hovered: false
                pressed: false
                accentColor: theme.anchor
                neutralColor: theme.accentSoft
                edge: "frame"
                radius: 0
            }

            StackLayout {
                anchors.fill: parent
                anchors.margins: 18
                currentIndex: root.shellState.currentIndex

                HomePage { controller: root.controllerRef; shellState: root.shellRef; theme: root.theme }
                LibraryPage { controller: root.controllerRef; theme: root.theme }
                SearchPage { controller: root.controllerRef; theme: root.theme }
                AnalysisPage { controller: root.controllerRef; theme: root.theme }
                SettingsPage { controller: root.controllerRef; theme: root.theme }
            }
        }
    }
}
