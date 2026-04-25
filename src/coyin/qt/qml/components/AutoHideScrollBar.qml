import QtQuick
import QtQuick.Controls
import "../support/UiDefaults.js" as UiDefaults

ScrollBar {
    id: root
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property bool transientActive: false
    readonly property bool reveal: visible && (pressed || hovered || active || transientActive)

    visible: size < 1.0
    implicitWidth: root.orientation === Qt.Vertical ? 14 : 60
    implicitHeight: root.orientation === Qt.Vertical ? 60 : 14
    opacity: reveal ? 1.0 : 0.0

    contentItem: Rectangle {
        implicitWidth: root.orientation === Qt.Vertical ? 8 : 52
        implicitHeight: root.orientation === Qt.Vertical ? 52 : 8
        radius: 3
        color: root.theme.anchor
        opacity: root.enabled ? 0.78 : 0.42
    }

    background: Rectangle {
        radius: 3
        color: root.theme.panelInset
        opacity: root.reveal ? 0.34 : 0.0
    }

    Behavior on opacity {
        NumberAnimation {
            duration: 180
        }
    }

    onPositionChanged: {
        if (!visible)
            return
        transientActive = true
        fadeTimer.restart()
    }

    onPressedChanged: {
        if (pressed) {
            transientActive = true
            fadeTimer.stop()
        } else if (visible) {
            fadeTimer.restart()
        }
    }

    onHoveredChanged: {
        if (hovered) {
            transientActive = true
            fadeTimer.stop()
        } else if (!pressed && visible) {
            fadeTimer.restart()
        }
    }

    onActiveChanged: {
        if (active) {
            transientActive = true
            fadeTimer.stop()
        } else if (!pressed && !hovered && visible) {
            fadeTimer.restart()
        }
    }

    Timer {
        id: fadeTimer
        interval: 560
        running: false
        repeat: false
        onTriggered: root.transientActive = false
    }
}
