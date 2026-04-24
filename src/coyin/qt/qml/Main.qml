pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "support/UiDefaults.js" as UiDefaults
import "support/MotionCore.js" as MotionCore
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
    property real pageReveal: 1.0
    property int activePageIndex: shellState.currentIndex
    property int outgoingPageIndex: -1
    property int pageDirection: 1
    readonly property real pageTravel: Math.max(36, Math.min(width * 0.08, 84))
    readonly property var shellState: shellRef ? shellRef : UiDefaults.shellState()

    color: theme.background

    Component.onCompleted: {
        if (controllerRef && controllerRef.themeTokens)
            theme = UiDefaults.safeTheme(controllerRef.themeTokens)
        if (controllerRef && shellRef)
            controllerRef.syncCurrentPage(shellRef.currentPage)
        root.activePageIndex = root.shellState.currentIndex
        root.outgoingPageIndex = -1
        root.pageReveal = 1.0
    }

    Connections {
        target: shellRef ? shellRef : null
        function onCurrentPageChanged() {
            var nextIndex = root.shellState.currentIndex
            root.pageDirection = nextIndex >= root.activePageIndex ? 1 : -1
            root.outgoingPageIndex = root.activePageIndex
            root.activePageIndex = nextIndex
            root.pagePulse = true
            root.pageReveal = 0.0
            pageRevealAnimation.restart()
            pageTransitionCleanup.restart()
            pulseReset.restart()
            if (root.controllerRef)
                root.controllerRef.syncCurrentPage(root.shellState.currentPage)
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

    Timer {
        id: pageTransitionCleanup
        interval: MotionCore.duration("page", root.theme) + 40
        onTriggered: root.outgoingPageIndex = -1
    }

    NumberAnimation {
        id: pageRevealAnimation
        target: root
        property: "pageReveal"
        from: 0.0
        to: 1.0
        duration: MotionCore.duration("page", root.theme)
        easing.type: Easing.OutCubic
    }

    Popup {
        id: appMenu
        objectName: "appMenu"
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
                objectName: "settingsMenuButton"
                width: parent.width
                theme: root.theme
                text: "设置"
                onClicked: {
                    if (root.shellRef) root.shellRef.setCurrentPage("settings")
                    appMenu.close()
                }
            }

            InteractiveButton {
                objectName: "themeMenuButton"
                width: parent.width
                theme: root.theme
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
                        text: "阅读、搜索、分析和写作"
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
                    frameColor: theme.panelRaised
                    borderColor: theme.border
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
            z: 8
            color: theme.chrome
            border.color: theme.border

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 14
                anchors.rightMargin: 14
                spacing: 8
                z: 1

                InteractiveButton {
                    text: "工作台"
                    selected: root.shellState.currentPage === "home"
                    tone: selected ? "accent" : "neutral"
                    theme: root.theme
                    z: 1
                    onClicked: if (root.shellRef) root.shellRef.setCurrentPage("home")
                }

                InteractiveButton {
                    text: "资料库"
                    selected: root.shellState.currentPage === "library"
                    tone: selected ? "accent" : "neutral"
                    theme: root.theme
                    z: 1
                    onClicked: if (root.shellRef) root.shellRef.setCurrentPage("library")
                }

                InteractiveButton {
                    text: "搜索"
                    selected: root.shellState.currentPage === "search"
                    tone: selected ? "accent" : "neutral"
                    theme: root.theme
                    z: 1
                    onClicked: if (root.shellRef) root.shellRef.setCurrentPage("search")
                }

                InteractiveButton {
                    text: "分析"
                    selected: root.shellState.currentPage === "analysis"
                    tone: selected ? "accent" : "neutral"
                    theme: root.theme
                    z: 1
                    onClicked: if (root.shellRef) root.shellRef.setCurrentPage("analysis")
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
                opacity: 0.32 + 0.10 * root.pageReveal

                Behavior on opacity {
                    NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 22
                color: theme.anchor
                opacity: 0.015 + (root.pagePulse ? 0.06 : 0.0) + (1.0 - root.pageReveal) * 0.045

                Behavior on opacity {
                    NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 1
                color: theme.accentOutline
                opacity: 0.26 + (1.0 - root.pageReveal) * 0.18

                Behavior on opacity {
                    NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                }
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

            Item {
                anchors.fill: parent
                anchors.margins: 18
                opacity: 0.80 + (0.20 * root.pageReveal)
                y: (1.0 - root.pageReveal) * (root.theme.pageOffset + 2)
                clip: true

                Behavior on opacity {
                    NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                }

                Behavior on y {
                    NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                }

                Item {
                    anchors.fill: parent

                    Item {
                        anchors.fill: parent
                        visible: opacity > 0.01 || root.activePageIndex === 0 || root.outgoingPageIndex === 0
                        opacity: root.activePageIndex === 0 ? 1.0 : 0.0
                        x: root.activePageIndex === 0 ? 0 : (root.outgoingPageIndex === 0 ? -root.pageDirection * root.pageTravel : root.pageDirection * root.pageTravel)
                        scale: root.activePageIndex === 0 ? 1.0 : (root.outgoingPageIndex === 0 ? 0.992 : 1.008)
                        z: root.activePageIndex === 0 ? 2 : (root.outgoingPageIndex === 0 ? 1 : 0)

                        Behavior on x {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        Behavior on opacity {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        Behavior on scale {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        HomePage { anchors.fill: parent; controller: root.controllerRef; shellState: root.shellRef; theme: root.theme }
                    }

                    Item {
                        anchors.fill: parent
                        visible: opacity > 0.01 || root.activePageIndex === 1 || root.outgoingPageIndex === 1
                        opacity: root.activePageIndex === 1 ? 1.0 : 0.0
                        x: root.activePageIndex === 1 ? 0 : (root.outgoingPageIndex === 1 ? -root.pageDirection * root.pageTravel : root.pageDirection * root.pageTravel)
                        scale: root.activePageIndex === 1 ? 1.0 : (root.outgoingPageIndex === 1 ? 0.992 : 1.008)
                        z: root.activePageIndex === 1 ? 2 : (root.outgoingPageIndex === 1 ? 1 : 0)

                        Behavior on x {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        Behavior on opacity {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        Behavior on scale {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        LibraryPage { anchors.fill: parent; controller: root.controllerRef; theme: root.theme }
                    }

                    Item {
                        anchors.fill: parent
                        visible: opacity > 0.01 || root.activePageIndex === 2 || root.outgoingPageIndex === 2
                        opacity: root.activePageIndex === 2 ? 1.0 : 0.0
                        x: root.activePageIndex === 2 ? 0 : (root.outgoingPageIndex === 2 ? -root.pageDirection * root.pageTravel : root.pageDirection * root.pageTravel)
                        scale: root.activePageIndex === 2 ? 1.0 : (root.outgoingPageIndex === 2 ? 0.992 : 1.008)
                        z: root.activePageIndex === 2 ? 2 : (root.outgoingPageIndex === 2 ? 1 : 0)

                        Behavior on x {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        Behavior on opacity {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        Behavior on scale {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        SearchPage { anchors.fill: parent; controller: root.controllerRef; theme: root.theme }
                    }

                    Item {
                        anchors.fill: parent
                        visible: opacity > 0.01 || root.activePageIndex === 3 || root.outgoingPageIndex === 3
                        opacity: root.activePageIndex === 3 ? 1.0 : 0.0
                        x: root.activePageIndex === 3 ? 0 : (root.outgoingPageIndex === 3 ? -root.pageDirection * root.pageTravel : root.pageDirection * root.pageTravel)
                        scale: root.activePageIndex === 3 ? 1.0 : (root.outgoingPageIndex === 3 ? 0.992 : 1.008)
                        z: root.activePageIndex === 3 ? 2 : (root.outgoingPageIndex === 3 ? 1 : 0)

                        Behavior on x {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        Behavior on opacity {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        Behavior on scale {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        AnalysisPage { anchors.fill: parent; controller: root.controllerRef; theme: root.theme }
                    }

                    Item {
                        anchors.fill: parent
                        visible: opacity > 0.01 || root.activePageIndex === 4 || root.outgoingPageIndex === 4
                        opacity: root.activePageIndex === 4 ? 1.0 : 0.0
                        x: root.activePageIndex === 4 ? 0 : (root.outgoingPageIndex === 4 ? -root.pageDirection * root.pageTravel : root.pageDirection * root.pageTravel)
                        scale: root.activePageIndex === 4 ? 1.0 : (root.outgoingPageIndex === 4 ? 0.992 : 1.008)
                        z: root.activePageIndex === 4 ? 2 : (root.outgoingPageIndex === 4 ? 1 : 0)

                        Behavior on x {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        Behavior on opacity {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        Behavior on scale {
                            NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                        }

                        SettingsPage { anchors.fill: parent; controller: root.controllerRef; theme: root.theme }
                    }
                }
            }
        }
    }
}
