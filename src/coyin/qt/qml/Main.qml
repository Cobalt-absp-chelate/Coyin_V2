pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import Coyin.Banner 1.0
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
    property int interactionResetToken: 0
    property int activePageIndex: shellState.currentIndex
    property int outgoingPageIndex: -1
    property int pageDirection: 1
    readonly property bool bannerParallaxEnabled: controllerRef ? controllerRef.bannerParallaxEnabled : true
    readonly property string bannerPresetId: controllerRef ? controllerRef.bannerPresetId : "preset_academic"
    readonly property string bannerAssetRoot: controllerRef ? controllerRef.bannerAssetRoot : ""
    readonly property string customBannerBackgroundPath: controllerRef ? controllerRef.customBannerBackgroundPath : ""
    readonly property string customBannerMidgroundPath: controllerRef ? controllerRef.customBannerMidgroundPath : ""
    readonly property string customBannerForegroundPath: controllerRef ? controllerRef.customBannerForegroundPath : ""
    readonly property string customBannerOverlayPath: controllerRef ? controllerRef.customBannerOverlayPath : ""
    readonly property real pageTravel: Math.max(64, Math.min(width * 0.13, 142))
    readonly property var shellState: shellRef ? shellRef : UiDefaults.shellState()

    color: theme.background

    function resetInteractions() {
        root.interactionResetToken += 1
    }

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
        target: root.shellRef ? root.shellRef : null
        function onCurrentPageChanged() {
            var nextIndex = root.shellState.currentIndex
            root.pageDirection = nextIndex >= root.activePageIndex ? 1 : -1
            root.outgoingPageIndex = root.activePageIndex
            root.activePageIndex = nextIndex
            root.pagePulse = true
            root.pageReveal = 0.0
            root.resetInteractions()
            pageRevealAnimation.restart()
            pageTransitionCleanup.restart()
            pulseReset.restart()
            if (root.controllerRef)
                root.controllerRef.syncCurrentPage(root.shellState.currentPage)
        }
    }

    Connections {
        target: root.controllerRef ? root.controllerRef : null
        function onThemeChanged() {
            root.theme = UiDefaults.safeTheme(root.controllerRef && root.controllerRef.themeTokens ? root.controllerRef.themeTokens : UiDefaults.theme())
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
        scale: 1.0
        opacity: 1.0
        transformOrigin: Item.TopRight
        closePolicy: Popup.CloseOnPressOutside | Popup.CloseOnEscape
        onOpened: root.resetInteractions()
        onClosed: root.resetInteractions()

        enter: Transition {
            NumberAnimation { property: "opacity"; from: 0.0; to: 1.0; duration: MotionCore.duration("fast", root.theme); easing.type: Easing.OutCubic }
            NumberAnimation { property: "scale"; from: 0.97; to: 1.0; duration: MotionCore.duration("fast", root.theme); easing.type: Easing.OutCubic }
        }

        exit: Transition {
            NumberAnimation { property: "opacity"; from: 1.0; to: 0.0; duration: MotionCore.duration("fast", root.theme); easing.type: Easing.OutCubic }
            NumberAnimation { property: "scale"; from: 1.0; to: 0.985; duration: MotionCore.duration("fast", root.theme); easing.type: Easing.OutCubic }
        }

        background: Rectangle {
            radius: 8
            color: MotionCore.mixColor(root.theme.panelRaised, root.theme.accentSurface, 0.08)
            border.color: MotionCore.mixColor(root.theme.border, root.theme.accentOutline, 0.18)
            border.width: 1

            Rectangle {
                anchors.fill: parent
                anchors.margins: -8
                z: -1
                radius: 14
                color: root.theme.shadow
                opacity: 0.16
            }
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
                    if (root.shellRef)
                        root.shellRef.setCurrentPage("settings")
                    appMenu.close()
                }
            }

            InteractiveButton {
                objectName: "themeMenuButton"
                width: parent.width
                theme: root.theme
                text: root.theme.mode === "light" ? "夜间模式" : "浅色模式"
                onClicked: {
                    if (root.controllerRef)
                        root.controllerRef.toggleTheme()
                    appMenu.close()
                }
            }
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Item {
            id: topChrome
            Layout.fillWidth: true
            Layout.preferredHeight: 142
            clip: true

            ParallaxBanner {
                id: topBanner
                anchors.fill: parent
                assetRoot: root.bannerAssetRoot
                presetId: root.bannerPresetId
                parallaxEnabled: root.bannerParallaxEnabled
                hoverActive: root.bannerParallaxEnabled && topBannerHover.hovered
                pointerRatio: (!root.bannerParallaxEnabled || !topBannerHover.hovered || topChrome.width <= 0)
                    ? 0.0
                    : (((topBannerHover.point.position.x / topChrome.width) - 0.5) * 2.0)
                customBackgroundPath: root.customBannerBackgroundPath
                customMidgroundPath: root.customBannerMidgroundPath
                customForegroundPath: root.customBannerForegroundPath
                customOverlayPath: root.customBannerOverlayPath
            }

            Rectangle {
                anchors.fill: parent
                color: root.theme.mode === "dark" ? Qt.rgba(0.03, 0.07, 0.11, 0.24) : "transparent"
            }

            HoverHandler {
                id: topBannerHover
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            }

            Rectangle {
                anchors.fill: parent
                gradient: Gradient {
                    GradientStop { position: 0.0; color: root.theme.mode === "dark" ? Qt.rgba(0.06, 0.10, 0.14, 0.16) : Qt.rgba(1, 1, 1, 0.08) }
                    GradientStop { position: 0.62; color: root.theme.mode === "dark" ? Qt.rgba(0.04, 0.08, 0.12, 0.05) : Qt.rgba(1, 1, 1, 0.02) }
                    GradientStop { position: 1.0; color: "transparent" }
                }
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.bottom: parent.bottom
                height: 42
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "transparent" }
                    GradientStop { position: 1.0; color: root.theme.workspace }
                }
            }

            ColumnLayout {
                anchors.fill: parent
                spacing: 0

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 76
                    color: root.theme.mode === "dark"
                        ? Qt.rgba(0.05, 0.09, 0.14, 0.42)
                        : Qt.rgba(1, 1, 1, 0.30)
                    border.color: root.theme.mode === "dark"
                        ? Qt.rgba(0.72, 0.84, 0.96, 0.12)
                        : Qt.rgba(1, 1, 1, 0.16)

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 12

                        Rectangle {
                            width: 40
                            height: 28
                            radius: 6
                            color: MotionCore.mixColor(root.theme.panelInset, root.theme.panelRaised, 0.12)
                            border.color: root.theme.border
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
                                color: root.theme.text
                                font.family: "Microsoft YaHei UI"
                                font.pixelSize: 16
                                font.weight: Font.DemiBold
                            }
                        }

                        Rectangle {
                            Layout.preferredWidth: 340
                            Layout.fillWidth: true
                            Layout.maximumWidth: 420
                            Layout.alignment: Qt.AlignVCenter
                            height: 32
                            radius: 6
                            color: MotionCore.mixColor(root.theme.panelInset, root.theme.panelRaised, 0.10)
                            border.color: root.theme.border
                            border.width: 1

                            Text {
                                anchors.fill: parent
                                anchors.margins: 10
                                text: root.controllerRef && root.controllerRef.statusText ? root.controllerRef.statusText : ""
                                color: root.theme.textMuted
                                elide: Text.ElideRight
                                verticalAlignment: Text.AlignVCenter
                                font.pixelSize: 12
                            }
                        }

                        LoadingStrip {
                            visible: root.controllerRef ? (root.controllerRef.searchLoading || root.controllerRef.analysisLoading) : false
                            Layout.preferredWidth: 126
                            Layout.alignment: Qt.AlignVCenter
                            tint: root.theme.anchor
                            base: root.theme.accentSoft
                            frameColor: root.theme.panelRaised
                            borderColor: root.theme.border
                            running: visible
                        }

                        InteractiveButton {
                            text: "导入"
                            theme: root.theme
                            onClicked: if (root.controllerRef) root.controllerRef.importDocuments()
                        }

                        InteractiveButton {
                            text: "新建"
                            theme: root.theme
                            onClicked: if (root.controllerRef) root.controllerRef.createWriterDocument()
                        }

                        InteractiveButton {
                            text: "LaTeX"
                            theme: root.theme
                            onClicked: if (root.controllerRef) root.controllerRef.openLatexWindow()
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
                    Layout.preferredHeight: 48
                    color: root.theme.mode === "dark"
                        ? Qt.rgba(0.04, 0.08, 0.12, 0.30)
                        : Qt.rgba(1, 1, 1, 0.16)
                    border.color: root.theme.mode === "dark"
                        ? Qt.rgba(0.72, 0.84, 0.96, 0.10)
                        : Qt.rgba(1, 1, 1, 0.12)

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 8

                        InteractiveButton {
                            text: "工作台"
                            selected: root.shellState.currentPage === "home"
                            tone: selected ? "accent" : "neutral"
                            theme: root.theme
                            onClicked: if (root.shellRef) root.shellRef.setCurrentPage("home")
                        }

                        InteractiveButton {
                            text: "资料库"
                            selected: root.shellState.currentPage === "library"
                            tone: selected ? "accent" : "neutral"
                            theme: root.theme
                            onClicked: if (root.shellRef) root.shellRef.setCurrentPage("library")
                        }

                        InteractiveButton {
                            text: "搜索"
                            selected: root.shellState.currentPage === "search"
                            tone: selected ? "accent" : "neutral"
                            theme: root.theme
                            onClicked: if (root.shellRef) root.shellRef.setCurrentPage("search")
                        }

                        InteractiveButton {
                            text: "分析"
                            selected: root.shellState.currentPage === "analysis"
                            tone: selected ? "accent" : "neutral"
                            theme: root.theme
                            onClicked: if (root.shellRef) root.shellRef.setCurrentPage("analysis")
                        }

                        Item { Layout.fillWidth: true }
                    }
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: root.theme.workspace

            Rectangle {
                anchors.fill: parent
                color: root.theme.workspaceTint
                opacity: 0.22 + 0.16 * root.pageReveal

                Behavior on opacity {
                    NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                }
            }

            Rectangle {
                id: pageStageShadow
                anchors.fill: pageStage
                anchors.margins: -10
                radius: pageStage.radius + 8
                color: root.theme.shadow
                opacity: 0.10 + (1.0 - root.pageReveal) * 0.04

                Behavior on opacity {
                    NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                }
            }

            Rectangle {
                id: pageStage
                anchors.fill: parent
                anchors.margins: 16
                radius: 14
                color: MotionCore.mixColor(root.theme.panel, root.theme.panelRaised, 0.64)
                border.color: MotionCore.mixColor(root.theme.border, root.theme.accentOutline, 0.12)
                border.width: 1
                y: (1.0 - root.pageReveal) * (root.theme.pageOffset + 6)
                clip: true

                Behavior on y {
                    NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                }

                Rectangle {
                    anchors.fill: parent
                    color: root.theme.workspaceTint
                    opacity: 0.16 + 0.10 * root.pageReveal

                    Behavior on opacity {
                        NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                    }
                }

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 22
                    color: root.theme.anchor
                    opacity: 0.01 + (root.pagePulse ? 0.08 : 0.0) + (1.0 - root.pageReveal) * 0.08

                    Behavior on opacity {
                        NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                    }
                }

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 1
                    color: root.theme.accentOutline
                    opacity: 0.18 + (1.0 - root.pageReveal) * 0.28

                    Behavior on opacity {
                        NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                    }
                }

                SignalAccent {
                    anchors.fill: parent
                    active: root.pagePulse
                    hovered: false
                    pressed: false
                    accentColor: root.theme.anchor
                    neutralColor: root.theme.accentSoft
                    edge: "frame"
                    radius: pageStage.radius
                }

                Item {
                    anchors.fill: parent
                    anchors.margins: 18
                    opacity: 0.70 + (0.30 * root.pageReveal)
                    clip: true

                    Behavior on opacity {
                        NumberAnimation { duration: MotionCore.duration("page", root.theme); easing.type: Easing.OutCubic }
                    }

                    Item {
                        anchors.fill: parent

                        Item {
                            anchors.fill: parent
                            visible: opacity > 0.01 || root.activePageIndex === 0 || root.outgoingPageIndex === 0
                            opacity: root.activePageIndex === 0 ? 1.0 : 0.0
                            x: root.activePageIndex === 0 ? 0 : (root.outgoingPageIndex === 0 ? -root.pageDirection * root.pageTravel : root.pageDirection * root.pageTravel * 0.88)
                            scale: root.activePageIndex === 0 ? 1.0 : (root.outgoingPageIndex === 0 ? 0.989 : 1.010)
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
                            x: root.activePageIndex === 1 ? 0 : (root.outgoingPageIndex === 1 ? -root.pageDirection * root.pageTravel : root.pageDirection * root.pageTravel * 0.88)
                            scale: root.activePageIndex === 1 ? 1.0 : (root.outgoingPageIndex === 1 ? 0.989 : 1.010)
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
                            x: root.activePageIndex === 2 ? 0 : (root.outgoingPageIndex === 2 ? -root.pageDirection * root.pageTravel : root.pageDirection * root.pageTravel * 0.88)
                            scale: root.activePageIndex === 2 ? 1.0 : (root.outgoingPageIndex === 2 ? 0.989 : 1.010)
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
                            x: root.activePageIndex === 3 ? 0 : (root.outgoingPageIndex === 3 ? -root.pageDirection * root.pageTravel : root.pageDirection * root.pageTravel * 0.88)
                            scale: root.activePageIndex === 3 ? 1.0 : (root.outgoingPageIndex === 3 ? 0.989 : 1.010)
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
                            x: root.activePageIndex === 4 ? 0 : (root.outgoingPageIndex === 4 ? -root.pageDirection * root.pageTravel : root.pageDirection * root.pageTravel * 0.88)
                            scale: root.activePageIndex === 4 ? 1.0 : (root.outgoingPageIndex === 4 ? 0.989 : 1.010)
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
}
