import QtQuick
import QtQuick.Controls
import Coyin.Chrome 1.0
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

TextField {
    id: root
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property bool busy: false
    property bool selected: false

    padding: 10
    color: theme.text
    font.family: "Microsoft YaHei UI"
    font.pixelSize: 12
    selectByMouse: true

    background: Rectangle {
        radius: MotionCore.tokens().radiusSmall
        color: root.enabled ? root.theme.panelInset : root.theme.panel
        border.color: root.activeFocus || root.selected ? root.theme.accentOutline : root.theme.border
        border.width: 1
        opacity: root.enabled ? 1.0 : 0.74

        SignalAccent {
            anchors.fill: parent
            active: root.activeFocus || root.selected || root.busy
            hovered: hover.containsMouse
            pressed: false
            accentColor: root.theme.anchor
            neutralColor: root.theme.accentSoft
            edge: "bottom"
            radius: MotionCore.tokens().radiusSmall
        }

        MouseArea {
            id: hover
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            hoverEnabled: true
        }
    }
}
