import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Coyin.Chrome 1.0
import "../support/UiDefaults.js" as UiDefaults
import "../support/MotionCore.js" as MotionCore

Control {
    id: root
    property string text: ""
    property var theme: UiDefaults.safeTheme(UiDefaults.theme())
    property bool checked: false
    property bool busy: false
    property color markColor: "transparent"
    signal clicked

    hoverEnabled: enabled
    focusPolicy: Qt.TabFocus
    implicitHeight: 30
    implicitWidth: Math.max(88, label.implicitWidth + (mark.visible ? 28 : 18) + (busy ? 14 : 0))

    background: Rectangle {
        radius: MotionCore.tokens().radiusSmall
        color: root.checked ? root.theme.accentPanel : root.theme.panelInset
        border.color: root.checked ? root.theme.accentOutline : root.theme.border
        border.width: 1
        opacity: root.enabled ? 1.0 : 0.72

        SignalAccent {
            anchors.fill: parent
            active: root.activeFocus || root.checked || root.busy
            hovered: pressArea.containsMouse
            pressed: pressArea.pressed
            accentColor: root.theme.anchor
            neutralColor: root.theme.accentSoft
            edge: "frame"
            radius: MotionCore.tokens().radiusSmall
        }
    }

    contentItem: RowLayout {
        spacing: 8

        Rectangle {
            id: mark
            visible: root.markColor !== "transparent"
            Layout.preferredWidth: 8
            Layout.preferredHeight: 8
            radius: 2
            color: root.markColor
        }

        Text {
            id: label
            Layout.fillWidth: true
            text: root.busy ? (root.text + "…") : root.text
            color: root.checked ? root.theme.anchor : root.theme.textMuted
            font.family: "Microsoft YaHei UI"
            font.pixelSize: 12
            font.weight: root.checked ? Font.DemiBold : Font.Medium
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }
    }

    MouseArea {
        id: pressArea
        anchors.fill: parent
        enabled: root.enabled && !root.busy
        hoverEnabled: true
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: root.clicked()
    }
}
