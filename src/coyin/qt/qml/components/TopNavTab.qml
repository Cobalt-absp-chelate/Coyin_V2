import QtQuick
import QtQuick.Controls
import Coyin.Chrome 1.0
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Control {
    id: root
    property string text: ""
    property bool active: false
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    signal clicked

    hoverEnabled: true
    focusPolicy: Qt.TabFocus
    implicitWidth: label.implicitWidth + 30
    implicitHeight: 32

    background: Rectangle {
        radius: MotionCore.tokens().radiusSmall
        color: root.active ? theme.accentPanel : "transparent"
        border.color: root.active || root.activeFocus ? theme.accentOutline : "transparent"
        border.width: root.active || root.activeFocus ? 1 : 0
        opacity: root.enabled ? 1.0 : 0.66

        SignalAccent {
            anchors.fill: parent
            active: root.active || root.activeFocus
            hovered: pressArea.containsMouse
            pressed: pressArea.pressed
            accentColor: theme.anchor
            neutralColor: theme.accentSoft
            edge: "bottom"
            radius: MotionCore.tokens().radiusSmall
        }
    }

    contentItem: Text {
        id: label
        text: root.text
        color: !root.enabled ? theme.textSoft : (root.active ? theme.anchor : theme.textMuted)
        font.family: "Microsoft YaHei UI"
        font.pixelSize: 13
        font.weight: root.active ? Font.DemiBold : Font.Medium
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    MouseArea {
        id: pressArea
        anchors.fill: parent
        hoverEnabled: true
        enabled: root.enabled
        cursorShape: root.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: root.clicked()
    }
}
